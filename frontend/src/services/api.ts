/**
 * Backend API istemcisi — tüm HTTP çağrılarını merkezi olarak yönetir.
 */
import type { FrameworksResponse, HistoryListResponse, ValidateResponse, InputMode, Framework, Language } from "../types";

const API_BASE = import.meta.env.VITE_API_URL || "/api/v1";

/** Desteklenen framework ve dil listesini getirir. */
export async function fetchFrameworks(): Promise<FrameworksResponse> {
  const res = await fetch(`${API_BASE}/frameworks`);
  if (!res.ok) throw new Error(`Frameworks fetch failed: ${res.status}`);
  return res.json();
}

/** Form girdisini backend'e gönderip normalize edilmiş alan listesi alır. */
export async function validateForm(
  mode: InputMode,
  content: string,
): Promise<ValidateResponse> {
  const body: Record<string, unknown> = { mode };
  if (mode === "html") body.html_content = content;
  else if (mode === "json") body.json_content = JSON.parse(content);
  else body.manual_fields = JSON.parse(content);

  const res = await fetch(`${API_BASE}/validate-form`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Validate failed: ${res.status}`);
  return res.json();
}

/** Test kodu üretimi için SSE stream bağlantısı başlatır. */
export function createGenerateStream(
  mode: InputMode,
  content: string,
  framework: Framework,
  language: Language,
  signal: AbortSignal,
): Promise<Response> {
  const body: Record<string, unknown> = { mode, framework, language };
  if (mode === "html") body.html_content = content;
  else if (mode === "json") body.json_content = JSON.parse(content);
  else body.manual_fields = JSON.parse(content);

  return fetch(`${API_BASE}/generate-test`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
}

/** Sayfalanmış geçmiş listesini getirir. */
export async function fetchHistory(limit = 20, skip = 0): Promise<HistoryListResponse> {
  const res = await fetch(`${API_BASE}/history?limit=${limit}&skip=${skip}`);
  if (!res.ok) throw new Error(`History fetch failed: ${res.status}`);
  return res.json();
}

/** Belirtilen geçmiş kaydını siler. */
export async function deleteHistory(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/history/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`History delete failed: ${res.status}`);
}
