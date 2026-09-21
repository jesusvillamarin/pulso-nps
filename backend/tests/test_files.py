from pathlib import Path

import pandas as pd

from app.files import inspect_file, normalize_score, read_rows


def test_normalize_standard_nps_scores() -> None:
    assert normalize_score("10") == (10.0, True, "Promotor")
    assert normalize_score(8) == (8.0, True, "Pasivo")
    assert normalize_score("0") == (0.0, True, "Detractor")
    assert normalize_score(11) == (11.0, False, None)
    assert normalize_score("texto") == (None, False, None)


def test_csv_preview_detects_semicolon_and_multiline(tmp_path: Path) -> None:
    path = tmp_path / "opiniones.csv"
    path.write_text('score;comment\n10;"Excelente\nservicio"\n4;"Debe mejorar"\n', encoding="utf-8-sig")
    inspection = inspect_file(path)
    assert inspection["headers"] == ["score", "comment"]
    assert inspection["row_count"] == 2
    assert inspection["preview"][0]["comment"] == "Excelente\nservicio"


def test_xlsx_multiple_sheets_and_header_row(tmp_path: Path) -> None:
    path = tmp_path / "opiniones.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame({"nota": [10], "texto": ["Muy bien"]}).to_excel(writer, sheet_name="NPS", index=False)
        pd.DataFrame({"otro": [1]}).to_excel(writer, sheet_name="Auxiliar", index=False)
    inspection = inspect_file(path, sheet="NPS")
    assert inspection["sheets"] == ["NPS", "Auxiliar"]
    assert inspection["selected_sheet"] == "NPS"
    assert read_rows(path, "NPS", 1)[0]["texto"] == "Muy bien"
