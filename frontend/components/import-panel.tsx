"use client";

import { Button } from "@heroui/react";
import { ChevronLeft, FileSpreadsheet, Upload, X } from "lucide-react";
import { useRef, useState } from "react";
import { api } from "@/lib/api";
import type { AreaConfig, UploadInspection } from "@/lib/types";
import { AppSelect } from "./app-select";
import { TaxonomyEditor } from "./taxonomy-editor";

interface ImportPanelProps {
  taxonomy: AreaConfig[];
  setTaxonomy: (value: AreaConfig[]) => void;
  onClose: () => void;
  onStart: (payload: { upload_id: string; score_column: string; comment_column: string; taxonomy: AreaConfig[] }) => Promise<void>;
}

function guessColumn(headers: string[], words: string[]): string {
  return headers.find((header) => words.some((word) => header.toLowerCase().includes(word))) ?? headers[0] ?? "";
}

export function ImportPanel({ taxonomy, setTaxonomy, onClose, onStart }: ImportPanelProps) {
  const [step, setStep] = useState(1);
  const [inspection, setInspection] = useState<UploadInspection | null>(null);
  const [scoreColumn, setScoreColumn] = useState("");
  const [commentColumn, setCommentColumn] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const acceptInspection = (next: UploadInspection) => {
    setInspection(next);
    setScoreColumn(guessColumn(next.headers, ["nps", "puntaje", "score", "puntuación"]));
    setCommentColumn(guessColumn(next.headers, ["coment", "comment", "opinion", "mensaje"]));
    setStep(2);
  };

  const run = async (action: () => Promise<UploadInspection>) => {
    setLoading(true);
    setError("");
    try { acceptInspection(await action()); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Ocurrió un error."); }
    finally { setLoading(false); }
  };

  const handleFile = (file?: File) => {
    if (file) void run(() => api.upload(file));
  };

  const refreshInspection = async () => {
    if (!inspection) return;
    setLoading(true);
    setError("");
    try {
      const next = await api.inspect(inspection.id, inspection.selected_sheet, inspection.header_row);
      acceptInspection(next);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No fue posible leer el archivo.");
    } finally { setLoading(false); }
  };

  const start = async () => {
    if (!inspection || !scoreColumn || !commentColumn) return;
    if (scoreColumn === commentColumn) {
      setError("El puntaje y el comentario deben usar columnas diferentes.");
      return;
    }
    setLoading(true);
    setError("");
    try { await onStart({ upload_id: inspection.id, score_column: scoreColumn, comment_column: commentColumn, taxonomy }); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "No fue posible iniciar el análisis."); setLoading(false); }
  };

  return (
    <aside className="side-panel" aria-label="Nuevo análisis">
      <div className="panel-header">
        <div>
          <h2>Nuevo análisis</h2>
          <p>Importa valoraciones y define cómo debe interpretarlas Pulso.</p>
        </div>
        <button className="icon-button" onClick={onClose} aria-label="Cerrar panel"><X size={19} /></button>
      </div>
      <div className="step-list" aria-label={`Paso ${step} de 3`}>
        {[1, 2, 3].map((number) => <span className={number <= step ? "active" : ""} key={number} />)}
      </div>

      {step === 1 ? (
        <>
          <div
            className="dropzone"
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => { event.preventDefault(); handleFile(event.dataTransfer.files[0]); }}
          >
            <div>
              <Upload size={34} color="#2457dd" />
              <strong>Arrastra tu archivo aquí</strong>
              <p>CSV o XLSX · máximo 25 MB y 10.000 filas</p>
              <input ref={fileRef} hidden type="file" accept=".csv,.xlsx" onChange={(event) => handleFile(event.target.files?.[0])} />
              <Button isPending={loading} onPress={() => fileRef.current?.click()}>Cargar archivo</Button>
            </div>
          </div>
          <div className="or-divider">o</div>
          <Button className="w-full" variant="secondary" isPending={loading} onPress={() => void run(api.useExample)}>
            <FileSpreadsheet size={17} /> Usar archivo de ejemplo
          </Button>
        </>
      ) : null}

      {step === 2 && inspection ? (
        <>
          <div className="analysis-strip">
            <FileSpreadsheet size={20} />
            <div className="analysis-strip-copy"><strong>{inspection.filename}</strong><span>{inspection.row_count.toLocaleString("es")} registros</span></div>
          </div>
          <section className="panel-section">
            <h3>Lectura del archivo</h3>
            <p>Selecciona la hoja y la fila que contiene los encabezados.</p>
            {inspection.sheets.length > 1 ? (
              <div className="field"><AppSelect label="Hoja" value={inspection.selected_sheet} options={inspection.sheets} onChange={(selectedSheet) => setInspection({ ...inspection, selected_sheet: selectedSheet })} /></div>
            ) : null}
            <div className="field"><label htmlFor="header-row">Fila de encabezados</label><input id="header-row" className="field-input" type="number" min={1} max={100} value={inspection.header_row} onChange={(event) => setInspection({ ...inspection, header_row: Number(event.target.value) })} /></div>
            <Button size="sm" variant="secondary" isPending={loading} onPress={() => void refreshInspection()}>Actualizar vista previa</Button>
          </section>
          <section className="panel-section">
            <h3>Vista previa</h3><p>Primeras {Math.min(20, inspection.preview.length)} filas detectadas.</p>
            <div className="preview-table-wrap"><table className="preview-table"><thead><tr><th>#</th>{inspection.headers.map((header) => <th key={header}>{header}</th>)}</tr></thead><tbody>{inspection.preview.slice(0, 20).map((row, index) => <tr key={index}><td>{index + 1}</td>{inspection.headers.map((header) => <td key={header}>{String(row[header] ?? "—")}</td>)}</tr>)}</tbody></table></div>
          </section>
          <section className="panel-section">
            <h3>Selecciona las columnas</h3><p>Indica dónde están el puntaje NPS y el comentario.</p>
            <div className="field"><AppSelect label="Columna de puntaje" value={scoreColumn} options={inspection.headers} onChange={setScoreColumn} /></div>
            <div className="field"><AppSelect label="Columna de comentario" value={commentColumn} options={inspection.headers} onChange={setCommentColumn} /></div>
          </section>
        </>
      ) : null}

      {step === 3 ? (
        <section className="panel-section">
          <h3>Áreas y categorías</h3>
          <p>TypeSafe elegirá primero el área y después una categoría dentro de ella.</p>
          <TaxonomyEditor value={taxonomy} onChange={setTaxonomy} />
        </section>
      ) : null}

      {error ? <div className="panel-error" role="alert">{error}</div> : null}
      {step > 1 ? (
        <div className="panel-actions">
          <Button variant="secondary" onPress={() => { setError(""); setStep((current) => current - 1); }}><ChevronLeft size={16} /> Atrás</Button>
          <Button className="flex-1" isPending={loading} onPress={() => step === 2 ? setStep(3) : void start()}>{step === 2 ? "Continuar" : "Analizar comentarios"}</Button>
        </div>
      ) : null}
    </aside>
  );
}
