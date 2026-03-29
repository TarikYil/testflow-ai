/**
 * Ana uygulama bileşeni — sol panel (girdi + geçmiş) ve sağ panel (çıktı)
 * arasındaki state koordinasyonunu yönetir.
 */
import { useCallback, useState } from "react";
import Header from "./components/Header";
import InputPanel from "./components/InputPanel";
import type { InputSnapshot } from "./components/InputPanel";
import OutputPanel from "./components/OutputPanel";
import HistorySidebar from "./components/HistorySidebar";
import { useSSEStream } from "./hooks/useSSEStream";
import type { Framework, HistoryItem, InputMode, Language } from "./types";

interface ExportContext {
  inputContent: string;
  mode: InputMode;
  framework: Framework;
  language: Language;
}

export default function App() {
  const [language, setLanguage] = useState<Language>("python");
  const [historyRefresh, setHistoryRefresh] = useState(0);
  const [inputSnapshot, setInputSnapshot] = useState<InputSnapshot | null>(null);
  const [exportCtx, setExportCtx] = useState<ExportContext | null>(null);
  const { code, status, retries, error, start, cancel, reset, setCode, setStatus } = useSSEStream();

  const handleGenerate = (mode: InputMode, content: string, framework: Framework, lang: Language) => {
    setLanguage(lang);
    setInputSnapshot(null);
    setExportCtx({ inputContent: content, mode, framework, language: lang });
    reset();
    start(mode, content, framework, lang);
  };

  const handleStreamDone = useCallback(() => {
    setHistoryRefresh((n) => n + 1);
  }, []);

  const handleHistorySelect = (item: HistoryItem) => {
    reset();
    setLanguage(item.language);
    setCode(item.generated_code);
    setStatus(item.status === "success" ? "done" : "error");

    const snap: InputSnapshot = {
      mode: item.mode,
      content: item.input_content || "",
      framework: item.framework,
      language: item.language,
    };
    setInputSnapshot(snap);

    setExportCtx({
      inputContent: item.input_content || "",
      mode: item.mode,
      framework: item.framework,
      language: item.language,
    });
  };

  return (
    <div className="flex h-screen flex-col bg-slate-950 text-slate-200">
      <Header />
      <main className="flex flex-1 overflow-hidden">
        {/* Sol Panel — Input + History */}
        <div className="flex w-[420px] shrink-0 flex-col border-r border-slate-700/50 bg-slate-900/40">
          <div className="flex-1 overflow-hidden">
            <InputPanel
              onGenerate={handleGenerate}
              status={status}
              onCancel={cancel}
              snapshot={inputSnapshot}
            />
          </div>
          <HistorySidebar refreshKey={historyRefresh} onSelect={handleHistorySelect} />
        </div>

        {/* Sag Panel — Output */}
        <div className="flex flex-1 flex-col bg-slate-950">
          <OutputPanel
            code={code}
            status={status}
            language={language}
            retries={retries}
            error={error}
            onDone={handleStreamDone}
            exportContext={exportCtx}
          />
        </div>
      </main>
    </div>
  );
}
