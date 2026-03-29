import { useEffect, useRef } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { CheckCircle2, XCircle, Copy, Check, AlertTriangle, Terminal, StopCircle, Download } from "lucide-react";
import { useState } from "react";
import type { Framework, InputMode, Language, StreamStatus } from "../types";
import { exportAsZip } from "../utils/exportZip";

/** ZIP indirme için gerekli girdi bağlamı. */
export interface ExportContext {
  inputContent: string;
  mode: InputMode;
  framework: Framework;
  language: Language;
}

interface Props {
  code: string;
  status: StreamStatus;
  language: string;
  retries: number;
  error: string | null;
  onDone?: () => void;
  exportContext?: ExportContext | null;
}

/** Sağ panel — syntax-highlighted kod çıktısı, durum badge'i, hata banner'ı ve indirme. */
export default function OutputPanel({ code, status, language, retries, error, onDone, exportContext }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [copied, setCopied] = useState(false);
  const prevStatusRef = useRef(status);

  useEffect(() => {
    if (scrollRef.current && status === "streaming") {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [code, status]);

  useEffect(() => {
    if (prevStatusRef.current === "streaming" && (status === "done" || status === "error")) {
      onDone?.();
    }
    prevStatusRef.current = status;
  }, [status, onDone]);

  const handleCopy = async () => {
    if (!code) return;
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = async () => {
    if (!code || !exportContext) return;
    await exportAsZip({ code, ...exportContext });
  };

  const canDownload = !!code && !!exportContext && status !== "streaming";
  const syntaxLang = language === "python" ? "python" : "javascript";

  return (
    <div className="flex h-full flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between border-b border-slate-700/50 px-4 py-2.5">
        <div className="flex items-center gap-2">
          <Terminal size={14} className="text-slate-400" />
          <span className="text-xs font-medium text-slate-400">Çıktı</span>
          <StatusBadge status={status} retries={retries} />
        </div>
        <div className="flex items-center gap-1">
          {canDownload && (
            <button
              onClick={handleDownload}
              className="flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs text-slate-400 transition-colors hover:bg-slate-700/50 hover:text-slate-200"
              title="Girdi + çıktı + meta bilgisini ZIP olarak indir"
            >
              <Download size={13} />
              İndir
            </button>
          )}
          {code && (
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs text-slate-400 transition-colors hover:bg-slate-700/50 hover:text-slate-200"
            >
              {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
              {copied ? "Kopyalandı" : "Kopyala"}
            </button>
          )}
        </div>
      </div>

      {/* Error Banner */}
      {status === "error" && error && (
        <div className="mx-3 mt-3 flex flex-col gap-1.5 rounded-lg border border-red-500/20 bg-red-500/5 px-3 py-2.5">
          <div className="flex items-start gap-2">
            <XCircle size={16} className="mt-0.5 shrink-0 text-red-400" />
            <p className="text-xs leading-relaxed text-red-300">{error}</p>
          </div>
          {retries > 0 && (
            <p className="ml-6 text-[0.65rem] text-red-400/50">
              {retries} deneme yapıldı, tüm denemeler başarısız oldu.
            </p>
          )}
        </div>
      )}

      {/* Code Area */}
      <div ref={scrollRef} className="flex-1 overflow-auto p-3">
        {!code && status === "idle" && (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-slate-600">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-800/50 ring-1 ring-slate-700/50">
              <Terminal size={28} />
            </div>
            <p className="text-sm">Henüz test kodu üretilmedi</p>
            <p className="text-xs text-slate-700">Sol panelden form yapısını girin ve "Test Üret"e tıklayın</p>
          </div>
        )}

        {code && (
          <SyntaxHighlighter
            language={syntaxLang}
            style={vscDarkPlus}
            showLineNumbers
            wrapLines
            customStyle={{
              margin: 0,
              borderRadius: "0.5rem",
              fontSize: "0.8rem",
              background: "rgb(15 23 42 / 0.5)",
              border: "1px solid rgb(51 65 85 / 0.5)",
            }}
            lineNumberStyle={{ color: "#475569", fontSize: "0.7rem" }}
          >
            {code}
          </SyntaxHighlighter>
        )}

        {status === "streaming" && (
          <div className="mt-2 flex items-center gap-2 text-xs text-violet-400">
            <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-violet-500" />
            Kod üretiliyor...
          </div>
        )}
      </div>

      {/* AI Warning */}
      {(status === "done" || code) && status !== "idle" && (
        <div className="border-t border-slate-700/50 px-4 py-2">
          <div className="flex items-center gap-1.5 text-[0.65rem] text-amber-500/60">
            <AlertTriangle size={11} />
            Bu kod AI tarafından üretilmiştir. Çalıştırmadan önce gözden geçiriniz.
          </div>
        </div>
      )}
    </div>
  );
}

/** Stream durumunu gösteren renkli badge bileşeni. */
function StatusBadge({ status, retries }: { status: StreamStatus; retries: number }) {
  switch (status) {
    case "streaming":
      return (
        <span className="flex items-center gap-1 rounded-full bg-violet-500/10 px-2 py-0.5 text-[0.65rem] font-medium text-violet-400 ring-1 ring-violet-500/20">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-violet-500" />
          streaming
        </span>
      );
    case "done":
      return (
        <span className="flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[0.65rem] font-medium text-emerald-400 ring-1 ring-emerald-500/20">
          <CheckCircle2 size={11} />
          tamamlandı{retries > 0 && ` (${retries} retry)`}
        </span>
      );
    case "error":
      return (
        <span className="flex items-center gap-1 rounded-full bg-red-500/10 px-2 py-0.5 text-[0.65rem] font-medium text-red-400 ring-1 ring-red-500/20">
          <XCircle size={11} />
          hata
        </span>
      );
    case "cancelled":
      return (
        <span className="flex items-center gap-1 rounded-full bg-amber-500/10 px-2 py-0.5 text-[0.65rem] font-medium text-amber-400 ring-1 ring-amber-500/20">
          <StopCircle size={11} />
          iptal edildi
        </span>
      );
    default:
      return null;
  }
}
