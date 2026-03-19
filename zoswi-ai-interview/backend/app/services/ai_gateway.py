from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from time import monotonic
from typing import Any

from openai import AsyncOpenAI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.metrics import metrics_store

logger = logging.getLogger(__name__)


MODEL_PRICING_PER_1K: dict[str, tuple[float, float]] = {
    # input, output (USD per 1K tokens; indicative)
    "gpt-4.1-mini": (0.0004, 0.0016),
    "gpt-4o-mini": (0.00015, 0.0006),
    "whisper-1": (0.0, 0.0),
    "gpt-4o-mini-transcribe": (0.0, 0.0),
    "gpt-4o-mini-tts": (0.0, 0.0),
}


@dataclass(frozen=True)
class UsageRecord:
    org_id: str | None
    session_id: str | None
    model: str
    input_tokens: int
    output_tokens: int
    audio_seconds: float
    cost_usd: float


class AIGateway:
    def __init__(self, client_factory):
        self._client_factory = client_factory

    async def chat_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        response_format: dict[str, Any] | None = None,
        fallback_models: list[str] | None = None,
        session_id: str | None = None,
        org_id: str | None = None,
        db: AsyncSession | None = None,
    ) -> Any:
        models = [model] + [name for name in (fallback_models or []) if name and name != model]
        last_error: Exception | None = None
        for selected in models:
            try:
                started = monotonic()
                client: AsyncOpenAI | None = await self._client_factory(db)
                if client is None:
                    raise RuntimeError("OpenAI client unavailable.")
                kwargs: dict[str, Any] = {
                    "model": selected,
                    "messages": messages,
                    "temperature": temperature,
                }
                if response_format:
                    kwargs["response_format"] = response_format
                response = await self._retry(lambda: client.chat.completions.create(**kwargs))
                await self._record_usage_from_chat(
                    response=response,
                    model=selected,
                    session_id=session_id,
                    org_id=org_id,
                    db=db,
                )
                logger.info(
                    "AI chat completion success.",
                    extra={
                        "session_id": session_id or "",
                        "model_used": selected,
                        "latency": round((monotonic() - started) * 1000, 2),
                    },
                )
                return response
            except Exception as exc:
                last_error = exc
                logger.warning("AI chat model failed. model=%s error=%s", selected, type(exc).__name__)
        if last_error is not None:
            raise last_error
        raise RuntimeError("No AI model configured.")

    async def transcribe(
        self,
        *,
        model: str,
        file_payload: tuple[str, bytes, str],
        fallback_models: list[str] | None = None,
        session_id: str | None = None,
        org_id: str | None = None,
        db: AsyncSession | None = None,
    ) -> Any:
        models = [model] + [name for name in (fallback_models or []) if name and name != model]
        last_error: Exception | None = None
        for selected in models:
            try:
                client: AsyncOpenAI | None = await self._client_factory(db)
                if client is None:
                    raise RuntimeError("OpenAI client unavailable.")
                response = await self._retry(
                    lambda: client.audio.transcriptions.create(model=selected, file=file_payload)
                )
                await self.record_usage(
                    UsageRecord(
                        org_id=org_id,
                        session_id=session_id,
                        model=selected,
                        input_tokens=0,
                        output_tokens=0,
                        audio_seconds=0.0,
                        cost_usd=0.0,
                    ),
                    db=db,
                )
                return response
            except Exception as exc:
                last_error = exc
                logger.warning("AI transcription failed. model=%s error=%s", selected, type(exc).__name__)
        if last_error is not None:
            raise last_error
        raise RuntimeError("No transcription model configured.")

    async def synthesize_speech(
        self,
        *,
        model: str,
        voice: str,
        text_input: str,
        session_id: str | None = None,
        org_id: str | None = None,
        db: AsyncSession | None = None,
    ) -> bytes:
        client: AsyncOpenAI | None = await self._client_factory(db)
        if client is None:
            return b""
        response = await self._retry(
            lambda: client.audio.speech.create(
                model=model,
                voice=voice,
                input=text_input,
                response_format="mp3",
            )
        )
        data = response.read()
        if hasattr(data, "__await__"):
            data = await data
        await self.record_usage(
            UsageRecord(
                org_id=org_id,
                session_id=session_id,
                model=model,
                input_tokens=0,
                output_tokens=0,
                audio_seconds=0.0,
                cost_usd=0.0,
            ),
            db=db,
        )
        return data

    async def _retry(self, operation, attempts: int = 3, base_delay_seconds: float = 0.25):
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                return await operation()
            except Exception as exc:
                last_error = exc
                if attempt == attempts - 1:
                    break
                await asyncio.sleep(base_delay_seconds * (2**attempt))
        if last_error:
            raise last_error
        raise RuntimeError("Retry operation failed.")

    async def _record_usage_from_chat(
        self,
        *,
        response: Any,
        model: str,
        session_id: str | None,
        org_id: str | None,
        db: AsyncSession | None,
    ) -> None:
        usage = getattr(response, "usage", None)
        input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
        cost_usd = self._estimate_cost(model=model, input_tokens=input_tokens, output_tokens=output_tokens)
        await self.record_usage(
            UsageRecord(
                org_id=org_id,
                session_id=session_id,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                audio_seconds=0.0,
                cost_usd=cost_usd,
            ),
            db=db,
        )

    def _estimate_cost(self, *, model: str, input_tokens: int, output_tokens: int) -> float:
        pricing = MODEL_PRICING_PER_1K.get(model)
        if not pricing:
            return 0.0
        in_cost, out_cost = pricing
        return round((input_tokens / 1000.0) * in_cost + (output_tokens / 1000.0) * out_cost, 6)

    async def record_usage(self, record: UsageRecord, db: AsyncSession | None) -> None:
        metrics_store.add_model_cost(str(record.session_id or "unknown"), float(record.cost_usd or 0.0))
        if db is None:
            return
        try:
            # Isolate optional usage logging from the caller transaction so
            # missing table/column errors don't poison interview writes.
            async with db.begin_nested():
                await db.execute(
                    text(
                        """
                        INSERT INTO usage_ledger (
                            org_id,
                            session_id,
                            model,
                            input_tokens,
                            output_tokens,
                            audio_seconds,
                            cost_usd,
                            timestamp
                        )
                        VALUES (
                            :org_id,
                            :session_id,
                            :model,
                            :input_tokens,
                            :output_tokens,
                            :audio_seconds,
                            :cost_usd,
                            NOW()
                        )
                        """
                    ),
                    {
                        "org_id": record.org_id,
                        "session_id": record.session_id,
                        "model": record.model,
                        "input_tokens": record.input_tokens,
                        "output_tokens": record.output_tokens,
                        "audio_seconds": record.audio_seconds,
                        "cost_usd": record.cost_usd,
                    },
                )
        except Exception as exc:
            # Usage logging must not break interview flow.
            logger.debug(
                "usage_ledger insert skipped (table may not exist yet): %s",
                type(exc).__name__,
            )
