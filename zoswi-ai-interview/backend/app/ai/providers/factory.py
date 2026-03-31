from app.ai.providers.anthropic_provider import AnthropicProvider
from app.ai.providers.base import AIProvider
from app.ai.providers.mock_provider import MockProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.core.config import Settings
from app.core.exceptions import ExternalServiceError


def build_provider(settings: Settings) -> AIProvider:
    if settings.ai_provider == "openai":
        if settings.openai_api_key:
            return OpenAIProvider(api_key=settings.openai_api_key)
        if settings.ai_allow_mock_provider:
            return MockProvider()
        raise ExternalServiceError("OpenAI provider selected but OPENAI_API_KEY is not configured")

    if settings.ai_provider == "anthropic":
        if settings.anthropic_api_key:
            return AnthropicProvider(api_key=settings.anthropic_api_key)
        if settings.ai_allow_mock_provider:
            return MockProvider()
        raise ExternalServiceError("Anthropic provider selected but ANTHROPIC_API_KEY is not configured")

    return MockProvider()

