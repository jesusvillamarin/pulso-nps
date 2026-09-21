from __future__ import annotations

import io
import json
import shutil
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Literal

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .classifier import classify_batch
from .config import BATCH_SIZE, EXAMPLE_PATH, MAX_FILE_BYTES, UPLOAD_DIR
from .database import connect, decode_json_fields, init_db, now_iso, row_to_dict
from .files import inspect_file, normalize_score, read_rows
from .taxonomy import DEFAULT_TAXONOMY


app = FastAPI(title="Pulso API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in __import__("os").getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InspectRequest(BaseModel):
    sheet: str | None = None
    header_row: int = Field(default=1, ge=1, le=100)


class AnalysisRequest(BaseModel):
    upload_id: str
    score_column: str
    comment_column: str
    taxonomy: list[dict[str, Any]]


class CorrectionRequest(BaseModel):
    area: str
    category: str
    tone: str


@app.on_event("startup")
def startup() -> None:
    init_db()
    if not EXAMPLE_PATH.exists():
        EXAMPLE_PATH.write_text(
            "puntaje_nps,comentario,fecha\n10,Excelente servicio,2026-08-01\n2,Me cobraron dos veces,2026-08-02\n",
            encoding="utf-8",
        )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/taxonomies/default")
def default_taxonomy() -> dict[str, Any]:
    return {"areas": DEFAULT_TAXONOMY}


def _persist_upload(source: Path, filename: str) -> dict[str, Any]:
    upload_id = uuid.uuid4().hex
    suffix = source.suffix.lower()
    target = UPLOAD_DIR / f"{upload_id}{suffix}"
    if source.resolve() != target.resolve():
        shutil.copyfile(source, target)
    try:
        inspection = inspect_file(target)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    with connect() as db:
        db.execute(
            """INSERT INTO uploads
            (id, filename, path, file_type, sheets_json, selected_sheet, header_row, headers_json, preview_json, row_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)""",
            (
                upload_id, filename, str(target), suffix.removeprefix("."), json.dumps(inspection["sheets"]),
                inspection["selected_sheet"], json.dumps(inspection["headers"]),
                json.dumps(inspection["preview"], ensure_ascii=False), inspection["row_count"], now_iso(),
            ),
        )
    return {"id": upload_id, "filename": filename, **inspection, "header_row": 1}


@app.post("/v1/uploads")
async def upload(file: UploadFile = File(...)) -> dict[str, Any]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".csv", ".xlsx"}:
        raise HTTPException(400, "Formato no soportado. Usa CSV o XLSX.")
    upload_id = uuid.uuid4().hex
    temp = UPLOAD_DIR / f"temp-{upload_id}{suffix}"
    size = 0
    with temp.open("wb") as handle:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_FILE_BYTES:
                temp.unlink(missing_ok=True)
                raise HTTPException(413, "El archivo supera el límite de 25 MB.")
            handle.write(chunk)
    try:
        return _persist_upload(temp, file.filename or f"archivo{suffix}")
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    finally:
        temp.unlink(missing_ok=True)


@app.post("/v1/uploads/example")
def upload_example() -> dict[str, Any]:
    return _persist_upload(EXAMPLE_PATH, "nps_ejemplo.csv")


@app.post("/v1/uploads/{upload_id}/inspect")
def reinspect(upload_id: str, request: InspectRequest) -> dict[str, Any]:
    with connect() as db:
        item = row_to_dict(db.execute("SELECT * FROM uploads WHERE id = ?", (upload_id,)).fetchone())
    if not item:
        raise HTTPException(404, "Carga no encontrada.")
    try:
        inspection = inspect_file(Path(item["path"]), request.sheet, request.header_row)
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    with connect() as db:
        db.execute(
            """UPDATE uploads SET sheets_json=?, selected_sheet=?, header_row=?, headers_json=?, preview_json=?, row_count=?
            WHERE id=?""",
            (
                json.dumps(inspection["sheets"]), inspection["selected_sheet"], request.header_row,
                json.dumps(inspection["headers"]), json.dumps(inspection["preview"], ensure_ascii=False),
                inspection["row_count"], upload_id,
            ),
        )
    return {"id": upload_id, "filename": item["filename"], **inspection, "header_row": request.header_row}


