/**
 * Uygulama genelinde kullanılan TypeScript tip tanımları.
 */

/** Girdi modu: HTML yapıştırma, JSON tanımı veya manuel alan girişi. */
export type InputMode = "html" | "json" | "manual";
/** Desteklenen test framework'leri. */
export type Framework = "playwright" | "selenium";
/** Desteklenen programlama dilleri. */
export type Language = "python" | "javascript";

/** Normalize edilmiş tek bir form alanı. */
export interface FormField {
  name: string;
  type: string;
  label?: string;
  required?: boolean;
  placeholder?: string;
}

/** HTML form etiketinin meta bilgisi. */
export interface FormMeta {
  action?: string;
  method?: string;
}

/** POST /validate-form yanıtı. */
export interface ValidateResponse {
  fields: FormField[];
  form_meta: FormMeta;
  warnings: string[];
}

export interface FrameworkOption {
  id: Framework;
  label: string;
  languages: Language[];
}

export interface FrameworksResponse {
  frameworks: FrameworkOption[];
}

export interface HealthResponse {
  status: string;
  groq_latency_ms: number | null;
  model: string;
  fallback_model: string;
}

/** SSE stream'den gelen tek bir veri satırının yapısı. */
export interface SSEData {
  chunk?: string;
  done?: boolean;
  retries?: number;
  retry?: boolean;
  attempt?: number;
  error?: string;
  reason?: string;
  raw?: string;
}

/** Stream sürecinin olası durumları. */
export type StreamStatus = "idle" | "streaming" | "done" | "error" | "cancelled";

/** Tek bir test üretim geçmişi kaydı. */
export interface HistoryItem {
  _id: string;
  mode: InputMode;
  input_content: string;
  fields: FormField[];
  framework: Framework;
  language: Language;
  generated_code: string;
  status: "success" | "error";
  error_reason?: string | null;
  retries: number;
  model_used: string;
  config_hash?: string;
  created_at: string;
  updated_at?: string | null;
}

/** Sayfalanmış geçmiş listesi yanıtı. */
export interface HistoryListResponse {
  items: HistoryItem[];
  total: number;
}
