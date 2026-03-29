"""MongoDB bağlantı yönetimi — Motor async client ile lifecycle kontrolü."""

from __future__ import annotations

import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_mongo() -> None:
    """MongoDB'ye bağlanır, index'leri oluşturur. FastAPI lifespan'da çağrılır."""
    global _client, _db
    logger.info("Connecting to MongoDB: %s", settings.MONGO_URL)
    _client = AsyncIOMotorClient(settings.MONGO_URL)
    _db = _client[settings.MONGO_DB]
    await _db.command("ping")
    await _db["history"].create_index("config_hash", unique=True, sparse=True)
    await _db["history"].create_index([("updated_at", -1)])
    logger.info("MongoDB connected — db: %s", settings.MONGO_DB)


async def close_mongo() -> None:
    """MongoDB bağlantısını kapatır. FastAPI shutdown'da çağrılır."""
    global _client, _db
    if _client:
        _client.close()
        logger.info("MongoDB connection closed")
    _client = None
    _db = None


def get_db() -> AsyncIOMotorDatabase:
    """Aktif veritabanı referansını döner. Bağlantı yoksa RuntimeError fırlatır."""
    if _db is None:
        raise RuntimeError("MongoDB not connected. Call connect_mongo() first.")
    return _db
