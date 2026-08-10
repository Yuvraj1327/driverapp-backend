import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Date, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ExportFormat, ReportType
from app.database.base import Base, TimestampMixin, UUIDMixin


class Report(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "reports"

    generated_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    report_type: Mapped[ReportType] = mapped_column(Enum(ReportType, name="report_type"), nullable=False)
    export_format: Mapped[ExportFormat] = mapped_column(
        Enum(ExportFormat, name="export_format"), nullable=False
    )
    period_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    period_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)

    generator: Mapped[Optional["User"]] = relationship()

    def __repr__(self) -> str:
        return f"<Report {self.report_type} {self.export_format}>"
