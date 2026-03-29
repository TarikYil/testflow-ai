"""LLM çıktı doğrulayıcı — syntax, import ve test fonksiyonu kontrolleri."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import Literal

ValidationReason = Literal[
    "syntax_error",
    "missing_import",
    "missing_test_fn",
    "empty_output",
]


@dataclass
class ValidationResult:
    """Doğrulama sonucu: geçerlilik durumu ve hata detayı."""
    valid: bool
    reason: ValidationReason | None = None
    detail: str | None = None


FRAMEWORK_IMPORT_PATTERNS: dict[str, list[str]] = {
    "playwright": ["playwright"],
    "selenium": ["selenium"],
}

JS_TEST_FN_PATTERN = re.compile(
    r"""(?:test\s*\(|describe\s*\(|it\s*\(|function\s+test)""",
)


def _clean_output(code: str) -> str:
    """LLM çıktısından olası markdown code fence'lerini temizler."""
    code = code.strip()
    if code.startswith("```"):
        first_newline = code.find("\n")
        if first_newline != -1:
            code = code[first_newline + 1:]
    if code.endswith("```"):
        code = code[:-3]
    return code.strip()


def validate_python(code: str, framework: str) -> ValidationResult:
    """Python kodu için 3 aşamalı doğrulama."""
    code = _clean_output(code)

    if not code:
        return ValidationResult(valid=False, reason="empty_output", detail="LLM boş yanıt döndü")

    try:
        ast.parse(code)
    except SyntaxError as exc:
        return ValidationResult(
            valid=False,
            reason="syntax_error",
            detail=f"Satır {exc.lineno}: {exc.msg}",
        )

    required_imports = FRAMEWORK_IMPORT_PATTERNS.get(framework, [])
    for imp in required_imports:
        if imp not in code:
            return ValidationResult(
                valid=False,
                reason="missing_import",
                detail=f"'{imp}' import bulunamadı",
            )

    if "def test_" not in code:
        return ValidationResult(
            valid=False,
            reason="missing_test_fn",
            detail="'def test_' fonksiyonu bulunamadı",
        )

    return ValidationResult(valid=True)


def validate_javascript(code: str, framework: str) -> ValidationResult:
    """JavaScript kodu için temel doğrulama."""
    code = _clean_output(code)

    if not code:
        return ValidationResult(valid=False, reason="empty_output", detail="LLM boş yanıt döndü")

    required_imports = FRAMEWORK_IMPORT_PATTERNS.get(framework, [])
    for imp in required_imports:
        if imp not in code:
            return ValidationResult(
                valid=False,
                reason="missing_import",
                detail=f"'{imp}' import/require bulunamadı",
            )

    if not JS_TEST_FN_PATTERN.search(code):
        return ValidationResult(
            valid=False,
            reason="missing_test_fn",
            detail="Test fonksiyonu bulunamadı (test/describe/it)",
        )

    return ValidationResult(valid=True)


def validate_output(code: str, framework: str, language: str) -> ValidationResult:
    """Dile göre doğrulama pipeline'ını çalıştırır."""
    if language == "python":
        return validate_python(code, framework)
    elif language == "javascript":
        return validate_javascript(code, framework)
    return ValidationResult(valid=False, reason="syntax_error", detail=f"Desteklenmeyen dil: {language}")
