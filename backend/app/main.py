"""FastAPI uygulama giriş noktası — CORS, router, MongoDB lifecycle ve hata yakalama."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import generate, validate, frameworks, health, history
from app.core.config import settings
from app.core.database import close_mongo, connect_mongo

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_mongo()
    yield
    await close_mongo()


app = FastAPI(
    title="testflow-ai",
    description="Form yapısından otomatik test kodu üreten API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    field_errors = []
    for err in exc.errors():
        loc = " → ".join(str(l) for l in err.get("loc", []) if l != "body")
        field_errors.append(f"{loc}: {err['msg']}" if loc else err["msg"])
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": "Gönderilen veri geçersiz",
            "details": field_errors,
        },
    )


PREFIX = "/api/v1"
app.include_router(health.router, prefix=PREFIX, tags=["health"])
app.include_router(frameworks.router, prefix=PREFIX, tags=["frameworks"])
app.include_router(validate.router, prefix=PREFIX, tags=["validate"])
app.include_router(generate.router, prefix=PREFIX, tags=["generate"])
app.include_router(history.router, prefix=PREFIX, tags=["history"])
