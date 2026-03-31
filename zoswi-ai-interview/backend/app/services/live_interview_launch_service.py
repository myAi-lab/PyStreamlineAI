from datetime import timedelta
from urllib.parse import urlencode, urlsplit

from jose import jwt

from app.core.config import get_settings
from app.core.exceptions import ValidationError
from app.models.user import User
from app.schemas.interview import LiveInterviewLaunchRequest, LiveInterviewLaunchResponse
from app.utils.time import utcnow


class LiveInterviewLaunchService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def build_launch_url(self, *, user: User, payload: LiveInterviewLaunchRequest) -> LiveInterviewLaunchResponse:
        base_url = self._validated_base_url()
        launch_secret = str(self.settings.interview_launch_secret or self.settings.jwt_secret_key or "").strip()
        if not launch_secret:
            raise ValidationError("Interview launch secret is not configured")

        issued_at = utcnow()
        expires_at = issued_at + timedelta(seconds=max(60, int(self.settings.interview_launch_ttl_seconds or 900)))
        launch_token = jwt.encode(
            {
                "sub": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "candidate_name": payload.candidate_name.strip(),
                "target_role": payload.target_role.strip(),
                "requirement_type": payload.requirement_type.value,
                "iss": self.settings.interview_launch_issuer,
                "aud": self.settings.interview_launch_audience,
                "iat": int(issued_at.timestamp()),
                "exp": int(expires_at.timestamp()),
                "typ": "live_interview_launch",
                "source": "zoswi-web",
            },
            launch_secret,
            algorithm=self.settings.jwt_algorithm,
        )
        query = urlencode(
            {
                "candidate": payload.candidate_name.strip(),
                "role": payload.target_role.strip(),
                "type": payload.requirement_type.value,
                "source": "zoswi-web",
                "launch_token": launch_token,
            }
        )
        joiner = "&" if "?" in base_url else "?"
        return LiveInterviewLaunchResponse(
            launch_url=f"{base_url}{joiner}{query}",
            expires_at=expires_at,
        )

    def _validated_base_url(self) -> str:
        raw = str(self.settings.live_interview_app_url or "").strip()
        parsed = urlsplit(raw)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValidationError("Live interview app URL is invalid")
        path = str(parsed.path or "/")
        normalized = f"{parsed.scheme}://{parsed.netloc}{path}"
        if parsed.query:
            normalized = f"{normalized}?{parsed.query}"
        return normalized
