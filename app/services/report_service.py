"""
Reporting service: dashboard summary, period reports, vehicle/driver/expense-wise
breakdowns, and PDF/Excel export.
"""
import calendar
import uuid
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.constants import AssignmentStatus, ExpenseStatus, ExportFormat, ReportType, VehicleStatus
from app.models.driver import Driver
from app.models.expense import Expense
from app.models.km_log import KmLog
from app.models.report import Report
from app.models.user import User
from app.models.vehicle import Vehicle
from app.repositories.expense_repository import ExpenseRepository
from app.repositories.km_log_repository import KmLogRepository
from app.repositories.reminder_repository import ReminderRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.service_repository import ServiceRepository
from app.schemas.report import (
    DashboardSummary,
    DriverWiseReport,
    ExpenseWiseReport,
    PeriodReport,
    ReportGenerateRequest,
    VehicleWiseReport,
)
from app.utils.excel_export import export_to_excel
from app.utils.pdf_export import export_to_pdf


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.expense_repo = ExpenseRepository(db)
        self.km_log_repo = KmLogRepository(db)
        self.service_repo = ServiceRepository(db)
        self.reminder_repo = ReminderRepository(db)
        self.report_repo = ReportRepository(db)

    async def dashboard_summary(self) -> DashboardSummary:
        today = date.today()
        month_start = today.replace(day=1)

        total_vehicles = (
            await self.db.execute(select(func.count()).select_from(Vehicle))
        ).scalar_one()
        active_vehicles = (
            await self.db.execute(
                select(func.count()).select_from(Vehicle).where(Vehicle.status == VehicleStatus.ACTIVE)
            )
        ).scalar_one()
        total_drivers = (
            await self.db.execute(select(func.count()).select_from(Driver))
        ).scalar_one()
        available_drivers = (
            await self.db.execute(
                select(func.count()).select_from(Driver).where(Driver.is_available.is_(True))
            )
        ).scalar_one()

        total_expenses_this_month = await self.expense_repo.total_amount_between(month_start, today)
        pending_expense_approvals = await self.expense_repo.count_pending()
        upcoming_reminders = await self.reminder_repo.count_upcoming(
            today + timedelta(days=settings.DOCUMENT_EXPIRY_ALERT_DAYS)
        )
        total_km_this_month = await self.km_log_repo.total_distance_between(month_start, today)
        total_services_this_month = await self.service_repo.count_between(month_start, today)

        return DashboardSummary(
            total_vehicles=total_vehicles,
            active_vehicles=active_vehicles,
            total_drivers=total_drivers,
            available_drivers=available_drivers,
            total_expenses_this_month=total_expenses_this_month,
            pending_expense_approvals=pending_expense_approvals,
            upcoming_reminders=upcoming_reminders,
            total_km_this_month=total_km_this_month,
            total_services_this_month=total_services_this_month,
        )

    def _period_bounds(self, report_type: ReportType, ref_date: date | None = None) -> tuple[date, date]:
        ref_date = ref_date or date.today()
        if report_type == ReportType.DAILY:
            return ref_date, ref_date
        if report_type == ReportType.WEEKLY:
            start = ref_date - timedelta(days=ref_date.weekday())
            return start, start + timedelta(days=6)
        if report_type == ReportType.MONTHLY:
            start = ref_date.replace(day=1)
            end = ref_date.replace(day=calendar.monthrange(ref_date.year, ref_date.month)[1])
            return start, end
        return ref_date, ref_date

    async def period_report(
        self,
        report_type: ReportType,
        start: date | None = None,
        end: date | None = None,
        vehicle_id: uuid.UUID | None = None,
        driver_id: uuid.UUID | None = None,
    ) -> PeriodReport:
        if start is None or end is None:
            start, end = self._period_bounds(report_type)

        total_distance = await self.km_log_repo.total_distance_between(start, end, vehicle_id, driver_id)
        total_expenses = await self.expense_repo.total_amount_between(start, end, vehicle_id, driver_id)
        total_services = await self.service_repo.count_between(start, end, vehicle_id)
        service_cost = await self.service_repo.total_cost_between(start, end, vehicle_id)
        category_rows = await self.expense_repo.expense_by_category_between(start, end)

        return PeriodReport(
            period_start=start,
            period_end=end,
            total_distance_km=total_distance,
            total_expenses=total_expenses,
            total_services=total_services,
            service_cost=service_cost,
            expense_by_category=[
                ExpenseWiseReport(category_name=name, total_amount=float(amount), count=count)
                for name, amount, count in category_rows
            ],
        )

    async def vehicle_wise_report(self, start: date, end: date) -> list[VehicleWiseReport]:
        result = await self.db.execute(select(Vehicle))
        vehicles = result.scalars().all()
        report_rows: list[VehicleWiseReport] = []
        for vehicle in vehicles:
            distance = await self.km_log_repo.total_distance_between(start, end, vehicle_id=vehicle.id)
            expenses = await self.expense_repo.total_amount_between(start, end, vehicle_id=vehicle.id)
            services_count = await self.service_repo.count_between(start, end, vehicle_id=vehicle.id)
            service_cost = await self.service_repo.total_cost_between(start, end, vehicle_id=vehicle.id)
            report_rows.append(
                VehicleWiseReport(
                    vehicle_id=vehicle.id,
                    registration_number=vehicle.registration_number,
                    total_distance_km=distance,
                    total_expenses=expenses,
                    total_services=services_count,
                    service_cost=service_cost,
                )
            )
        return report_rows

    async def driver_wise_report(self, start: date, end: date) -> list[DriverWiseReport]:
        result = await self.db.execute(select(Driver).options(selectinload(Driver.user)))
        drivers = result.scalars().all()
        report_rows: list[DriverWiseReport] = []
        for driver in drivers:
            distance = await self.km_log_repo.total_distance_between(start, end, driver_id=driver.id)
            expenses = await self.expense_repo.total_amount_between(start, end, driver_id=driver.id)
            trips_stmt = select(func.count()).select_from(KmLog).where(
                KmLog.driver_id == driver.id, KmLog.log_date >= start, KmLog.log_date <= end
            )
            trips_count = (await self.db.execute(trips_stmt)).scalar_one()
            report_rows.append(
                DriverWiseReport(
                    driver_id=driver.id,
                    driver_name=driver.user.full_name if driver.user else "Unknown",
                    total_distance_km=distance,
                    total_expenses=expenses,
                    trips_count=trips_count,
                )
            )
        return report_rows

    async def expense_wise_report(self, start: date, end: date) -> list[ExpenseWiseReport]:
        rows = await self.expense_repo.expense_by_category_between(start, end)
        return [
            ExpenseWiseReport(category_name=name, total_amount=float(amount), count=count)
            for name, amount, count in rows
        ]

    async def generate_export(self, request: ReportGenerateRequest, generated_by: uuid.UUID) -> Report:
        start = request.period_start
        end = request.period_end
        if start is None or end is None:
            start, end = self._period_bounds(request.report_type)

        rows: list[dict] = []
        title = f"FleetFlow {request.report_type.value.replace('_', ' ').title()} Report"

        if request.report_type == ReportType.VEHICLE_WISE:
            data = await self.vehicle_wise_report(start, end)
            rows = [d.model_dump(mode="json") for d in data]
        elif request.report_type == ReportType.DRIVER_WISE:
            data = await self.driver_wise_report(start, end)
            rows = [d.model_dump(mode="json") for d in data]
        elif request.report_type == ReportType.EXPENSE_WISE:
            data = await self.expense_wise_report(start, end)
            rows = [d.model_dump(mode="json") for d in data]
        else:
            period = await self.period_report(
                request.report_type, start, end, request.vehicle_id, request.driver_id
            )
            rows = [
                {
                    "period_start": str(period.period_start),
                    "period_end": str(period.period_end),
                    "total_distance_km": period.total_distance_km,
                    "total_expenses": period.total_expenses,
                    "total_services": period.total_services,
                    "service_cost": period.service_cost,
                }
            ]

        prefix = f"{request.report_type.value}_{start}_{end}"
        if request.export_format == ExportFormat.PDF:
            file_path = export_to_pdf(title, rows, prefix, subtitle=f"Period: {start} to {end}")
        else:
            file_path = export_to_excel(request.report_type.value, rows, prefix)

        report = await self.report_repo.create(
            {
                "generated_by": generated_by,
                "report_type": request.report_type,
                "export_format": request.export_format,
                "period_start": start,
                "period_end": end,
                "file_path": file_path,
            }
        )
        return report
