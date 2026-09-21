"use client";

import { Button } from "@heroui/react";
import { AlertTriangle, ChevronLeft, ChevronRight, Download, FileSpreadsheet, Search, X } from "lucide-react";
import { useDeferredValue, useEffect, useMemo, useState } from "react";
import { API_URL, api } from "@/lib/api";
import type { Analysis, Metrics, ResultRow } from "@/lib/types";
import { AppSelect } from "./app-select";

const TONES = ["Positivo", "Feliz", "Neutral", "Confundido", "Decepcionado", "Frustrado", "Agresivo"];

function percentage(value: number, total: number) { return total ? Math.round((value / total) * 100) : 0; }
function toneClass(tone: string | null) {
  const key = (tone ?? "neutral").toLowerCase();
  if (key === "positivo") return "tone-positive";
  if (key === "feliz") return "tone-happy";
  if (key === "confundido") return "tone-confused";
  if (key === "agresivo") return "tone-aggressive";
  if (key === "frustrado") return "tone-frustrated";
  if (key === "decepcionado") return "tone-disappointed";
  return "tone-neutral";
}

function Breakdown({ title, values }: { title: string; values: Record<string, number> }) {
  const max = Math.max(1, ...Object.values(values));
  return (
    <section className="breakdown">
      <h3>{title}</h3>
      {Object.entries(values).slice(0, 6).map(([label, count]) => (
        <div className="breakdown-row" key={label}>
          <span>{label}</span><i><b style={{ width: `${(count / max) * 100}%` }} /></i><strong>{count}</strong>
        </div>
      ))}
    </section>
  );
}

function RowEditor({ analysis, row, onClose, onSaved }: { analysis: Analysis; row: ResultRow; onClose: () => void; onSaved: () => void }) {
  const [area, setArea] = useState(row.area ?? analysis.taxonomy[0]?.name ?? "");
  const categories = useMemo(
    () => analysis.taxonomy.find((item) => item.name === area)?.categories ?? [],
    [analysis.taxonomy, area],
  );
  const [category, setCategory] = useState(row.category ?? categories[0]?.name ?? "");
  const [tone, setTone] = useState(row.tone ?? "Neutral");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const save = async () => {
    setSaving(true); setError("");
    try { await api.correctRow(analysis.id, row.row_index, { area, category, tone }); onSaved(); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "No fue posible guardar."); setSaving(false); }
  };

  return (
    <aside className="side-panel" aria-label="Corregir clasificación">
      <div className="panel-header"><div><h2>Revisar comentario</h2><p>La predicción original se conserva para auditoría.</p></div><button className="icon-button" onClick={onClose} aria-label="Cerrar"><X size={19} /></button></div>
      <div className="review-comment"><span>Puntaje {row.score ?? "—"}</span><p>{row.comment || "Sin comentario"}</p></div>
      <div className="field"><AppSelect label="Área" value={area} options={analysis.taxonomy.map((item) => item.name)} onChange={(nextArea) => { setArea(nextArea); setCategory(analysis.taxonomy.find((item) => item.name === nextArea)?.categories[0]?.name ?? ""); }} /></div>
      <div className="field"><AppSelect label="Categoría" value={category} options={categories.map((item) => item.name)} onChange={setCategory} /></div>
      <div className="field"><AppSelect label="Tono" value={tone} options={TONES} onChange={setTone} /></div>
      {error ? <div className="panel-error">{error}</div> : null}
      <div className="panel-actions"><Button variant="secondary" onPress={onClose}>Cancelar</Button><Button className="flex-1" isPending={saving} onPress={() => void save()}>Guardar corrección</Button></div>
    </aside>
  );
}

