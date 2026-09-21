import type { Analysis, AreaConfig, Metrics, ResultRow, UploadInspection } from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, init);
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "No fue posible completar la solicitud." }));
    throw new Error(payload.detail ?? "No fue posible completar la solicitud.");
  }
  return response.json() as Promise<T>;
}

export const api = {
  getTaxonomy: async () => (await request<{ areas: AreaConfig[] }>("/v1/taxonomies/default")).areas,
  useExample: () => request<UploadInspection>("/v1/uploads/example", { method: "POST" }),
  upload: (file: File) => {
    const body = new FormData();
    body.append("file", file);
    return request<UploadInspection>("/v1/uploads", { method: "POST", body });
  },
  inspect: (id: string, sheet: string, headerRow: number) => request<UploadInspection>(`/v1/uploads/${id}/inspect`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sheet, header_row: headerRow }),
  }),
  createAnalysis: (payload: { upload_id: string; score_column: string; comment_column: string; taxonomy: AreaConfig[] }) =>
    request<{ id: string; status: string; total: number }>("/v1/analyses", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  getAnalysis: (id: string) => request<Analysis>(`/v1/analyses/${id}`),
  getMetrics: (id: string) => request<Metrics>(`/v1/analyses/${id}/metrics`),
  getRows: (id: string, query = "") => request<{ items: ResultRow[]; total: number }>(`/v1/analyses/${id}/rows?${query}`),
  correctRow: (id: string, rowIndex: number, payload: { area: string; category: string; tone: string }) =>
    request<{ ok: boolean }>(`/v1/analyses/${id}/rows/${rowIndex}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
};