@app.post("/v1/analyses", status_code=202)
def create_analysis(request: AnalysisRequest) -> dict[str, Any]:
    with connect() as db:
        upload_item = row_to_dict(db.execute("SELECT * FROM uploads WHERE id = ?", (request.upload_id,)).fetchone())
    if not upload_item:
        raise HTTPException(404, "Carga no encontrada.")
    headers = json.loads(upload_item["headers_json"])
    if request.score_column not in headers or request.comment_column not in headers:
        raise HTTPException(400, "Las columnas seleccionadas no existen.")
    if request.score_column == request.comment_column:
        raise HTTPException(400, "Selecciona columnas diferentes para puntaje y comentario.")
    if not request.taxonomy or any(not area.get("categories") for area in request.taxonomy):
        raise HTTPException(400, "Cada área debe contener al menos una categoría.")

    rows = read_rows(Path(upload_item["path"]), upload_item["selected_sheet"], upload_item["header_row"])
    analysis_id = uuid.uuid4().hex
    timestamp = now_iso()
    with connect() as db:
        db.execute(
            """INSERT INTO analyses
            (id, upload_id, status, score_column, comment_column, taxonomy_json, processed, total, created_at, updated_at)
            VALUES (?, ?, 'queued', ?, ?, ?, 0, ?, ?, ?)""",
            (analysis_id, request.upload_id, request.score_column, request.comment_column, json.dumps(request.taxonomy, ensure_ascii=False), len(rows), timestamp, timestamp),
        )
        for index, raw in enumerate(rows, start=1):
            score, valid, segment = normalize_score(raw.get(request.score_column))
            comment_value = raw.get(request.comment_column)
            comment = str(comment_value).strip() if comment_value is not None else ""
            db.execute(
                """INSERT INTO result_rows
                (analysis_id, row_index, raw_json, score, score_valid, comment, nps_segment, needs_review, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    analysis_id, index, json.dumps(raw, ensure_ascii=False), score, int(valid), comment or None,
                    segment, int(bool(comment) is False), None if comment else "Comentario vacío",
                ),
            )
    threading.Thread(target=_process_analysis, args=(analysis_id,), daemon=True).start()
    return {"id": analysis_id, "status": "queued", "total": len(rows)}


def _process_analysis(analysis_id: str) -> None:
    try:
        with connect() as db:
            analysis = row_to_dict(db.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,)).fetchone())
            db.execute("UPDATE analyses SET status='processing', updated_at=? WHERE id=?", (now_iso(), analysis_id))
            pending = [dict(row) for row in db.execute(
                "SELECT row_index, comment FROM result_rows WHERE analysis_id=? AND comment IS NOT NULL ORDER BY row_index",
                (analysis_id,),
            ).fetchall()]
        taxonomy = json.loads(analysis["taxonomy_json"])
        processed = 0
        had_errors = False
        for offset in range(0, len(pending), BATCH_SIZE):
            batch = pending[offset : offset + BATCH_SIZE]
            try:
                last_error: Exception | None = None
                results: list[dict[str, Any]] = []
                for attempt in range(3):
                    try:
                        results = classify_batch(batch, taxonomy)
                        last_error = None
                        break
                    except Exception as error:
                        last_error = error
                        if attempt < 2:
                            time.sleep(2 ** attempt)
                if last_error is not None:
                    raise last_error
                with connect() as db:
                    for result in results:
                        db.execute(
                            """UPDATE result_rows SET
                            predicted_area=?, predicted_category=?, predicted_tone=?, area=?, category=?, tone=?,
                            area_confidence=?, category_confidence=?, tone_confidence=?, area_probabilities=?,
                            category_probabilities=?, tone_probabilities=?, model=?, needs_review=? WHERE analysis_id=? AND row_index=?""",
                            (
                                result["area"], result["category"], result["tone"], result["area"], result["category"], result["tone"],
                                result["area_confidence"], result["category_confidence"], result["tone_confidence"],
                                json.dumps(result["area_probabilities"]), json.dumps(result["category_probabilities"]),
                                json.dumps(result["tone_probabilities"]), result["model"], int(result["needs_review"]),
                                analysis_id, result["row_index"],
                            ),
                        )
            except Exception as error:  # preserve partial progress for a prototype job
                had_errors = True
                with connect() as db:
                    for item in batch:
                        db.execute(
                            "UPDATE result_rows SET error=?, needs_review=1 WHERE analysis_id=? AND row_index=?",
                            (str(error)[:500], analysis_id, item["row_index"]),
                        )
            processed += len(batch)
            with connect() as db:
                db.execute("UPDATE analyses SET processed=?, updated_at=? WHERE id=?", (processed, now_iso(), analysis_id))
        with connect() as db:
            status = "completed_with_errors" if had_errors else "completed"
            db.execute("UPDATE analyses SET status=?, processed=total, updated_at=? WHERE id=?", (status, now_iso(), analysis_id))
    except Exception as error:
        with connect() as db:
            db.execute("UPDATE analyses SET status='failed', error=?, updated_at=? WHERE id=?", (str(error)[:1000], now_iso(), analysis_id))


@app.get("/v1/analyses/{analysis_id}")
def get_analysis(analysis_id: str) -> dict[str, Any]:
    with connect() as db:
        analysis = row_to_dict(db.execute(
            """SELECT a.*, u.filename FROM analyses a JOIN uploads u ON u.id=a.upload_id WHERE a.id=?""", (analysis_id,)
        ).fetchone())
    if not analysis:
        raise HTTPException(404, "Análisis no encontrado.")
    analysis["progress"] = round((analysis["processed"] / analysis["total"] * 100) if analysis["total"] else 100, 1)
    analysis["taxonomy"] = json.loads(analysis.pop("taxonomy_json"))
    return analysis


@app.get("/v1/analyses/{analysis_id}/rows")
def get_rows(
    analysis_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = "",
    area: str = "",
    tone: str = "",
    needs_review: bool | None = None,
) -> dict[str, Any]:
    clauses = ["analysis_id = ?"]
    params: list[Any] = [analysis_id]
    if search:
        clauses.append("comment LIKE ?")
        params.append(f"%{search}%")
    if area:
        clauses.append("area = ?")
        params.append(area)
    if tone:
        clauses.append("tone = ?")
        params.append(tone)
    if needs_review is not None:
        clauses.append("needs_review = ?")
        params.append(int(needs_review))
    where = " AND ".join(clauses)
    with connect() as db:
        total = db.execute(f"SELECT COUNT(*) FROM result_rows WHERE {where}", params).fetchone()[0]
        records = [dict(row) for row in db.execute(
            f"SELECT * FROM result_rows WHERE {where} ORDER BY row_index LIMIT ? OFFSET ?",
            [*params, page_size, (page - 1) * page_size],
        ).fetchall()]
    for record in records:
        decode_json_fields(record, ["raw_json", "area_probabilities", "category_probabilities", "tone_probabilities"])
        record["needs_review"] = bool(record["needs_review"])
        record["corrected"] = bool(record["corrected"])
    return {"items": records, "total": total, "page": page, "page_size": page_size}


@app.patch("/v1/analyses/{analysis_id}/rows/{row_index}")
def correct_row(analysis_id: str, row_index: int, request: CorrectionRequest) -> dict[str, Any]:
    with connect() as db:
        analysis = row_to_dict(db.execute("SELECT taxonomy_json FROM analyses WHERE id=?", (analysis_id,)).fetchone())
        if not analysis:
            raise HTTPException(404, "Análisis no encontrado.")
        taxonomy = json.loads(analysis["taxonomy_json"])
        area = next((item for item in taxonomy if item["name"] == request.area), None)
        if not area or request.category not in {item["name"] for item in area["categories"]}:
            raise HTTPException(400, "Área o categoría inválida.")
        cursor = db.execute(
            """UPDATE result_rows SET area=?, category=?, tone=?, corrected=1, needs_review=0
            WHERE analysis_id=? AND row_index=?""",
            (request.area, request.category, request.tone, analysis_id, row_index),
        )
        if cursor.rowcount == 0:
            raise HTTPException(404, "Fila no encontrada.")
    return {"ok": True}


@app.get("/v1/analyses/{analysis_id}/metrics")
def metrics(analysis_id: str) -> dict[str, Any]:
    with connect() as db:
        exists = db.execute("SELECT 1 FROM analyses WHERE id=?", (analysis_id,)).fetchone()
        if not exists:
            raise HTTPException(404, "Análisis no encontrado.")
        valid = db.execute("SELECT COUNT(*) FROM result_rows WHERE analysis_id=? AND score_valid=1", (analysis_id,)).fetchone()[0]
        segments = {row[0]: row[1] for row in db.execute(
            "SELECT nps_segment, COUNT(*) FROM result_rows WHERE analysis_id=? AND score_valid=1 GROUP BY nps_segment", (analysis_id,)
        ).fetchall()}
        distributions: dict[str, dict[str, int]] = {}
        for field in ("area", "category", "tone"):
            distributions[field] = {row[0]: row[1] for row in db.execute(
                f"SELECT {field}, COUNT(*) FROM result_rows WHERE analysis_id=? AND {field} IS NOT NULL GROUP BY {field} ORDER BY COUNT(*) DESC",
                (analysis_id,),
            ).fetchall()}
        review = db.execute("SELECT COUNT(*) FROM result_rows WHERE analysis_id=? AND needs_review=1", (analysis_id,)).fetchone()[0]
    promoters = segments.get("Promotor", 0)
    detractors = segments.get("Detractor", 0)
    nps = round(((promoters - detractors) / valid) * 100) if valid else 0
    return {"nps": nps, "valid_scores": valid, "segments": segments, "distributions": distributions, "needs_review": review}


@app.get("/v1/analyses/{analysis_id}/exports")
def export_analysis(analysis_id: str, format: Literal["csv", "xlsx"] = "csv") -> StreamingResponse:
    with connect() as db:
        analysis = row_to_dict(db.execute("SELECT id FROM analyses WHERE id=?", (analysis_id,)).fetchone())
        if not analysis:
            raise HTTPException(404, "Análisis no encontrado.")
        rows = [dict(row) for row in db.execute("SELECT * FROM result_rows WHERE analysis_id=? ORDER BY row_index", (analysis_id,)).fetchall()]
    output_rows = []
    for row in rows:
        raw = json.loads(row["raw_json"])
        confidence_values = [value for value in (row["area_confidence"], row["category_confidence"], row["tone_confidence"]) if value is not None]
        output_rows.append({
            **raw,
            "segmento_nps": row["nps_segment"], "area": row["area"], "categoria": row["category"], "tono": row["tone"],
            "confianza_area": row["area_confidence"], "confianza_categoria": row["category_confidence"],
            "confianza_tono": row["tone_confidence"], "confianza_minima": min(confidence_values) if confidence_values else None,
            "requiere_revision": bool(row["needs_review"]), "corregido": bool(row["corrected"]), "error": row["error"],
        })
    frame = pd.DataFrame(output_rows)
    if format == "csv":
        payload = frame.to_csv(index=False).encode("utf-8-sig")
        media_type, filename = "text/csv; charset=utf-8", "pulso_resultados.csv"
    else:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            frame.to_excel(writer, index=False, sheet_name="Resultados")
        payload = buffer.getvalue()
        media_type, filename = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "pulso_resultados.xlsx"
    return StreamingResponse(io.BytesIO(payload), media_type=media_type, headers={"Content-Disposition": f'attachment; filename="{filename}"'})
