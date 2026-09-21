export interface CategoryConfig { name: string; description: string }
export interface AreaConfig { name: string; description: string; categories: CategoryConfig[] }

export interface UploadInspection {
  id: string;
  filename: string;
  sheets: string[];
  selected_sheet: string;
  header_row: number;
  headers: string[];
  preview: Record<string, unknown>[];
  row_count: number;
}

export interface Analysis {
  id: string;
  filename: string;
  status: "queued" | "processing" | "completed" | "completed_with_errors" | "failed";
  processed: number;
  total: number;
  progress: number;
  error?: string;
  taxonomy: AreaConfig[];
}

export interface ResultRow {
  id: number;
  row_index: number;
  raw_json: Record<string, unknown>;
  score: number | null;
  score_valid: number;
  comment: string | null;
  nps_segment: string | null;
  predicted_area: string | null;
  predicted_category: string | null;
  predicted_tone: string | null;
  area: string | null;
  category: string | null;
  tone: string | null;
  area_confidence: number | null;
  category_confidence: number | null;
  tone_confidence: number | null;
  needs_review: boolean;
  corrected: boolean;
  error: string | null;
}

export interface Metrics {
  nps: number;
  valid_scores: number;
  segments: Record<string, number>;
  distributions: {
    area: Record<string, number>;
    category: Record<string, number>;
    tone: Record<string, number>;
  };
  needs_review: number;
}
