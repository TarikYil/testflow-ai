import { Zap } from "lucide-react";

/** Uygulama üst barı — logo, başlık ve beta etiketi. */
export default function Header() {
  return (
    <header className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-sm">
      <div className="mx-auto flex h-14 max-w-screen-2xl items-center gap-3 px-4">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600">
            <Zap size={18} className="text-white" />
          </div>
          <h1 className="text-lg font-bold tracking-tight text-white">
            testflow<span className="text-violet-400">.ai</span>
          </h1>
        </div>
        <span className="rounded-full bg-violet-500/10 px-2.5 py-0.5 text-xs font-medium text-violet-400 ring-1 ring-violet-500/20">
          beta
        </span>
        <div className="ml-auto text-xs text-slate-500">
          LLM-powered test generator
        </div>
      </div>
    </header>
  );
}
