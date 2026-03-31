from typing import TypeVar

from anthropic import AsyncAnthropic
from pydantic import BaseModel

from app.ai.providers.base import AIProvider
from app.ai.providers.json_utils import parse_json_payload

T = TypeVar("T", bound=BaseModel)


class AnthropicProvider(AIProvider):
    def __init__(self, api_key: str) -> None:
        self.client = AsyncAnthropic(api_key=api_key)

    async def generate_structured(
        self,
        *,
        messages: list[dict[str, str]],
        response_model: type[T],
        model_name: str,
        timeout_seconds: float,
    ) -> T:
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_parts = [m["content"] for m in messages if m["role"] != "system"]

        response = await self.client.messages.create(
            model=model_name,
            system=system,
            max_tokens=1200,
            temperature=0.3,
            messages=[{"role": "user", "content": "\n\n".join(user_parts)}],
            timeout=timeout_seconds,
        )
        content = "".join(
            block.text for block in response.content if hasattr(block, "text") and block.text
        )
        parsed = parse_json_payload(content)
        return response_model.model_validate(parsed)

