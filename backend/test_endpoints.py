"""Backend endpoint'lerini hızlı test scripti."""
import httpx
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://127.0.0.1:8000/api/v1"

# 1) Health
print("=" * 40)
print("  HEALTH CHECK")
print("=" * 40)
try:
    r = httpx.get(f"{BASE}/health", timeout=15)
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"HATA: {e}")

# 2) Frameworks
print("\n" + "=" * 40)
print("  FRAMEWORKS")
print("=" * 40)
r = httpx.get(f"{BASE}/frameworks")
print(f"Status: {r.status_code}")
print(json.dumps(r.json(), indent=2, ensure_ascii=False))

# 3) Validate Form (HTML mode)
print("\n" + "=" * 40)
print("  VALIDATE-FORM (HTML)")
print("=" * 40)
html = (
    '<form action="/login" method="post">'
    '  <label for="email">Email</label>'
    '  <input id="email" name="email" type="email" required placeholder="Enter email">'
    '  <label for="pw">Password</label>'
    '  <input id="pw" name="password" type="password" required>'
    '  <button type="submit">Login</button>'
    '</form>'
)
r = httpx.post(f"{BASE}/validate-form", json={"mode": "html", "html_content": html})
print(f"Status: {r.status_code}")
print(json.dumps(r.json(), indent=2, ensure_ascii=False))

# 4) Generate Test (SSE stream)
print("\n" + "=" * 40)
print("  GENERATE-TEST (SSE Stream)")
print("=" * 40)
with httpx.stream(
    "POST",
    f"{BASE}/generate-test",
    json={
        "mode": "html",
        "html_content": html,
        "framework": "playwright",
        "language": "python",
    },
    timeout=60,
) as resp:
    print(f"Status: {resp.status_code}")
    print("Stream output:")
    for line in resp.iter_lines():
        if line.startswith("data: "):
            data = json.loads(line[6:])
            if "chunk" in data:
                print(data["chunk"], end="", flush=True)
            elif "done" in data:
                print(f"\n\n--- DONE (retries: {data.get('retries', 0)}) ---")
            elif "error" in data:
                print(f"\n--- ERROR: {data} ---")