export function Dashboard({ analysis, metrics, onNew, onRefresh }: { analysis: Analysis; metrics: Metrics; onNew: () => void; onRefresh: () => Promise<void> }) {
  const [rows, setRows] = useState<ResultRow[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const deferredSearch = useDeferredValue(search);
  const [area, setArea] = useState("");
  const [tone, setTone] = useState("");
  const [reviewOnly, setReviewOnly] = useState(false);
  const [selectedRow, setSelectedRow] = useState<ResultRow | null>(null);
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    const params = new URLSearchParams({ page: String(page), page_size: "20" });
    if (deferredSearch) params.set("search", deferredSearch);
    if (area) params.set("area", area);
    if (tone) params.set("tone", tone);
    if (reviewOnly) params.set("needs_review", "true");
    void api.getRows(analysis.id, params.toString()).then((payload) => { setRows(payload.items); setTotal(payload.total); });
  }, [analysis.id, page, deferredSearch, area, tone, reviewOnly, refresh]);

  const segments = metrics.segments;
  const valid = metrics.valid_scores;
  const promoter = percentage(segments.Promotor ?? 0, valid);
  const passive = percentage(segments.Pasivo ?? 0, valid);
  const detractor = percentage(segments.Detractor ?? 0, valid);
  const pages = Math.max(1, Math.ceil(total / 20));
  const areas = useMemo(() => analysis.taxonomy.map((item) => item.name), [analysis.taxonomy]);

  return (
    <>
      <div className="analysis-strip">
        <FileSpreadsheet size={21} />
        <div className="analysis-strip-copy"><strong>{analysis.filename}</strong><span>{analysis.total.toLocaleString("es")} registros · análisis completado</span></div>
        <Button variant="secondary" size="sm" onPress={() => window.open(`${API_URL}/v1/analyses/${analysis.id}/exports?format=xlsx`, "_blank")}><Download size={15} /> Exportar XLSX</Button>
        <Button variant="ghost" size="sm" onPress={() => window.open(`${API_URL}/v1/analyses/${analysis.id}/exports?format=csv`, "_blank")}>CSV</Button>
      </div>

      <div className="metric-grid">
        <div className="metric"><span className="metric-label">NPS general</span><div className="metric-value">{metrics.nps}</div><small className="metric-foot">Escala de −100 a 100</small></div>
        <div className="metric"><span className="metric-label">Promotores</span><div className="metric-value" style={{ color: "#15955d" }}>{promoter}%</div><small className="metric-foot">{segments.Promotor ?? 0} respuestas</small></div>
        <div className="metric"><span className="metric-label">Pasivos</span><div className="metric-value" style={{ color: "#d98c08" }}>{passive}%</div><small className="metric-foot">{segments.Pasivo ?? 0} respuestas</small></div>
        <div className="metric"><span className="metric-label">Detractores</span><div className="metric-value" style={{ color: "#dd3e4f" }}>{detractor}%</div><small className="metric-foot">{segments.Detractor ?? 0} respuestas</small></div>
      </div>

      <section className="distribution">
        <h2 className="section-title">Distribución de puntuaciones NPS</h2>
        <div className="distribution-bar">
          <span className="segment-detractor" style={{ width: `${detractor}%` }}>{detractor ? `${detractor}%` : ""}</span>
          <span className="segment-passive" style={{ width: `${passive}%` }}>{passive ? `${passive}%` : ""}</span>
          <span className="segment-promoter" style={{ width: `${promoter}%` }}>{promoter ? `${promoter}%` : ""}</span>
        </div>
        <div className="legend"><span><i className="segment-detractor" />Detractores (0–6)</span><span><i className="segment-passive" />Pasivos (7–8)</span><span><i className="segment-promoter" />Promotores (9–10)</span></div>
      </section>

      <div className="toolbar">
        <div className="search-wrap"><Search size={16} /><input className="search-input" placeholder="Buscar en comentarios…" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} /></div>
        <AppSelect className="filter-select-control" label="Filtrar por área" hideLabel emptyOptionLabel="Todas las áreas" value={area} options={areas} onChange={(nextArea) => { setArea(nextArea); setPage(1); }} />
        <AppSelect className="filter-select-control" label="Filtrar por tono" hideLabel emptyOptionLabel="Todos los tonos" value={tone} options={TONES} onChange={(nextTone) => { setTone(nextTone); setPage(1); }} />
        <label className="review-check"><input type="checkbox" checked={reviewOnly} onChange={(event) => { setReviewOnly(event.target.checked); setPage(1); }} /> Requiere revisión ({metrics.needs_review})</label>
      </div>

      <div className="table-frame">
        <table className="results-table">
          <colgroup><col style={{ width: 52 }} /><col style={{ width: 74 }} /><col /><col style={{ width: 118 }} /><col style={{ width: 126 }} /><col style={{ width: 110 }} /><col style={{ width: 110 }} /><col style={{ width: 88 }} /></colgroup>
          <thead><tr><th>#</th><th>Puntaje</th><th>Comentario</th><th>Área</th><th>Categoría</th><th>Tono</th><th>Revisión</th><th>Confianza</th></tr></thead>
          <tbody>{rows.map((row) => {
            const confidence = Math.min(...[row.area_confidence, row.category_confidence, row.tone_confidence].filter((value): value is number => value !== null));
            return <tr key={row.id} onClick={() => setSelectedRow(row)}><td>{row.row_index}</td><td><span className={`score-badge score-${(row.nps_segment ?? "pasivo").toLowerCase()}`}>{row.score ?? "—"}</span></td><td className="comment-cell" title={row.comment ?? ""}>{row.comment || row.error || "Sin comentario"}</td><td>{row.area ?? "—"}</td><td>{row.category ?? "—"}</td><td><span className={`tone-badge ${toneClass(row.tone)}`}>{row.tone ?? "—"}</span></td><td>{row.needs_review ? <span className="review-badge"><AlertTriangle size={12} /> Revisar</span> : row.corrected ? "Corregido" : "—"}</td><td className="confidence">{Number.isFinite(confidence) ? confidence.toFixed(2) : "—"}</td></tr>;
          })}</tbody>
        </table>
      </div>
      <div className="table-footer"><span>Mostrando {rows.length} de {total.toLocaleString("es")} registros</span><div className="pagination"><Button isIconOnly size="sm" variant="secondary" isDisabled={page === 1} onPress={() => setPage((current) => Math.max(1, current - 1))} aria-label="Página anterior"><ChevronLeft size={16} /></Button><span>{page} / {pages}</span><Button isIconOnly size="sm" variant="secondary" isDisabled={page >= pages} onPress={() => setPage((current) => current + 1)} aria-label="Página siguiente"><ChevronRight size={16} /></Button></div></div>

      <div className="insight-grid"><Breakdown title="Comentarios por área" values={metrics.distributions.area} /><Breakdown title="Comentarios por tono" values={metrics.distributions.tone} /></div>
      <div className="new-analysis-bottom"><Button variant="secondary" onPress={onNew}>Crear otro análisis</Button></div>
      {selectedRow ? <RowEditor analysis={analysis} row={selectedRow} onClose={() => setSelectedRow(null)} onSaved={() => { setSelectedRow(null); setRefresh((value) => value + 1); void onRefresh(); }} /> : null}
    </>
  );
}
