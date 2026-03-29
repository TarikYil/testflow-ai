/**
 * ZIP dışa aktarma — girdi, üretilen kod ve meta bilgisini tek dosyada indirir.
 */
import JSZip from "jszip";
import { saveAs } from "file-saver";
import type { Framework, InputMode, Language } from "../types";

/** Zip'e dahil edilecek tüm verilerin yapısı. */
interface ExportData {
  code: string;
  inputContent: string;
  mode: InputMode;
  framework: Framework;
  language: Language;
}

const MODE_LABELS: Record<InputMode, string> = {
  html: "HTML",
  json: "JSON",
  manual: "Manuel",
};

function getCodeFilename(language: Language): string {
  const ext = language === "python" ? "py" : "js";
  return `test_generated.${ext}`;
}

function getInputFilename(mode: InputMode): string {
  if (mode === "html") return "input.html";
  return "input.json";
}

/** Girdi + çıktı + meta'yı ZIP olarak oluşturup tarayıcıda indirir. */
export async function exportAsZip(data: ExportData): Promise<void> {
  const zip = new JSZip();
  const folder = zip.folder("testflow-export")!;

  folder.file(getInputFilename(data.mode), data.inputContent);

  folder.file(getCodeFilename(data.language), data.code);

  const meta = {
    framework: data.framework,
    language: data.language,
    mode: MODE_LABELS[data.mode],
    exported_at: new Date().toISOString(),
  };
  folder.file("meta.json", JSON.stringify(meta, null, 2));

  const blob = await zip.generateAsync({ type: "blob" });
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
  saveAs(blob, `testflow-${data.framework}-${data.language}-${timestamp}.zip`);
}
