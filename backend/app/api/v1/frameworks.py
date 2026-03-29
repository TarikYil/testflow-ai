"""GET /frameworks — Desteklenen test framework ve dil listesi."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.response import FrameworkOption, FrameworksResponse

router = APIRouter()

SUPPORTED_FRAMEWORKS: list[FrameworkOption] = [
    FrameworkOption(
        id="playwright",
        label="Playwright",
        languages=["python", "javascript"],
    ),
    FrameworkOption(
        id="selenium",
        label="Selenium",
        languages=["python", "javascript"],
    ),
]


@router.get("/frameworks", response_model=FrameworksResponse)
async def list_frameworks() -> FrameworksResponse:
    """Desteklenen framework ve dil listesini döner."""
    return FrameworksResponse(frameworks=SUPPORTED_FRAMEWORKS)
