"""
Shared enums / constants for FleetFlow.
"""
import enum


class RoleName(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    DRIVER = "driver"


class ExpenseStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AssignmentStatus(str, enum.Enum):
    ACTIVE = "active"
    UNASSIGNED = "unassigned"


class ReminderType(str, enum.Enum):
    INSURANCE_EXPIRY = "insurance_expiry"
    MULKIYA_EXPIRY = "mulkiya_expiry"
    SERVICE_DUE = "service_due"
    TYRE_CHANGE = "tyre_change"
    CUSTOM = "custom"


class ReminderStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    READ = "read"
    DISMISSED = "dismissed"


class NotificationType(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ALERT = "alert"
    APPROVAL = "approval"


class VehicleStatus(str, enum.Enum):
    ACTIVE = "active"
    IN_SERVICE = "in_service"
    INACTIVE = "inactive"
    RETIRED = "retired"


class ReportType(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    VEHICLE_WISE = "vehicle_wise"
    DRIVER_WISE = "driver_wise"
    EXPENSE_WISE = "expense_wise"


class ExportFormat(str, enum.Enum):
    PDF = "pdf"
    EXCEL = "excel"
