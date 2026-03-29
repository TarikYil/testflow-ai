"""LLM prompt şablonları — system, few-shot ve user prompt'ları burada tanımlıdır."""

from __future__ import annotations

import json

SYSTEM_PROMPT_TEMPLATE = """\
Sen bir test otomasyon uzmanısın.
Görevin: verilen form yapısından SADECE çalışır {framework} ({language}) kodu üretmek.

Kurallar:
- Sadece kod yaz, açıklama yazma
- Markdown kullanma, kod bloğu açma (``` kullanma)
- Import statement'larını ekle
- Her field için ayrı test adımı yaz
- En az bir assertion ekle (expect / assert)
- Fonksiyon adı test_ prefix ile başlasın
"""

FEW_SHOT_INPUT = [
    {"name": "email", "type": "email", "required": True},
    {"name": "password", "type": "password", "required": True},
    {"name": "submit", "type": "submit"},
]

FEW_SHOT_OUTPUTS: dict[str, dict[str, str]] = {
    "playwright": {
        "python": (
            'import pytest\n'
            'from playwright.sync_api import Page, expect\n'
            '\n'
            '\n'
            'def test_login_form(page: Page):\n'
            '    page.goto("http://localhost:3000/login")\n'
            '    page.get_by_label("email").fill("test@example.com")\n'
            '    page.get_by_label("password").fill("password123")\n'
            '    page.get_by_role("button", name="submit").click()\n'
            '    expect(page).not_to_have_url("http://localhost:3000/login")\n'
        ),
        "javascript": (
            "const { test, expect } = require('@playwright/test');\n"
            "\n"
            "test('test login form', async ({ page }) => {\n"
            "    await page.goto('http://localhost:3000/login');\n"
            "    await page.getByLabel('email').fill('test@example.com');\n"
            "    await page.getByLabel('password').fill('password123');\n"
            "    await page.getByRole('button', { name: 'submit' }).click();\n"
            "    await expect(page).not.toHaveURL('http://localhost:3000/login');\n"
            "});\n"
        ),
    },
    "selenium": {
        "python": (
            'import pytest\n'
            'from selenium import webdriver\n'
            'from selenium.webdriver.common.by import By\n'
            '\n'
            '\n'
            'def test_login_form():\n'
            '    driver = webdriver.Chrome()\n'
            '    driver.get("http://localhost:3000/login")\n'
            '    driver.find_element(By.NAME, "email").send_keys("test@example.com")\n'
            '    driver.find_element(By.NAME, "password").send_keys("password123")\n'
            '    driver.find_element(By.CSS_SELECTOR, \'[type="submit"]\').click()\n'
            '    assert driver.current_url != "http://localhost:3000/login"\n'
            '    driver.quit()\n'
        ),
        "javascript": (
            "const { Builder, By } = require('selenium-webdriver');\n"
            "const assert = require('assert');\n"
            "\n"
            "async function testLoginForm() {\n"
            "    const driver = await new Builder().forBrowser('chrome').build();\n"
            "    await driver.get('http://localhost:3000/login');\n"
            "    await driver.findElement(By.name('email')).sendKeys('test@example.com');\n"
            "    await driver.findElement(By.name('password')).sendKeys('password123');\n"
            "    await driver.findElement(By.css('[type=\"submit\"]')).click();\n"
            "    const url = await driver.getCurrentUrl();\n"
            "    assert.notStrictEqual(url, 'http://localhost:3000/login');\n"
            "    await driver.quit();\n"
            "}\n"
        ),
    },
}

USER_PROMPT_TEMPLATE = """\
Framework : {framework}
Language  : {language}
Form Fields:
{fields_json}

Yukarıdaki form için test kodu üret.\
"""

RETRY_SUFFIX_TEMPLATE = """

ÖNCEKİ DENEME BAŞARISIZ. Hata: {error}
Lütfen kuralları tekrar oku ve SADECE düzgün çalışır kod üret.\
"""


def build_messages(
    fields: list[dict],
    framework: str,
    language: str,
    *,
    previous_error: str | None = None,
) -> list[dict[str, str]]:
    """LLM'e gönderilecek system + few-shot + user mesaj listesini oluşturur."""
    system_text = SYSTEM_PROMPT_TEMPLATE.format(
        framework=framework,
        language=language,
    )

    few_shot_output = FEW_SHOT_OUTPUTS.get(framework, {}).get(language, "")

    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_text},
    ]

    if few_shot_output:
        messages.extend([
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(
                    framework=framework,
                    language=language,
                    fields_json=json.dumps(FEW_SHOT_INPUT, indent=2),
                ),
            },
            {"role": "assistant", "content": few_shot_output},
        ])

    user_text = USER_PROMPT_TEMPLATE.format(
        framework=framework,
        language=language,
        fields_json=json.dumps(fields, indent=2, ensure_ascii=False),
    )
    if previous_error:
        user_text += RETRY_SUFFIX_TEMPLATE.format(error=previous_error)

    messages.append({"role": "user", "content": user_text})
    return messages
