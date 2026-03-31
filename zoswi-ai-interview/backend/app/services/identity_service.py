from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError, ConflictError, ValidationError
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.models.candidate_profile import CandidateProfile
from app.models.enums import UserRole
from app.models.oauth_identity import OAuthIdentity
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.oauth_identity_repository import OAuthIdentityRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthPayload, LoginRequest, SignupRequest, TokenPair, UserPublic
from app.utils.time import utcnow

PUBLIC_EMAIL_DOMAINS = {
    "gmail.com",
    "googlemail.com",
    "yahoo.com",
    "yahoo.co.in",
    "outlook.com",
    "hotmail.com",
    "live.com",
    "msn.com",
    "icloud.com",
    "aol.com",
    "protonmail.com",
    "pm.me",
    "mail.com",
    "gmx.com",
    "zoho.com",
    "yandex.com",
}


class IdentityService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()
        self.users = UserRepository(session)
        self.refresh_tokens = RefreshTokenRepository(session)
        self.oauth_identities = OAuthIdentityRepository(session)

    async def signup(self, payload: SignupRequest) -> AuthPayload:
        primary_email = payload.email.lower()
        role_contact_email = payload.role_contact_email.lower() if payload.role_contact_email else None

        await self._ensure_unique_user_emails(primary_email=primary_email, role_contact_email=role_contact_email)
        years_experience, target_roles, role_profile = self._validate_role_signup_inputs(payload, role_contact_email)
        user = User(
            email=primary_email,
            role_contact_email=role_contact_email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name.strip(),
            role=payload.role,
        )
        await self.users.create(user)
        self.session.add(
            CandidateProfile(
                user_id=user.id,
                years_experience=years_experience,
                target_roles=target_roles,
                role_profile=role_profile,
            )
        )
        tokens = await self._issue_tokens(user)
        await self.session.commit()
        await self.session.refresh(user)
        return AuthPayload(user=UserPublic.model_validate(user), tokens=tokens)

    async def login(self, payload: LoginRequest) -> AuthPayload:
        user = await self.users.get_by_email(payload.email.lower())
        if not user or not verify_password(payload.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("User account is disabled")

        tokens = await self._issue_tokens(user)
        await self.session.commit()
        return AuthPayload(user=UserPublic.model_validate(user), tokens=tokens)

    async def refresh(self, refresh_token: str) -> TokenPair:
        claims = decode_token(refresh_token)
        if claims.type != "refresh" or not claims.jti:
            raise AuthenticationError("Invalid refresh token")

        stored = await self.refresh_tokens.get_by_jti(claims.jti)
        if stored is None or stored.is_revoked or stored.expires_at < utcnow():
            raise AuthenticationError("Refresh token is expired or revoked")

        user = await self.users.get_by_id(stored.user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("User not active")

        await self.refresh_tokens.revoke(stored)
        tokens = await self._issue_tokens(user)
        await self.session.commit()
        return tokens

    async def oauth_login_or_signup(
        self,
        *,
        provider: str,
        provider_user_id: str,
        email: str | None,
        full_name: str | None,
    ) -> User:
        linked = await self.oauth_identities.get_by_provider_identity(
            provider=provider,
            provider_user_id=provider_user_id,
        )
        if linked is not None:
            user = await self.users.get_by_id(linked.user_id)
            if user is None:
                raise AuthenticationError("OAuth identity is not linked to an active user")
            return user

        if email:
            existing = await self.users.get_by_email(email.lower())
            if existing is not None:
                user = existing
            else:
                user = User(
                    email=email.lower(),
                    hashed_password=hash_password(str(uuid4())),
                    full_name=(full_name or "OAuth User").strip()[:200] or "OAuth User",
                    role=UserRole.CANDIDATE,
                )
                await self.users.create(user)
                self.session.add(CandidateProfile(user_id=user.id, target_roles=[], role_profile={}))
        else:
            synthetic_email = f"{provider}_{provider_user_id}@oauth.zoswi.local"
            user = User(
                email=synthetic_email,
                hashed_password=hash_password(str(uuid4())),
                full_name=(full_name or "OAuth User").strip()[:200] or "OAuth User",
                role=UserRole.CANDIDATE,
            )
            await self.users.create(user)
            self.session.add(CandidateProfile(user_id=user.id, target_roles=[], role_profile={}))

        await self.oauth_identities.create(
            OAuthIdentity(
                user_id=user.id,
                provider=provider,
                provider_user_id=provider_user_id,
                email=email.lower() if email else None,
            )
        )
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def issue_auth_payload_for_user(self, user: User) -> AuthPayload:
        tokens = await self._issue_tokens(user)
        await self.session.commit()
        return AuthPayload(user=UserPublic.model_validate(user), tokens=tokens)

    async def _issue_tokens(self, user: User) -> TokenPair:
        access_token = create_access_token(subject=str(user.id), role=user.role.value)
        refresh_token, token_jti = create_refresh_token(subject=str(user.id))

        refresh_record = RefreshToken(
            user_id=user.id,
            token_jti=token_jti,
            expires_at=utcnow() + timedelta(days=self.settings.refresh_token_exp_days),
        )
        await self.refresh_tokens.create(refresh_record)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            access_token_expires_minutes=self.settings.access_token_exp_minutes,
        )

    async def _ensure_unique_user_emails(
        self,
        *,
        primary_email: str,
        role_contact_email: str | None,
    ) -> None:
        checks: list[tuple[str, str]] = [
            ("primary_email", primary_email),
            ("role_contact_email", role_contact_email or ""),
        ]
        for source, candidate_email in checks:
            if not candidate_email:
                continue
            existing_primary = await self.users.get_by_email(candidate_email)
            if existing_primary:
                raise ConflictError(
                    "Email is already registered"
                    if source == "primary_email"
                    else "Role contact email is already registered"
                )
            existing_role_contact = await self.users.get_by_role_contact_email(candidate_email)
            if existing_role_contact:
                raise ConflictError("Email is already registered")

    def _validate_role_signup_inputs(
        self,
        payload: SignupRequest,
        role_contact_email: str | None,
    ) -> tuple[float | None, list[str], dict[str, str]]:
        profile_data = payload.profile_data or {}
        role = payload.role

        if role == UserRole.ADMIN:
            raise ValidationError("Self-signup for admin role is not allowed")

        if role == UserRole.CANDIDATE:
            if payload.years_experience is None:
                raise ValidationError("Years of experience is required for candidate accounts")
            target_role = self._clean_text(profile_data.get("target_role"), max_len=120)
            target_roles = [target_role] if target_role else []
            role_profile: dict[str, str] = {"target_role": target_role} if target_role else {}
            return float(payload.years_experience), target_roles, role_profile

        if role == UserRole.STUDENT:
            if not role_contact_email:
                raise ValidationError("University email is required for student accounts")
            if not self._is_university_domain(self._extract_domain(role_contact_email)):
                raise ValidationError("Student accounts require a university email domain (for example, .edu)")

            university_name = self._clean_text(profile_data.get("university_name"), max_len=120)
            graduation_year_raw = self._clean_text(profile_data.get("graduation_year"), max_len=4)
            degree_program = self._clean_text(profile_data.get("degree_program"), max_len=120)

            if not university_name:
                raise ValidationError("University name is required for student accounts")
            if not graduation_year_raw.isdigit() or len(graduation_year_raw) != 4:
                raise ValidationError("Graduation year must be a 4-digit year")

            graduation_year = int(graduation_year_raw)
            current_year = datetime.now(timezone.utc).year
            if graduation_year < current_year - 10 or graduation_year > current_year + 10:
                raise ValidationError("Graduation year is out of allowed range")

            role_profile = {
                "university_name": university_name,
                "graduation_year": str(graduation_year),
            }
            if degree_program:
                role_profile["degree_program"] = degree_program
            return None, [], role_profile

        if role == UserRole.RECRUITER:
            if not role_contact_email:
                raise ValidationError("Recruiter email is required for recruiter accounts")
            primary_domain = self._extract_domain(payload.email)
            if self._is_public_domain(primary_domain) or self._is_university_domain(primary_domain):
                raise ValidationError(
                    "Recruiter signup requires an organization primary email. Use Candidate or Student for personal/university domains."
                )
            role_domain = self._extract_domain(role_contact_email)
            if self._is_public_domain(role_domain):
                raise ValidationError("Recruiter accounts require an organization email (not personal domains)")
            if self._is_university_domain(role_domain):
                raise ValidationError("Recruiter accounts require an organization email (university domains are not allowed)")

            organization_name = self._clean_text(profile_data.get("organization_name"), max_len=120)
            recruiter_title = self._clean_text(profile_data.get("recruiter_title"), max_len=120)
            hiring_focus = self._clean_text(profile_data.get("hiring_focus"), max_len=160)
            if not organization_name:
                raise ValidationError("Organization name is required for recruiter accounts")

            role_profile = {"organization_name": organization_name}
            if recruiter_title:
                role_profile["recruiter_title"] = recruiter_title
            if hiring_focus:
                role_profile["hiring_focus"] = hiring_focus
            return None, [], role_profile

        raise ValidationError("Unsupported role for signup")

    @staticmethod
    def _clean_text(value: object, *, max_len: int) -> str:
        return str(value or "").strip()[:max_len]

    @staticmethod
    def _extract_domain(email: str) -> str:
        clean = str(email or "").strip().lower()
        if "@" not in clean:
            return ""
        return clean.split("@", 1)[1].strip()

    @staticmethod
    def _is_university_domain(domain: str) -> bool:
        clean = str(domain or "").strip().lower()
        if not clean:
            return False
        return clean.endswith(".edu") or ".edu." in clean or ".ac." in clean

    @staticmethod
    def _is_public_domain(domain: str) -> bool:
        return str(domain or "").strip().lower() in PUBLIC_EMAIL_DOMAINS
