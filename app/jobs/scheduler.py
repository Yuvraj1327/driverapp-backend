"""
APScheduler-based background scheduler:
- Scans vehicles for upcoming insurance/mulkiya expiry and creates reminders.
- Scans reminders due soon and creates in-app notifications for admins/managers.
Runs on an interval configured by REMINDER_CHECK_INTERVAL_HOURS.
"""
from datetime import date, datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.constants import NotificationType, ReminderStatus, ReminderType, RoleName
from app.core.logging_config import get_logger
from app.database.session import AsyncSessionLocal
from app.models.reminder import Reminder
from app.models.role import Role
from app.models.user import User
from app.models.vehicle import Vehicle
from app.repositories.notification_repository import NotificationRepository
from app.repositories.reminder_repository import ReminderRepository

logger = get_logger(__name__)

scheduler = AsyncIOScheduler()


async def _create_reminder_if_missing(
    db: AsyncSession, vehicle: Vehicle, reminder_type: ReminderType, due_date: date, title: str
) -> None:
    existing_stmt = select(Reminder).where(
        Reminder.vehicle_id == vehicle.id,
        Reminder.reminder_type == reminder_type,
        Reminder.due_date == due_date,
    )
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()
    if existing:
        return

    reminder_repo = ReminderRepository(db)
    await reminder_repo.create(
        {
            "vehicle_id": vehicle.id,
            "reminder_type": reminder_type,
            "title": title,
            "description": f"{title} for vehicle {vehicle.registration_number}",
            "due_date": due_date,
            "status": ReminderStatus.PENDING,
        }
    )
    logger.info("Created reminder '%s' for vehicle %s", title, vehicle.registration_number)


async def check_document_expiries() -> None:
    """Creates reminders for vehicles whose insurance/mulkiya expire soon."""
    async with AsyncSessionLocal() as db:
        alert_horizon = date.today() + timedelta(days=settings.DOCUMENT_EXPIRY_ALERT_DAYS)
        result = await db.execute(select(Vehicle))
        vehicles = result.scalars().all()

        for vehicle in vehicles:
            if vehicle.insurance_expiry and vehicle.insurance_expiry <= alert_horizon:
                await _create_reminder_if_missing(
                    db, vehicle, ReminderType.INSURANCE_EXPIRY, vehicle.insurance_expiry,
                    "Insurance expiry approaching",
                )
            if vehicle.mulkiya_expiry and vehicle.mulkiya_expiry <= alert_horizon:
                await _create_reminder_if_missing(
                    db, vehicle, ReminderType.MULKIYA_EXPIRY, vehicle.mulkiya_expiry,
                    "Mulkiya (registration) expiry approaching",
                )
        logger.info("Document expiry check completed for %d vehicles", len(vehicles))


async def dispatch_due_reminders() -> None:
    """Turns pending reminders due soon into notifications for admins/managers."""
    async with AsyncSessionLocal() as db:
        reminder_repo = ReminderRepository(db)
        notification_repo = NotificationRepository(db)

        horizon = date.today() + timedelta(days=settings.DOCUMENT_EXPIRY_ALERT_DAYS)
        due_reminders = await reminder_repo.list_due_before(horizon, status=ReminderStatus.PENDING)

        if not due_reminders:
            return

        result = await db.execute(
            select(User).join(Role, User.role_id == Role.id).where(
                Role.name.in_([RoleName.ADMIN.value, RoleName.MANAGER.value])
            )
        )
        recipients = result.scalars().all()

        for reminder in due_reminders:
            for recipient in recipients:
                await notification_repo.create(
                    {
                        "user_id": recipient.id,
                        "title": reminder.title,
                        "message": reminder.description or reminder.title,
                        "notification_type": NotificationType.WARNING,
                        "link": f"/reminders/{reminder.id}",
                    }
                )
            await reminder_repo.update(reminder, {"status": ReminderStatus.SENT})

        logger.info("Dispatched %d reminders as notifications", len(due_reminders))


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(
        check_document_expiries,
        "interval",
        hours=settings.REMINDER_CHECK_INTERVAL_HOURS,
        id="check_document_expiries",
        next_run_time=datetime.now(),
        replace_existing=True,
    )
    scheduler.add_job(
        dispatch_due_reminders,
        "interval",
        hours=settings.REMINDER_CHECK_INTERVAL_HOURS,
        id="dispatch_due_reminders",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("APScheduler started with a %sh interval", settings.REMINDER_CHECK_INTERVAL_HOURS)


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler shut down")
