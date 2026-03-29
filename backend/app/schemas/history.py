"""Geçmiş (history) veri şemaları — MongoDB kayıtlarının Pydantic modelleri."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.request import FormField


class HistoryItem(BaseModel):
    """Tek bir test üretim kaydı. Girdi, çıktı ve durum bilgisi içerir."""
    id: str = Field(alias="_id", default="")
    mode: str
    input_content: str
    fields: list[FormField]
    framework: str
    language: str
    generated_code: str
    status: Literal["success", "error"]
    error_reason: Optional[str] = None
    retries: int = 0
    model_used: str
    config_hash: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


class HistoryListResponse(BaseModel):
    """Sayfalanmış history listesi yanıtı."""
    items: list[HistoryItem]
    total: int
