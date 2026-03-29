import { useEffect, useState } from "react";
import { Code2, FileJson, PenLine, Play, Loader2 } from "lucide-react";
import { fetchFrameworks } from "../services/api";
import type { Framework, FrameworkOption, InputMode, Language, StreamStatus } from "../types";

/** Geçmişten yüklenen girdinin tüm parametreleri. */
export interface InputSnapshot {
  mode: InputMode;
  content: string;
  framework: Framework;
  language: Language;
}

interface Props {
  onGenerate: (mode: InputMode, content: string, framework: Framework, language: Language) => void;
  status: StreamStatus;
  onCancel: () => void;
  snapshot?: InputSnapshot | null;
}

const MODE_TABS: { id: InputMode; label: string; icon: React.ReactNode; placeholder: string }[] = [
  {
    id: "html",
    label: "HTML",
    icon: <Code2 size={14} />,
    placeholder: '<form action="/login" method="post">\n  <label for="email">Email</label>\n  <input id="email" name="email" type="email" required>\n  <label for="pw">Password</label>\n  <input id="pw" name="password" type="password" required>\n  <button type="submit">Login</button>\n</form>',
  },
  {
    id: "json",
    label: "JSON",
    icon: <FileJson size={14} />,
    placeholder: '[\n  {"name": "email", "type": "email", "required": true},\n  {"name": "password", "type": "password", "required": true},\n  {"name": "submit", "type": "submit"}\n]',
  },
  {
    id: "manual",
    label: "Manuel",
    icon: <PenLine size={14} />,
    placeholder: '[\n  {"name": "username", "type": "text", "label": "Kullanıcı Adı", "required": true},\n  {"name": "password", "type": "password", "label": "Şifre", "required": true}\n]',
  },
];

/** Sol panel — mod sekmeleri, framework/dil seçici, textarea ve üret butonu. */
export default function InputPanel({ onGenerate, status, onCancel, snapshot }: Props) {
  const [mode, setMode] = useState<InputMode>("html");
  const [content, setContent] = useState("");
  const [framework, setFramework] = useState<Framework>("playwright");
  const [language, setLanguage] = useState<Language>("python");
  const [frameworks, setFrameworks] = useState<FrameworkOption[]>([]);

  useEffect(() => {
    fetchFrameworks()
      .then((res) => setFrameworks(res.frameworks))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (snapshot) {
      setMode(snapshot.mode);
      setContent(snapshot.content);
      setFramework(snapshot.framework);
      setLanguage(snapshot.language);
    }
  }, [snapshot]);

  const activeTab = MODE_TABS.find((t) => t.id === mode)!;
  const isStreaming = status === "streaming";
  const selectedFw = frameworks.find((f) => f.id === framework);
  const availableLanguages = selectedFw?.languages ?? ["python", "javascript"];

  const handleSubmit = () => {
    if (!content.trim()) return;
    onGenerate(mode, content, framework, language);
  };

  return (
    <div className="flex h-full flex-col">
      {/* Mode Tabs */}
      <div className="flex items-center gap-1 border-b border-slate-700/50 px-3 pt-3 pb-0">
        {MODE_TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setMode(tab.id)}
            className={`flex items-center gap-1.5 rounded-t-lg border-b-2 px-3 py-2 text-xs font-medium transition-colors ${
              mode === tab.id
                ? "border-violet-500 bg-slate-800/50 text-violet-400"
                : "border-transparent text-slate-400 hover:bg-slate-800/30 hover:text-slate-300"
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Options Row */}
      <div className="flex flex-wrap items-center gap-3 border-b border-slate-700/50 px-4 py-3">
        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-slate-400">Framework</label>
          <select
            value={framework}
            onChange={(e) => {
              const fw = e.target.value as Framework;
              setFramework(fw);
              const fwOption = frameworks.find((f) => f.id === fw);
              if (fwOption && !fwOption.languages.includes(language)) {
                setLanguage(fwOption.languages[0] as Language);
              }
            }}
            className="rounded-md border border-slate-600 bg-slate-800 px-2.5 py-1.5 text-xs text-slate-200 outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/30"
          >
            {frameworks.map((fw) => (
              <option key={fw.id} value={fw.id}>
                {fw.label}
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-slate-400">Dil</label>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value as Language)}
            className="rounded-md border border-slate-600 bg-slate-800 px-2.5 py-1.5 text-xs text-slate-200 outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/30"
          >
            {availableLanguages.map((lang) => (
              <option key={lang} value={lang}>
                {lang === "python" ? "Python" : "JavaScript"}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Textarea */}
      <div className="flex-1 p-3">
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder={activeTab.placeholder}
          spellCheck={false}
          className="h-full w-full resize-none rounded-lg border border-slate-700/50 bg-slate-900/50 p-3 font-mono text-sm text-slate-200 placeholder-slate-600 outline-none transition-colors focus:border-violet-500/50 focus:ring-1 focus:ring-violet-500/20"
        />
      </div>

      {/* Action Bar */}
      <div className="border-t border-slate-700/50 px-4 py-3">
        {isStreaming ? (
          <button
            onClick={onCancel}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-red-500/10 py-2.5 text-sm font-medium text-red-400 ring-1 ring-red-500/20 transition-all hover:bg-red-500/20"
          >
            <Loader2 size={16} className="animate-spin" />
            İptal Et
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={!content.trim()}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-violet-600 to-indigo-600 py-2.5 text-sm font-medium text-white shadow-lg shadow-violet-500/20 transition-all hover:from-violet-500 hover:to-indigo-500 disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none"
          >
            <Play size={16} />
            Test Üret
          </button>
        )}
      </div>
    </div>
  );
}
