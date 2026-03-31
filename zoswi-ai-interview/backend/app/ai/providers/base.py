from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class AIProvider(ABC):
    @abstractmethod
    async def generate_structured(
        self,
        *,
        messages: list[dict[str, str]],
        response_model: type[T],
        model_name: str,
        timeout_seconds: float,
    ) -> T:
        raise NotImplementedError

