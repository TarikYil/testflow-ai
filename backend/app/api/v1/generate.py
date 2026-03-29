"""POST /generate-test — Form yapısından test kodu üretir, SSE stream ile döner."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.schemas.request import FormField, GenerateTestRequest
from app.services.llm_service import LLMService, get_llm_service
from app.services.parser_service import normalize_fields
from app.services import history_service

logger = logging.getLogger(__name__)

router = APIRouter()


async def _stream_and_save(
    llm_stream: AsyncGenerator[str, None],
    *,
    mode: str,
    input_content: str,
    fields: list[FormField],
    framework: str,
    language: str,
) -> AsyncGenerator[str, None]:
    """LLM stream'ini sarmalayarak sonucu MongoDB'ye kaydeder."""
    collected_code = ""
    status = "success"
    error_reason: str | None = None
    retries = 0

    async for sse_line in llm_stream:
        yield sse_line

        if sse_line.startswith("data: "):
            try:
                data = json.loads(sse_line[6:].strip())
                if "chunk" in data:
                    collected_code += data["chunk"]
                if "done" in data:
                    retries = data.get("retries", 0)
                if "retry" in data:
                    collected_code = ""
                if "error" in data:
                    status = "error"
                    error_reason = data.get("reason")
                    retries = data.get("retries", 0)
                    if data.get("raw"):
                        collected_code = data["raw"]
            except (json.JSONDecodeError, KeyError):
                pass

    try:
        await history_service.save_history(
            mode=mode,
            input_content=input_content,
            fields=fields,
            framework=framework,
            language=language,
            generated_code=collected_code,
            status=status,
            error_reason=error_reason,
            retries=retries,
            model_used=settings.GROQ_MODEL,
        )
    except Exception:
        logger.exception("Failed to save history")


@router.post("/generate-test")
async def generate_test(
    body: GenerateTestRequest,
    llm: LLMService = Depends(get_llm_service),
) -> StreamingResponse:
    """Form yapısından test kodu üretir. SSE stream ile döner."""
    fields, _meta = normalize_fields(body)

    input_content = body.html_content or ""
    if body.mode == "json" and body.json_content:
        input_content = json.dumps([f.model_dump(exclude_none=True) for f in body.json_content], ensure_ascii=False)
    elif body.mode == "manual" and body.manual_fields:
        input_content = json.dumps([f.model_dump(exclude_none=True) for f in body.manual_fields], ensure_ascii=False)

    if not fields:
        async def empty_error():
            yield f"data: {json.dumps({'error': 'no_fields', 'reason': 'Form alanı bulunamadı'})}\n\n"

        return StreamingResponse(empty_error(), media_type="text/event-stream")

    wrapped = _stream_and_save(
        llm.generate_stream(fields=fields, framework=body.framework, language=body.language),
        mode=body.mode,
        input_content=input_content,
        fields=fields,
        framework=body.framework,
        language=body.language,
    )

    return StreamingResponse(
        wrapped,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
