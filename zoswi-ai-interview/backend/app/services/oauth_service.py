from typing import Literal
from urllib.parse import urlencode

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.core.security import create_oauth_bridge_token, create_oauth_state_token, decode_token
from app.services.identity_service import IdentityService

OAuthProvider = Literal["google", "linkedin"]


class OAuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()
        self.identity = IdentityService(session)

    def build_authorization_url(self, provider: OAuthProvider) -> str:
        state = create_oauth_state_token(provider=provider)
        if provider == "google":
            if not self.settings.google_oauth_client_id:
                raise AuthenticationError("Google OAuth is not configured")
            params = {
                "client_id": self.settings.google_oauth_client_id,
                "redirect_uri": self.settings.google_oauth_redirect_uri,
                "response_type": "code",
                "scope": "openid email profile",
                "state": state,
                "prompt": "select_account",
            }
            return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

        if provider == "linkedin":
            if not self.settings.linkedin_oauth_client_id:
                raise AuthenticationError("LinkedIn OAuth is not configured")
            params = {
                "response_type": "code",
                "client_id": self.settings.linkedin_oauth_client_id,
                "redirect_uri": self.settings.linkedin_oauth_redirect_uri,
                "scope": "openid profile email",
                "state": state,
            }
            return f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"

        raise AuthenticationError("Unsupported OAuth provider")

    async def handle_callback(
        self,
        *,
        provider: OAuthProvider,
        code: str,
        state: str,
    ) -> str:
        claims = decode_token(state)
        if claims.type != "oauth_state" or claims.sub != provider:
            raise AuthenticationError("Invalid OAuth state")

        profile = await self._fetch_profile(provider=provider, code=code)
        user = await self.identity.oauth_login_or_signup(
            provider=provider,
            provider_user_id=profile["provider_user_id"],
            email=profile.get("email"),
            full_name=profile.get("full_name"),
        )
        return create_oauth_bridge_token(subject=str(user.id))

    async def exchange_bridge_token(self, bridge_token: str):
        claims = decode_token(bridge_token)
        if claims.type != "oauth_bridge":
            raise AuthenticationError("Invalid OAuth bridge token")
        user = await self.identity.users.get_by_id(user_id=self._uuid(claims.sub))
        if user is None:
            raise AuthenticationError("User not found for OAuth token")
        return await self.identity.issue_auth_payload_for_user(user)

    @staticmethod
    def _uuid(value: str):
        from uuid import UUID

        return UUID(value)

    async def _fetch_profile(self, *, provider: OAuthProvider, code: str) -> dict[str, str | None]:
        if provider == "google":
            return await self._google_profile(code)
        return await self._linkedin_profile(code)

    async def _google_profile(self, code: str) -> dict[str, str | None]:
        if not self.settings.google_oauth_client_id or not self.settings.google_oauth_client_secret:
            raise AuthenticationError("Google OAuth credentials are not configured")
        async with httpx.AsyncClient(timeout=20.0) as client:
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": self.settings.google_oauth_client_id,
                    "client_secret": self.settings.google_oauth_client_secret,
                    "redirect_uri": self.settings.google_oauth_redirect_uri,
                    "grant_type": "authorization_code",
                },
                headers={"Accept": "application/json"},
            )
            if token_resp.status_code >= 400:
                raise AuthenticationError("Google token exchange failed")
            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            if not access_token:
                raise AuthenticationError("Google token response missing access token")

            user_resp = await client.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if user_resp.status_code >= 400:
                raise AuthenticationError("Google user profile fetch failed")
            profile = user_resp.json()
            provider_user_id = profile.get("sub")
            if not provider_user_id:
                raise AuthenticationError("Google profile missing subject")
            return {
                "provider_user_id": str(provider_user_id),
                "email": profile.get("email"),
                "full_name": profile.get("name"),
            }

    async def _linkedin_profile(self, code: str) -> dict[str, str | None]:
        if not self.settings.linkedin_oauth_client_id or not self.settings.linkedin_oauth_client_secret:
            raise AuthenticationError("LinkedIn OAuth credentials are not configured")
        async with httpx.AsyncClient(timeout=20.0) as client:
            token_resp = await client.post(
                "https://www.linkedin.com/oauth/v2/accessToken",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.settings.linkedin_oauth_redirect_uri,
                    "client_id": self.settings.linkedin_oauth_client_id,
                    "client_secret": self.settings.linkedin_oauth_client_secret,
                },
                headers={"Accept": "application/json"},
            )
            if token_resp.status_code >= 400:
                raise AuthenticationError("LinkedIn token exchange failed")
            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            if not access_token:
                raise AuthenticationError("LinkedIn token response missing access token")

            user_resp = await client.get(
                "https://api.linkedin.com/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if user_resp.status_code >= 400:
                raise AuthenticationError("LinkedIn user profile fetch failed")
            profile = user_resp.json()
            provider_user_id = profile.get("sub")
            if not provider_user_id:
                raise AuthenticationError("LinkedIn profile missing subject")

            full_name = profile.get("name")
            if not full_name:
                given = profile.get("given_name")
                family = profile.get("family_name")
                full_name = " ".join(part for part in [given, family] if part).strip() or None

            return {
                "provider_user_id": str(provider_user_id),
                "email": profile.get("email"),
                "full_name": full_name,
            }

