"""Geçmiş (history) CRUD servisi — MongoDB ile upsert, listeleme ve silme."""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

from bson import ObjectId

from app.core.database import get_db
from app.schemas.history import HistoryItem
from app.schemas.request import FormField

COLLECTION = "history"


def _config_hash(mode: str, input_content: str, framework: str, language: str) -> str:
    """Aynı konfigürasyonu tespit etmek için deterministik hash üretir."""
    raw = f"{mode}|{input_content.strip()}|{framework}|{language}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def save_history(
    *,
    mode: str,
    input_content: str,
    fields: list[FormField],
    framework: str,
    language: str,
    generated_code: str,
    status: str,
    error_reason: str | None = None,
    retries: int = 0,
    model_used: str,
) -> str:
    """
    Aynı konfigürasyon (mode + input + framework + language) varsa günceller,
    yoksa yeni kayıt oluşturur. Güncellenen/eklenen document'ın id'sini döner.
    """
    cfg_hash = _config_hash(mode, input_content, framework, language)

    update_doc: dict[str, Any] = {
        "$set": {
            "mode": mode,
            "input_content": input_content,
            "fields": [f.model_dump(exclude_none=True) for f in fields],
            "framework": framework,
            "language": language,
            "generated_code": generated_code,
            "status": status,
            "error_reason": error_reason,
            "retries": retries,
            "model_used": model_used,
            "config_hash": cfg_hash,
            "updated_at": datetime.utcnow(),
        },
        "$setOnInsert": {
            "created_at": datetime.utcnow(),
        },
    }

    result = await get_db()[COLLECTION].find_one_and_update(
        {"config_hash": cfg_hash},
        update_doc,
        upsert=True,
        return_document=True,
    )
    return str(result["_id"])


async def list_history(*, limit: int = 20, skip: int = 0) -> tuple[list[HistoryItem], int]:
    """Sayfalama ile history listesi döner (yeniden eskiye)."""
    db = get_db()
    total = await db[COLLECTION].count_documents({})
    cursor = db[COLLECTION].find().sort("updated_at", -1).skip(skip).limit(limit)

    items: list[HistoryItem] = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        items.append(HistoryItem(**doc))
    return items, total


async def get_history(history_id: str) -> HistoryItem | None:
    """Tek bir history kaydı döner."""
    if not ObjectId.is_valid(history_id):
        return None
    doc = await get_db()[COLLECTION].find_one({"_id": ObjectId(history_id)})
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])
    return HistoryItem(**doc)


async def delete_history(history_id: str) -> bool:
    """History kaydı siler, başarılıysa True döner."""
    if not ObjectId.is_valid(history_id):
        return False
    result = await get_db()[COLLECTION].delete_one({"_id": ObjectId(history_id)})
    return result.deleted_count > 0
