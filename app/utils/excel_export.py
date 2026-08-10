"""
Excel (.xlsx) report generation using pandas + openpyxl.
"""
import uuid
from pathlib import Path
from typing import Any

import pandas as pd

from app.core.config import settings

REPORTS_DIR = Path(settings.UPLOAD_DIR) / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def export_to_excel(sheet_name: str, rows: list[dict[str, Any]], filename_prefix: str) -> str:
    """Writes rows to a formatted .xlsx file and returns the file path."""
    df = pd.DataFrame(rows)
    file_name = f"{filename_prefix}_{uuid.uuid4().hex[:8]}.xlsx"
    file_path = REPORTS_DIR / file_name

    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name[:31] or "Report")
        worksheet = writer.sheets[sheet_name[:31] or "Report"]
        for idx, column in enumerate(df.columns, start=1):
            max_len = max(
                [len(str(column))] + [len(str(v)) for v in df[column].astype(str).tolist()]
            )
            worksheet.column_dimensions[worksheet.cell(row=1, column=idx).column_letter].width = min(
                max_len + 4, 50
            )

    return str(file_path)
