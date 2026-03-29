/**
 * Geçmiş kenar çubuğu — önceki test üretimlerini listeler,
 * seçim ve silme işlemlerini yönetir.
 */
import { useEffect, useState, useCallback } from "react";
import { History, Trash2, ChevronDown, ChevronUp, CheckCircle2, XCircle, Clock, FileCode2 } from "lucide-react";
import { fetchHistory, deleteHistory } from "../services/api";
import type { HistoryItem } from "../types";

interface Props {
  refreshKey: number;
  onSelect: (item: HistoryItem) => void;
}

const MODE_LABELS: Record<string, string> = {
  html: "HTML",
  json: "JSON",
  manual: "Manuel",
};

function truncateInput(raw: string, max = 60): string {
  const oneLine = raw.replace(/\s+/g, " ").trim();
  return oneLine.length > max ? oneLine.slice(0, max) + "…" : oneLine;
}

/** Açılır/kapanır geçmiş paneli — son 20 kaydı gösterir. */
export default function HistorySidebar({ refreshKey, onSelect }: Props) {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [open, setOpen] = useState(true);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchHistory(20, 0);
      setItems(res.items);
      setTotal(res.total);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    try {
      await deleteHistory(id);
      setItems((prev) => prev.filter((i) => i._id !== id));
      setTotal((prev) => prev - 1);
    } catch {
      // silently fail
    }
  };

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleString("tr-TR", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="border-t border-slate-700/50">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-2.5 text-xs font-medium text-slate-400 transition-colors hover:bg-slate-800/30"
      >
        <div className="flex items-center gap-2">
          <History size={13} />
          Geçmiş
          {total > 0 && (
            <span className="rounded-full bg-slate-700/50 px-1.5 py-0.5 text-[0.6rem] text-slate-500">
              {total}
            </span>
          )}
        </div>
        {open ? <ChevronDown size={13} /> : <ChevronUp size={13} />}
      </button>

      {open && (
        <div className="max-h-[280px] overflow-y-auto px-2 pb-2">
          {loading && items.length === 0 && (
            <div className="px-2 py-3 text-center text-xs text-slate-600">Yükleniyor...</div>
          )}

          {!loading && items.length === 0 && (
            <div className="px-2 py-3 text-center text-xs text-slate-600">Henüz geçmiş yok</div>
          )}

          {items.map((item) => (
            <button
              key={item._id}
              onClick={() => onSelect(item)}
              className="group mb-1 flex w-full items-start gap-2 rounded-lg px-2.5 py-2 text-left transition-colors hover:bg-slate-800/50"
            >
              <div className="mt-0.5">
                {item.status === "success" ? (
                  <CheckCircle2 size={12} className="text-emerald-500/70" />
                ) : (
                  <XCircle size={12} className="text-red-500/70" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="truncate text-xs font-medium text-slate-300">
                    {item.framework}/{item.language}
                  </span>
                  <span className="shrink-0 rounded bg-slate-800 px-1 text-[0.6rem] text-slate-500">
                    {MODE_LABELS[item.mode] ?? item.mode}
                  </span>
                </div>
                {item.input_content && (
                  <div className="mt-0.5 flex items-center gap-1 text-[0.6rem] text-slate-500">
                    <FileCode2 size={9} className="shrink-0" />
                    <span className="truncate">{truncateInput(item.input_content)}</span>
                  </div>
                )}
                <div className="mt-0.5 flex items-center gap-1 text-[0.65rem] text-slate-600">
                  <Clock size={9} />
                  {formatDate(item.updated_at ?? item.created_at)}
                </div>
              </div>
              <button
                onClick={(e) => handleDelete(e, item._id)}
                className="mt-0.5 shrink-0 rounded p-0.5 text-slate-700 opacity-0 transition-all hover:bg-red-500/10 hover:text-red-400 group-hover:opacity-100"
              >
                <Trash2 size={12} />
              </button>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
