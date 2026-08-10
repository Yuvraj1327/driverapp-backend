"""
Import every model here so that Base.metadata is fully populated
for Alembic autogenerate and for create_all in dev/testing.
"""
from app.database.base import Base  # noqa: F401
from app.models.role import Role  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.driver import Driver  # noqa: F401
from app.models.vehicle import Vehicle  # noqa: F401
from app.models.vehicle_assignment import VehicleAssignment  # noqa: F401
from app.models.km_log import KmLog  # noqa: F401
from app.models.expense_category import ExpenseCategory  # noqa: F401
from app.models.expense import Expense  # noqa: F401
from app.models.expense_approval import ExpenseApproval  # noqa: F401
from app.models.tyre import Tyre  # noqa: F401
from app.models.service import Service  # noqa: F401
from app.models.reminder import Reminder  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.report import Report  # noqa: F401
from app.models.revoked_token import RevokedToken  # noqa: F401

__all__ = [
    "Base",
    "Role",
    "User",
    "Driver",
    "Vehicle",
    "VehicleAssignment",
    "KmLog",
    "ExpenseCategory",
    "Expense",
    "ExpenseApproval",
    "Tyre",
    "Service",
    "Reminder",
    "Notification",
    "Report",
    "RevokedToken",
]
