"""Form girdi ayrıştırıcı — HTML, JSON ve Manuel modlardan FormField listesi üretir."""

from __future__ import annotations

from bs4 import BeautifulSoup, Tag

from app.schemas.request import FormField, GenerateTestRequest, InputMode, ValidateFormRequest
from app.schemas.response import FormMeta

INPUT_TYPES = {
    "text", "email", "password", "number", "tel", "url", "search",
    "date", "time", "datetime-local", "month", "week", "color",
    "range", "file", "hidden", "checkbox", "radio", "submit", "reset",
    "button",
}


def _extract_field_from_tag(tag: Tag) -> FormField | None:
    """Tek bir HTML input/select/textarea etiketinden FormField çıkarır."""
    tag_name = tag.name

    if tag_name == "input":
        field_type = (tag.get("type") or "text").lower()
    elif tag_name == "select":
        field_type = "select"
    elif tag_name == "textarea":
        field_type = "textarea"
    else:
        return None

    name = tag.get("name") or tag.get("id") or ""
    if not name and field_type not in ("submit", "reset", "button"):
        return None

    label_text: str | None = None
    if tag.get("id"):
        parent_form = tag.find_parent("form") or tag.parent
        if parent_form:
            label_tag = parent_form.find("label", attrs={"for": tag["id"]})
            if label_tag:
                label_text = label_tag.get_text(strip=True)

    if not label_text:
        label_text = tag.get("aria-label") or tag.get("placeholder") or None

    return FormField(
        name=name,
        type=field_type,
        label=label_text,
        required=tag.has_attr("required"),
        placeholder=tag.get("placeholder"),
    )


def parse_html(html: str) -> tuple[list[FormField], FormMeta]:
    """Ham HTML'den FormField listesi ve form meta bilgisi çıkarır."""
    soup = BeautifulSoup(html, "html.parser")

    form_tag = soup.find("form")
    meta = FormMeta()
    if form_tag and isinstance(form_tag, Tag):
        meta = FormMeta(
            action=form_tag.get("action"),
            method=form_tag.get("method"),
        )

    search_root = form_tag if form_tag else soup
    fields: list[FormField] = []

    for tag in search_root.find_all(["input", "select", "textarea"]):
        field = _extract_field_from_tag(tag)
        if field:
            fields.append(field)

    return fields, meta


def normalize_fields(request: ValidateFormRequest | GenerateTestRequest) -> tuple[list[FormField], FormMeta]:
    """Herhangi bir input modundan normalize edilmiş FormField listesi döner."""
    if request.mode == InputMode.html:
        return parse_html(request.html_content or "")
    elif request.mode == InputMode.json:
        return (request.json_content or []), FormMeta()
    elif request.mode == InputMode.manual:
        return (request.manual_fields or []), FormMeta()
    raise ValueError(f"Unknown mode: {request.mode}")
