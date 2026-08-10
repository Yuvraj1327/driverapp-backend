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
from app.models.service import Service
from app.models.tyre import Tyre
from app.models.user import User
from app.models.vehicle import Vehicle
from app.repositories.notification_repository import NotificationRepository
from app.repositories.reminder_repository import ReminderRepository

logger = get_logger(__name__)

scheduler = AsyncIOScheduler()

# Once a tyre has consumed this fraction of its expected life, a replacement
# reminder is raised.
TYRE_REPLACEMENT_THRESHOLD = 0.9
# Vehicles within this many km of their next scheduled service are flagged.
SERVICE_DUE_KM_BUFFER = 500.0


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


async def _create_reminder_if_no_active(
    db: AsyncSession, vehicle: Vehicle, reminder_type: ReminderType, due_date: date, title: str, description: str
) -> None:
    """Like `_create_reminder_if_missing`, but dedupes on (vehicle, type) rather
    than (vehicle, type, due_date) — used for km/usage-based reminders whose
    computed due_date can shift slightly between scheduler runs."""
    existing_stmt = select(Reminder).where(
        Reminder.vehicle_id == vehicle.id,
        Reminder.reminder_type == reminder_type,
        Reminder.status.in_([ReminderStatus.PENDING, ReminderStatus.SENT]),
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
            "description": description,
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


async def check_service_due() -> None:
    """Creates SERVICE_DUE reminders for vehicles approaching their next
    scheduled service, by date or by odometer reading."""
    async with AsyncSessionLocal() as db:
        alert_horizon = date.today() + timedelta(days=settings.DOCUMENT_EXPIRY_ALERT_DAYS)

        # Latest service record per vehicle (the one carrying the current
        # "next due" projection).
        result = await db.execute(select(Service).order_by(Service.vehicle_id, Service.service_date.desc()))
        services = result.scalars().all()
        latest_by_vehicle: dict = {}
        for service in services:
            if service.vehicle_id not in latest_by_vehicle:
                latest_by_vehicle[service.vehicle_id] = service

        vehicles_result = await db.execute(select(Vehicle))
        vehicles_by_id = {v.id: v for v in vehicles_result.scalars().all()}

        checked = 0
        for vehicle_id, service in latest_by_vehicle.items():
            vehicle = vehicles_by_id.get(vehicle_id)
            if not vehicle:
                continue

            due_by_date = service.next_service_due_date and service.next_service_due_date <= alert_horizon
            due_by_km = (
                service.next_service_due_km is not None
                and vehicle.current_odometer >= service.next_service_due_km - SERVICE_DUE_KM_BUFFER
            )
            if due_by_date or due_by_km:
                due_date = service.next_service_due_date or date.today()
                await _create_reminder_if_no_active(
                    db,
                    vehicle,
                    ReminderType.SERVICE_DUE,
                    due_date,
                    "Service due soon",
                    f"Vehicle {vehicle.registration_number} is due for {service.service_type} servicing "
                    f"(next due at {service.next_service_due_km or 'N/A'} km / {due_date}).",
                )
                checked += 1
        logger.info("Service-due check completed; %d reminder(s) evaluated as due", checked)


async def check_tyre_replacement_due() -> None:
    """Creates TYRE_CHANGE reminders once a tyre has consumed most of its
    expected life (by km driven since installation)."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Tyre).where(Tyre.removed_date.is_(None)))
        active_tyres = result.scalars().all()

        vehicles_result = await db.execute(select(Vehicle))
        vehicles_by_id = {v.id: v for v in vehicles_result.scalars().all()}

        flagged_vehicles: set = set()
        for tyre in active_tyres:
            vehicle = vehicles_by_id.get(tyre.vehicle_id)
            if not vehicle or tyre.vehicle_id in flagged_vehicles:
                continue

            used_km = vehicle.current_odometer - tyre.installed_odometer
            if tyre.expected_life_km > 0 and used_km >= tyre.expected_life_km * TYRE_REPLACEMENT_THRESHOLD:
                await _create_reminder_if_no_active(
                    db,
                    vehicle,
                    ReminderType.TYRE_CHANGE,
                    date.today(),
                    "Tyre replacement due soon",
                    f"Tyre ({tyre.brand}, {tyre.position}) on vehicle {vehicle.registration_number} has "
                    f"covered {used_km:.0f} km of its {tyre.expected_life_km:.0f} km expected life.",
                )
                flagged_vehicles.add(tyre.vehicle_id)
        logger.info("Tyre-replacement check completed; %d vehicle(s) flagged", len(flagged_vehicles))


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
        check_service_due,
        "interval",
        hours=settings.REMINDER_CHECK_INTERVAL_HOURS,
        id="check_service_due",
        next_run_time=datetime.now(),
        replace_existing=True,
    )
    scheduler.add_job(
        check_tyre_replacement_due,
        "interval",
        hours=settings.REMINDER_CHECK_INTERVAL_HOURS,
        id="check_tyre_replacement_due",
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
