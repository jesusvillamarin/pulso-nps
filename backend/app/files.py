from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import pandas as pd

from .config import MAX_ROWS, PREVIEW_ROWS


def _clean_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, (int, float, str, bool)):
        return value
    return str(value)


def _records(frame: pd.DataFrame, limit: int | None = None) -> list[dict[str, Any]]:
    selected = frame.head(limit) if limit else frame
    return [
        {str(key): _clean_value(value) for key, value in row.items()}
        for row in selected.to_dict(orient="records")
    ]


def inspect_file(path: Path, sheet: str | None = None, header_row: int = 1) -> dict[str, Any]:
    suffix = path.suffix.lower()
    header = max(0, header_row - 1)
    if suffix == ".csv":
        frame = pd.read_csv(path, sep=None, engine="python", encoding="utf-8-sig", header=header, nrows=MAX_ROWS + 1)
        sheets = ["CSV"]
        selected_sheet = "CSV"
    elif suffix == ".xlsx":
        book = pd.ExcelFile(path, engine="openpyxl")
        sheets = book.sheet_names
        selected_sheet = sheet if sheet in sheets else sheets[0]
        frame = pd.read_excel(path, sheet_name=selected_sheet, header=header, nrows=MAX_ROWS + 1, engine="openpyxl")
    else:
        raise ValueError("Formato no soportado. Usa CSV o XLSX.")

    if len(frame) > MAX_ROWS:
        raise ValueError(f"El prototipo admite como máximo {MAX_ROWS:,} filas.")
    frame.columns = [str(column).strip() or f"columna_{index + 1}" for index, column in enumerate(frame.columns)]
    return {
        "sheets": sheets,
        "selected_sheet": selected_sheet,
        "headers": list(frame.columns),
        "preview": _records(frame, PREVIEW_ROWS),
        "row_count": len(frame),
    }


def read_rows(path: Path, sheet: str | None, header_row: int) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    header = max(0, header_row - 1)
    if suffix == ".csv":
        frame = pd.read_csv(path, sep=None, engine="python", encoding="utf-8-sig", header=header, nrows=MAX_ROWS)
    else:
        frame = pd.read_excel(path, sheet_name=sheet, header=header, nrows=MAX_ROWS, engine="openpyxl")
    frame.columns = [str(column).strip() or f"columna_{index + 1}" for index, column in enumerate(frame.columns)]
    return _records(frame)


def normalize_score(value: Any) -> tuple[float | None, bool, str | None]:
    if value is None or value == "":
        return None, False, None
    try:
        number = float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None, False, None
    valid = number.is_integer() and 0 <= number <= 10
    if not valid:
        return number, False, None
    integer = int(number)
    segment = "Promotor" if integer >= 9 else "Pasivo" if integer >= 7 else "Detractor"
    return number, True, segment


def csv_dialect_name(path: Path) -> str:
    if path.suffix.lower() != ".csv":
        return "excel"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
    try:
        return csv.Sniffer().sniff(sample).delimiter
    except csv.Error:
        return ","
