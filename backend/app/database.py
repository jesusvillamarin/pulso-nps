from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from .config import DATA_DIR, DB_PATH, UPLOAD_DIR


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(DB_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS uploads (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                sheets_json TEXT NOT NULL,
                selected_sheet TEXT,
                header_row INTEGER NOT NULL DEFAULT 1,
                headers_json TEXT NOT NULL,
                preview_json TEXT NOT NULL,
                row_count INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                upload_id TEXT NOT NULL REFERENCES uploads(id) ON DELETE CASCADE,
                status TEXT NOT NULL,
                score_column TEXT NOT NULL,
                comment_column TEXT NOT NULL,
                taxonomy_json TEXT NOT NULL,
                processed INTEGER NOT NULL DEFAULT 0,
                total INTEGER NOT NULL DEFAULT 0,
                error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS result_rows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id TEXT NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
                row_index INTEGER NOT NULL,
                raw_json TEXT NOT NULL,
                score REAL,
                score_valid INTEGER NOT NULL DEFAULT 0,
                comment TEXT,
                nps_segment TEXT,
                predicted_area TEXT,
                predicted_category TEXT,
                predicted_tone TEXT,
                area TEXT,
                category TEXT,
                tone TEXT,
                area_confidence REAL,
                category_confidence REAL,
                tone_confidence REAL,
                area_probabilities TEXT,
                category_probabilities TEXT,
                tone_probabilities TEXT,
                model TEXT,
                needs_review INTEGER NOT NULL DEFAULT 0,
                corrected INTEGER NOT NULL DEFAULT 0,
                error TEXT,
                UNIQUE(analysis_id, row_index)
            );

            CREATE INDEX IF NOT EXISTS idx_rows_analysis ON result_rows(analysis_id, row_index);
            CREATE INDEX IF NOT EXISTS idx_rows_filters ON result_rows(analysis_id, area, category, tone, needs_review);
            """
        )


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def decode_json_fields(item: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    for field in fields:
        if field in item and isinstance(item[field], str):
            item[field] = json.loads(item[field])
    return item
