/**
 * SSE stream hook'u — backend'den gelen test kodunu gerçek zamanlı okur,
 * hata mesajlarını Türkçe'ye çevirir ve stream durumunu yönetir.
 */
import { useCallback, useRef, useState } from "react";
import { createGenerateStream } from "../services/api";
import type { Framework, InputMode, Language, SSEData, StreamStatus } from "../types";

const ERROR_MESSAGES: Record<string, string> = {
  "401": "API anahtarı geçersiz veya süresi dolmuş. Lütfen .env dosyasındaki GROQ_API_KEY değerini kontrol edin.",
  "403": "API erişim izni reddedildi. API anahtarınızın yetkileri kontrol edin.",
  "429": "İstek limiti aşıldı. Lütfen birkaç dakika bekleyip tekrar deneyin.",
  "500": "LLM servisi iç hata verdi. Lütfen tekrar deneyin.",
  "503": "LLM servisi geçici olarak kullanılamıyor. Lütfen birkaç dakika bekleyin.",
  all_models_failed: "Tüm modeller başarısız oldu. Servis geçici olarak yanıt veremiyor, lütfen daha sonra tekrar deneyin.",
  no_fields: "Girdiğiniz içerikte form alanı bulunamadı. HTML'in <input>, <select> veya <textarea> içerdiğinden emin olun.",
  generation_failed: "Test kodu üretilemedi. LLM çıktısı doğrulamadan geçemedi.",
  llm_error: "LLM servisiyle bağlantı kurulamadı.",
  invalid_output: "Üretilen kod geçersiz çıktı. Lütfen tekrar deneyin.",
  service_unavailable: "Servis şu anda kullanılamıyor. Lütfen daha sonra tekrar deneyin.",
};

const HTTP_ERROR_MESSAGES: Record<number, string> = {
  422: "Gönderdiğiniz form verisi geçersiz. Lütfen giriş formatını kontrol edin.",
  500: "Sunucu hatası oluştu. Lütfen tekrar deneyin.",
  502: "LLM servisine ulaşılamıyor.",
  503: "Sunucu geçici olarak kullanılamıyor.",
  504: "İstek zaman aşımına uğradı. Lütfen tekrar deneyin.",
};

function resolveErrorMessage(error?: string, reason?: string): string {
  if (reason && ERROR_MESSAGES[reason]) return ERROR_MESSAGES[reason];
  if (error && ERROR_MESSAGES[error]) return ERROR_MESSAGES[error];
  if (reason) return reason;
  if (error) return error;
  return "Bilinmeyen bir hata oluştu.";
}

function resolveHttpError(status: number): string {
  return HTTP_ERROR_MESSAGES[status] || `Sunucu hatası (HTTP ${status})`;
}

interface UseSSEStreamReturn {
  code: string;
  status: StreamStatus;
  retries: number;
  error: string | null;
  start: (mode: InputMode, content: string, framework: Framework, language: Language) => void;
  cancel: () => void;
  reset: () => void;
  setCode: (code: string) => void;
  setStatus: (status: StreamStatus) => void;
}

/** SSE stream yönetimi — kod üretimini başlatır, iptal eder ve durumu izler. */
export function useSSEStream(): UseSSEStreamReturn {
  const [code, setCode] = useState("");
  const [status, setStatus] = useState<StreamStatus>("idle");
  const [retries, setRetries] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setStatus((prev) => (prev === "streaming" ? "cancelled" : prev));
  }, []);

  const reset = useCallback(() => {
    cancel();
    setCode("");
    setStatus("idle");
    setRetries(0);
    setError(null);
  }, [cancel]);

  const start = useCallback(
    async (mode: InputMode, content: string, framework: Framework, language: Language) => {
      cancel();
      setCode("");
      setStatus("streaming");
      setRetries(0);
      setError(null);

      const controller = new AbortController();
      abortRef.current = controller;

      try {
        const response = await createGenerateStream(mode, content, framework, language, controller.signal);
        if (!response.ok) {
          if (response.status === 422) {
            try {
              const body = await response.json();
              const details = body.details as string[] | undefined;
              throw new Error(
                details?.length
                  ? `Geçersiz veri: ${details.join(", ")}`
                  : "Gönderilen form verisi geçersiz. Lütfen giriş formatını kontrol edin.",
              );
            } catch (parseErr) {
              if (parseErr instanceof Error && parseErr.message.startsWith("Geçersiz")) throw parseErr;
              throw new Error(resolveHttpError(422));
            }
          }
          throw new Error(resolveHttpError(response.status));
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("Stream bağlantısı kurulamadı. Lütfen tekrar deneyin.");

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const raw = line.slice(6).trim();
            if (!raw) continue;

            try {
              const data: SSEData = JSON.parse(raw);

              if (data.chunk) {
                setCode((prev) => prev + data.chunk);
              }

              if (data.retry) {
                setCode("");
              }

              if (data.done) {
                setRetries(data.retries ?? 0);
                setStatus("done");
              }

              if (data.error) {
                setError(resolveErrorMessage(data.error, data.reason));
                setRetries(data.retries ?? 0);
                if (data.raw) {
                  setCode(data.raw);
                }
                setStatus("error");
              }
            } catch {
              // skip malformed JSON
            }
          }
        }
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === "AbortError") return;
        if (err instanceof TypeError && err.message.includes("fetch")) {
          setError("Sunucuya bağlanılamıyor. Backend servisinin çalıştığından emin olun.");
        } else {
          setError(err instanceof Error ? err.message : "Bilinmeyen bir hata oluştu.");
        }
        setStatus("error");
      }
    },
    [cancel],
  );

  return { code, status, retries, error, start, cancel, reset, setCode, setStatus };
}
