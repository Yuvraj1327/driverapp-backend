"""
PDF report generation using ReportLab.
"""
import uuid
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.config import settings

REPORTS_DIR = Path(settings.UPLOAD_DIR) / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def export_to_pdf(
    title: str, rows: list[dict[str, Any]], filename_prefix: str, subtitle: str | None = None
) -> str:
    """Renders rows as a table in a PDF document and returns the file path."""
    file_name = f"{filename_prefix}_{uuid.uuid4().hex[:8]}.pdf"
    file_path = REPORTS_DIR / file_name

    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=landscape(A4),
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
    )
    styles = getSampleStyleSheet()
    elements = [Paragraph(title, styles["Title"])]
    if subtitle:
        elements.append(Paragraph(subtitle, styles["Normal"]))
    elements.append(Spacer(1, 0.5 * cm))

    if rows:
        headers = list(rows[0].keys())
        data = [headers] + [[str(row.get(h, "")) for h in headers] for row in rows]
        table = Table(data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        elements.append(table)
    else:
        elements.append(Paragraph("No data available for the selected period.", styles["Normal"]))

    doc.build(elements)
    return str(file_path)
