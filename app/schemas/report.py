import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import ExportFormat, ReportType


class ReportGenerateRequest(BaseModel):
    report_type: ReportType
    export_format: ExportFormat
    period_start: date | None = None
    period_end: date | None = None
    vehicle_id: uuid.UUID | None = None
    driver_id: uuid.UUID | None = None


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    report_type: ReportType
    export_format: ExportFormat
    period_start: date | None = None
    period_end: date | None = None
    file_path: str
    created_at: datetime


class DashboardSummary(BaseModel):
    total_vehicles: int
    active_vehicles: int
    total_drivers: int
    available_drivers: int
    total_expenses_this_month: float
    pending_expense_approvals: int
    upcoming_reminders: int
    total_km_this_month: float
    total_services_this_month: int


class VehicleWiseReport(BaseModel):
    vehicle_id: uuid.UUID
    registration_number: str
    total_distance_km: float
    total_expenses: float
    total_services: int
    service_cost: float


class DriverWiseReport(BaseModel):
    driver_id: uuid.UUID
    driver_name: str
    total_distance_km: float
    total_expenses: float
    trips_count: int


class ExpenseWiseReport(BaseModel):
    category_name: str
    total_amount: float
    count: int


class PeriodReport(BaseModel):
    period_start: date
    period_end: date
    total_distance_km: float
    total_expenses: float
    total_services: int
    service_cost: float
    expense_by_category: list[ExpenseWiseReport] = Field(default_factory=list)
