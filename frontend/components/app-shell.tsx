import { BarChart3, Boxes, History, Settings, Sparkles } from "lucide-react";
import type { ReactNode } from "react";

export function AppShell({ children, hasPanel }: { children: ReactNode; hasPanel: boolean }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark"><Sparkles size={18} strokeWidth={2.2} /></span>
          Pulso
        </div>
        <nav className="nav-list" aria-label="Navegación principal">
          <span className="nav-item active"><BarChart3 size={18} /> Análisis NPS</span>
          <span className="nav-item"><History size={18} /> Historial</span>
          <span className="nav-item"><Boxes size={18} /> Taxonomía</span>
          <span className="nav-item"><Settings size={18} /> Configuración</span>
        </nav>
        <div className="sidebar-note">Prototipo local<br />Clasificación con TypeSafe</div>
      </aside>
      <main className={`workspace${hasPanel ? " with-panel" : ""}`}>{children}</main>
    </div>
  );
}
