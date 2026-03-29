"""API yanıt şemaları — endpoint çıktılarının veri sözleşmeleri."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.schemas.request import FormField


class FormMeta(BaseModel):
    """HTML <form> etiketinin action ve method bilgisi."""
    action: Optional[str] = None
    method: Optional[str] = None


class ValidateFormResponse(BaseModel):
    """Form doğrulama yanıtı — parse edilmiş alanlar ve uyarılar."""
    fields: list[FormField]
    form_meta: FormMeta = FormMeta()
    warnings: list[str] = []


class FrameworkOption(BaseModel):
    """Tek bir framework seçeneği ve desteklediği diller."""
    id: str
    label: str
    languages: list[str]


class FrameworksResponse(BaseModel):
    frameworks: list[FrameworkOption]


class HealthResponse(BaseModel):
    """GET /health yanıtı — servis durumu ve LLM bağlantı gecikmesi."""
    status: str
    groq_latency_ms: Optional[int] = None
    model: str
    fallback_model: str


class GenerateErrorResponse(BaseModel):
    """SSE stream'de hata durumunda dönen yapı."""
    error: str
    reason: str
    retries: int = 0
    raw: Optional[str] = None


class SSEChunk(BaseModel):
    """Tek bir SSE data satırının yapısı."""
    chunk: Optional[str] = None
    done: Optional[bool] = None
    retries: Optional[int] = None
    error: Optional[str] = None
    reason: Optional[str] = None
    raw: Optional[str] = None
