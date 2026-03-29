"""Geçmiş endpoint'leri — listeleme, detay ve silme."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.history import HistoryListResponse
from app.services import history_service

router = APIRouter()


@router.get("/history", response_model=HistoryListResponse)
async def list_history(
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
) -> HistoryListResponse:
    """Sayfalama ile history listesi döner."""
    items, total = await history_service.list_history(limit=limit, skip=skip)
    return HistoryListResponse(items=items, total=total)


@router.get("/history/{history_id}")
async def get_history(history_id: str):
    """Tek bir history kaydı döner."""
    item = await history_service.get_history(history_id)
    if not item:
        raise HTTPException(status_code=404, detail="History kaydı bulunamadı")
    return item


@router.delete("/history/{history_id}")
async def delete_history(history_id: str):
    """History kaydı siler."""
    deleted = await history_service.delete_history(history_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="History kaydı bulunamadı")
    return {"deleted": True}
