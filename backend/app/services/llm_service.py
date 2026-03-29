"""Groq LLM entegrasyonu — SSE streaming, retry ve fallback mekanizması."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import AsyncGenerator
from typing import Any

import httpx
from groq import AsyncGroq, APIStatusError

from app.core.config import settings
from app.core.prompts import build_messages
from app.schemas.request import FormField
from app.services.validator_service import ValidationResult, validate_output

logger = logging.getLogger(__name__)


class LLMService:
    """Groq API istemcisi. Stream tabanlı kod üretimi ve sağlık kontrolü sağlar."""

    def __init__(self) -> None:
        self._client = AsyncGroq(
            api_key=settings.GROQ_API_KEY,
            timeout=httpx.Timeout(settings.REQUEST_TIMEOUT, connect=10.0),
        )

    async def health_check(self) -> int | None:
        """Groq bağlantısını test eder, latency (ms) döner."""
        try:
            start = time.monotonic()
            await self._client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
                timeout=settings.HEALTH_TIMEOUT,
            )
            elapsed_ms = int((time.monotonic() - start) * 1000)
            return elapsed_ms
        except Exception:
            logger.exception("Groq health check failed")
            return None

    async def generate_stream(
        self,
        fields: list[FormField],
        framework: str,
        language: str,
    ) -> AsyncGenerator[str, None]:
        """
        SSE stream olarak test kodu üretir.
        İlk deneme doğrudan stream edilir.
        Validation başarısız olursa retry'larda önce toplanır, geçerliyse toplu gönderilir.
        """
        fields_dicts = [f.model_dump(exclude_none=True) for f in fields]
        models = [settings.GROQ_MODEL, settings.GROQ_FALLBACK_MODEL]
        total_retries = 0
        previous_error: str | None = None
        is_first_attempt = True

        for model in models:
            for attempt in range(settings.MAX_RETRIES + 1):
                if attempt > 0 or not is_first_attempt:
                    total_retries += 1

                messages = build_messages(
                    fields=fields_dicts,
                    framework=framework,
                    language=language,
                    previous_error=previous_error,
                )

                collected_code = ""
                try:
                    stream = await self._client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=settings.TEMPERATURE,
                        max_tokens=settings.MAX_TOKENS,
                        top_p=settings.TOP_P,
                        stream=True,
                        timeout=settings.STREAM_TIMEOUT,
                    )

                    if is_first_attempt:
                        async for chunk in stream:
                            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                                token = chunk.choices[0].delta.content
                                collected_code += token
                                yield _sse_data({"chunk": token})
                    else:
                        async for chunk in stream:
                            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                                collected_code += chunk.choices[0].delta.content

                except APIStatusError as exc:
                    logger.warning("Groq API error: %s (model=%s, attempt=%d)", exc.status_code, model, attempt)
                    if exc.status_code in (429, 503):
                        previous_error = f"Groq {exc.status_code}"
                        is_first_attempt = False
                        continue
                    yield _sse_data({
                        "error": "llm_error",
                        "reason": str(exc.status_code),
                        "retries": total_retries,
                    })
                    return
                except TimeoutError:
                    logger.warning("Request timeout (model=%s, attempt=%d)", model, attempt)
                    previous_error = "Request timeout"
                    is_first_attempt = False
                    continue
                except Exception as exc:
                    logger.exception("Stream error (model=%s, attempt=%d)", model, attempt)
                    previous_error = str(exc)
                    is_first_attempt = False
                    continue

                result: ValidationResult = validate_output(collected_code, framework, language)

                if result.valid:
                    if not is_first_attempt:
                        yield _sse_data({"retry": True, "attempt": total_retries})
                        yield _sse_data({"chunk": collected_code})
                    yield _sse_data({"done": True, "retries": total_retries})
                    return

                logger.info(
                    "Validation failed: %s — %s (model=%s, attempt=%d)",
                    result.reason, result.detail, model, attempt,
                )
                previous_error = f"{result.reason}: {result.detail}"
                is_first_attempt = False

        yield _sse_data({
            "error": "generation_failed",
            "reason": "all_models_failed",
            "retries": total_retries,
            "raw": collected_code if collected_code else None,
        })


def _sse_data(payload: dict[str, Any]) -> str:
    """dict -> SSE data satırı."""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def get_llm_service() -> LLMService:
    """FastAPI Depends için factory."""
    return LLMService()
