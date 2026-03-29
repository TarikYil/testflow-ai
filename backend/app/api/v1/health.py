"""GET /health — Servis durumu ve Groq API bağlantı kontrolü."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.config import settings
from app.schemas.response import HealthResponse
from app.services.llm_service import LLMService, get_llm_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(
    llm: LLMService = Depends(get_llm_service),
) -> HealthResponse:
    """Servis durumu ve Groq bağlantı gecikmesi."""
    latency = await llm.health_check()
    return HealthResponse(
        status="ok",
        groq_latency_ms=latency,
        model=settings.GROQ_MODEL,
        fallback_model=settings.GROQ_FALLBACK_MODEL,
    )
