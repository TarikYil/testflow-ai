"""POST /validate-form — Form girdisini parse eder, normalize edilmiş alan listesi döner."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.request import ValidateFormRequest
from app.schemas.response import ValidateFormResponse
from app.services.parser_service import normalize_fields

router = APIRouter()


@router.post("/validate-form", response_model=ValidateFormResponse)
async def validate_form(body: ValidateFormRequest) -> ValidateFormResponse:
    """Form input'unu alır, normalize edilmiş field listesi ve meta döner."""
    fields, meta = normalize_fields(body)

    warnings: list[str] = []
    if not fields:
        warnings.append("Hiç form alanı bulunamadı. HTML'in <form> etiketi içerdiğinden emin olun.")

    return ValidateFormResponse(
        fields=fields,
        form_meta=meta,
        warnings=warnings,
    )
