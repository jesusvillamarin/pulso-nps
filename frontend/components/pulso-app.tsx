"use client";

import { Button } from "@heroui/react";
import { FileSpreadsheet, Plus } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Analysis, AreaConfig, Metrics } from "@/lib/types";
import { AppShell } from "./app-shell";
import { Dashboard } from "./dashboard";
import { ImportPanel } from "./import-panel";

export function PulsoApp() {
  const [panelOpen, setPanelOpen] = useState(true);
  const [taxonomy, setTaxonomy] = useState<AreaConfig[]>([]);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [error, setError] = useState("");

  useEffect(() => { void api.getTaxonomy().then(setTaxonomy).catch((caught) => setError(caught.message)); }, []);

  const loadCompleted = useCallback(async (id: string) => {
    const [nextAnalysis, nextMetrics] = await Promise.all([api.getAnalysis(id), api.getMetrics(id)]);
    setAnalysis(nextAnalysis); setMetrics(nextMetrics);
  }, []);

  useEffect(() => {
    if (!analysis || !["queued", "processing"].includes(analysis.status)) return;
    const timer = window.setInterval(() => {
      void api.getAnalysis(analysis.id).then((next) => {
        setAnalysis(next);
        if (["completed", "completed_with_errors"].includes(next.status)) void loadCompleted(next.id);
      }).catch((caught) => setError(caught.message));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [analysis, loadCompleted]);

  const start = async (payload: { upload_id: string; score_column: string; comment_column: string; taxonomy: AreaConfig[] }) => {
    const created = await api.createAnalysis(payload);
    setPanelOpen(false); setMetrics(null); setError("");
    setAnalysis({ id: created.id, filename: "Archivo cargado", status: "queued", processed: 0, total: created.total, progress: 0, taxonomy: payload.taxonomy });
  };

  const newAnalysis = () => { setPanelOpen(true); setAnalysis(null); setMetrics(null); setError(""); };
  const processing = analysis && ["queued", "processing"].includes(analysis.status);

  return (
    <AppShell hasPanel={panelOpen}>
      <header className="page-header">
        <div><h1 className="page-title">Análisis NPS</h1><p className="page-subtitle">Convierte miles de comentarios en señales claras para actuar.</p></div>
        <Button onPress={() => setPanelOpen(true)}><Plus size={17} /> Nuevo análisis</Button>
      </header>
      {error ? <div className="panel-error" role="alert">{error}</div> : null}
      {!analysis ? (
        <section className="empty-state"><div className="empty-state-inner"><div className="empty-icon"><FileSpreadsheet size={27} /></div><h2>Descubre qué sienten tus clientes</h2><p>Importa un CSV o XLSX, elige las columnas y deja que TypeSafe organice cada comentario por área, categoría y tono.</p><Button onPress={() => setPanelOpen(true)}>Empezar análisis</Button></div></section>
      ) : null}
      {processing ? (
        <section className="progress-block"><h2>Clasificando comentarios</h2><p>TypeSafe está evaluando área, categoría y tono. Puedes seguir el avance en tiempo real.</p><div className="progress-track"><div className="progress-fill" style={{ width: `${analysis.progress}%` }} /></div><div className="progress-meta"><span>{analysis.processed} de {analysis.total} filas</span><strong>{analysis.progress}%</strong></div></section>
      ) : null}
      {analysis?.status === "failed" ? <div className="panel-error">El análisis falló: {analysis.error}</div> : null}
      {analysis?.status === "completed_with_errors" ? <div className="partial-warning">Algunas filas no pudieron clasificarse después de varios reintentos. Están marcadas para revisión y el resto del análisis se conserva.</div> : null}
      {analysis && metrics ? <Dashboard analysis={analysis} metrics={metrics} onNew={newAnalysis} onRefresh={() => loadCompleted(analysis.id)} /> : null}
      {panelOpen && taxonomy.length ? <ImportPanel taxonomy={taxonomy} setTaxonomy={setTaxonomy} onClose={() => setPanelOpen(false)} onStart={start} /> : null}
    </AppShell>
  );
}
