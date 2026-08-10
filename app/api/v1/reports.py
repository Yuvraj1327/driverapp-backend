"""
Reporting endpoints: dashboard summary, daily/weekly/monthly, vehicle/driver/
expense-wise breakdowns, and PDF/Excel export.
"""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_any_role, require_manager
from app.core.constants import ReportType
from app.database.session import get_db
from app.models.user import User
from app.schemas.report import (
    DashboardSummary,
    DriverWiseReport,
    ExpenseWiseReport,
    PeriodReport,
    ReportGenerateRequest,
    ReportRead,
    VehicleWiseReport,
)
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/dashboard", response_model=DashboardSummary, dependencies=[Depends(require_any_role)])
async def dashboard_summary(db: AsyncSession = Depends(get_db)) -> DashboardSummary:
    service = ReportService(db)
    return await service.dashboard_summary()


@router.get("/daily", response_model=PeriodReport, dependencies=[Depends(require_any_role)])
async def daily_report(
    report_date: date | None = Query(default=None),
    vehicle_id: uuid.UUID | None = Query(default=None),
    driver_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> PeriodReport:
    service = ReportService(db)
    return await service.period_report(ReportType.DAILY, report_date, report_date, vehicle_id, driver_id)


@router.get("/weekly", response_model=PeriodReport, dependencies=[Depends(require_any_role)])
async def weekly_report(
    week_start: date | None = Query(default=None),
    week_end: date | None = Query(default=None),
    vehicle_id: uuid.UUID | None = Query(default=None),
    driver_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> PeriodReport:
    service = ReportService(db)
    return await service.period_report(ReportType.WEEKLY, week_start, week_end, vehicle_id, driver_id)


@router.get("/monthly", response_model=PeriodReport, dependencies=[Depends(require_any_role)])
async def monthly_report(
    month_start: date | None = Query(default=None),
    month_end: date | None = Query(default=None),
    vehicle_id: uuid.UUID | None = Query(default=None),
    driver_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> PeriodReport:
    service = ReportService(db)
    return await service.period_report(ReportType.MONTHLY, month_start, month_end, vehicle_id, driver_id)


@router.get(
    "/vehicle-wise", response_model=list[VehicleWiseReport], dependencies=[Depends(require_any_role)]
)
async def vehicle_wise_report(
    start_date: date, end_date: date, db: AsyncSession = Depends(get_db)
) -> list[VehicleWiseReport]:
    service = ReportService(db)
    return await service.vehicle_wise_report(start_date, end_date)


@router.get(
    "/driver-wise", response_model=list[DriverWiseReport], dependencies=[Depends(require_any_role)]
)
async def driver_wise_report(
    start_date: date, end_date: date, db: AsyncSession = Depends(get_db)
) -> list[DriverWiseReport]:
    service = ReportService(db)
    return await service.driver_wise_report(start_date, end_date)


@router.get(
    "/expense-wise", response_model=list[ExpenseWiseReport], dependencies=[Depends(require_any_role)]
)
async def expense_wise_report(
    start_date: date, end_date: date, db: AsyncSession = Depends(get_db)
) -> list[ExpenseWiseReport]:
    service = ReportService(db)
    return await service.expense_wise_report(start_date, end_date)


@router.post("/export", response_model=ReportRead, dependencies=[Depends(require_manager)])
async def generate_export(
    payload: ReportGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReportRead:
    service = ReportService(db)
    report = await service.generate_export(payload, current_user.id)
    return ReportRead.model_validate(report)


@router.get("/export/{report_id}/download", dependencies=[Depends(require_manager)])
async def download_export(report_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> FileResponse:
    from app.repositories.report_repository import ReportRepository
    from app.services.exceptions import NotFoundError

    repo = ReportRepository(db)
    report = await repo.get(report_id)
    if not report:
        raise NotFoundError("Report", str(report_id))

    media_type = "application/pdf" if report.export_format.value == "pdf" else (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    filename = report.file_path.split("/")[-1]
    return FileResponse(report.file_path, media_type=media_type, filename=filename)
