from typing import TypeVar

from pydantic import BaseModel
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.ai.providers.base import AIProvider
from app.ai.providers.factory import build_provider
from app.core.config import Settings
from app.core.exceptions import ExternalServiceError
from app.utils.redaction import redact_pii

logger = structlog.get_logger(__name__)
T = TypeVar("T", bound=BaseModel)


class AIGateway:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.provider: AIProvider = build_provider(settings)

    @retry(wait=wait_exponential(multiplier=0.5, min=0.5, max=3), stop=stop_after_attempt(3), reraise=True)
    async def run_structured(
        self,
        *,
        workflow: str,
        messages: list[dict[str, str]],
        response_model: type[T],
        model_name: str | None = None,
    ) -> T:
        chosen_model = model_name or self.settings.ai_default_model
        safe_messages = [{"role": m["role"], "content": redact_pii(m["content"])} for m in messages]
        logger.info(
            "ai_request_started",
            workflow=workflow,
            provider=self.settings.ai_provider,
            model=chosen_model,
            message_count=len(messages),
            redacted_preview=safe_messages[-1]["content"][:250] if safe_messages else "",
        )

        try:
            output = await self.provider.generate_structured(
                messages=messages,
                response_model=response_model,
                model_name=chosen_model,
                timeout_seconds=self.settings.ai_timeout_seconds,
            )
            logger.info("ai_request_succeeded", workflow=workflow, model=chosen_model)
            return output
        except Exception as exc:
            logger.warning("ai_request_failed", workflow=workflow, error=str(exc), model=chosen_model)
            raise ExternalServiceError("AI workflow failed", details={"workflow": workflow}) from exc

