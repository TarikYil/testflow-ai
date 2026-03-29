"""API istek şemaları — form doğrulama ve test üretim girdileri."""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, model_validator


class InputMode(str, Enum):
    """Desteklenen girdi modları."""
    html = "html"
    json = "json"
    manual = "manual"


class FormField(BaseModel):
    """Normalize edilmiş tek bir form alanı."""
    name: str
    type: str
    label: Optional[str] = None
    required: Optional[bool] = None
    placeholder: Optional[str] = None


class ValidateFormRequest(BaseModel):
    """POST /validate-form isteği. Mode'a göre ilgili content alanı zorunludur."""
    mode: InputMode
    html_content: Optional[str] = None
    json_content: Optional[list[FormField]] = None
    manual_fields: Optional[list[FormField]] = None

    @model_validator(mode="after")
    def check_content(self) -> "ValidateFormRequest":
        if self.mode == InputMode.html and not self.html_content:
            raise ValueError("html_content required for html mode")
        if self.mode == InputMode.json and not self.json_content:
            raise ValueError("json_content required for json mode")
        if self.mode == InputMode.manual and not self.manual_fields:
            raise ValueError("manual_fields required for manual mode")
        return self


class GenerateTestRequest(BaseModel):
    """POST /generate-test isteği. Framework ve dil seçimi içerir."""
    mode: InputMode
    html_content: Optional[str] = None
    json_content: Optional[list[FormField]] = None
    manual_fields: Optional[list[FormField]] = None
    framework: Literal["playwright", "selenium"] = "playwright"
    language: Literal["python", "javascript"] = "python"

    @model_validator(mode="after")
    def check_content(self) -> "GenerateTestRequest":
        if self.mode == InputMode.html and not self.html_content:
            raise ValueError("html_content required for html mode")
        if self.mode == InputMode.json and not self.json_content:
            raise ValueError("json_content required for json mode")
        if self.mode == InputMode.manual and not self.manual_fields:
            raise ValueError("manual_fields required for manual mode")
        return self
