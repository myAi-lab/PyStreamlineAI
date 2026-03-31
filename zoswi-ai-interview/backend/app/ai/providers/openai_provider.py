from typing import TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.ai.providers.base import AIProvider
from app.ai.providers.json_utils import parse_json_payload

T = TypeVar("T", bound=BaseModel)


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str) -> None:
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate_structured(
        self,
        *,
        messages: list[dict[str, str]],
        response_model: type[T],
        model_name: str,
        timeout_seconds: float,
    ) -> T:
        response = await self.client.responses.create(
            model=model_name,
            input=[
                {
                    "role": message["role"],
                    "content": [{"type": "input_text", "text": message["content"]}],
                }
                for message in messages
            ],
            temperature=0.3,
            timeout=timeout_seconds,
        )
        parsed = parse_json_payload(response.output_text)
        return response_model.model_validate(parsed)

