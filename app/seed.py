"""
Seed script: populates the database with roles, an admin/manager/driver user
set, vehicles, assignments, KM logs, expense categories/expenses, tyres,
services, and reminders so the API is immediately explorable.

Usage:
    python -m app.seed
"""
import asyncio
import uuid
from datetime import date, timedelta

from sqlalchemy import select

from app.core.constants import (
    AssignmentStatus,
    ExpenseStatus,
    ReminderStatus,
    ReminderType,
    RoleName,
    VehicleStatus,
)
from app.core.logging_config import get_logger, setup_logging
from app.core.security import hash_password
from app.database.session import AsyncSessionLocal, engine
from app.models import Base
from app.models.driver import Driver
from app.models.expense import Expense
from app.models.expense_category import ExpenseCategory
from app.models.km_log import KmLog
from app.models.reminder import Reminder
from app.models.role import Role
from app.models.service import Service
from app.models.tyre import Tyre
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.vehicle_assignment import VehicleAssignment

setup_logging(debug=True)
logger = get_logger("fleetflow.seed")

ROLES = [
    (RoleName.ADMIN.value, "Full system access"),
    (RoleName.MANAGER.value, "Manages fleet operations and approves expenses"),
    (RoleName.DRIVER.value, "Drives assigned vehicles and logs trips/expenses"),
]

EXPENSE_CATEGORIES = [
    ("Fuel", "Petrol/diesel refuelling costs"),
    ("Salik", "Dubai Salik toll gate charges"),
    ("Parking", "Parking fees"),
    ("Service", "Routine vehicle servicing (oil, filters, etc.)"),
    ("Repair", "Vehicle repairs (brakes, tyres, bodywork, etc.)"),
    ("Driver Allowance", "Daily/monthly allowances paid to drivers"),
    ("Miscellaneous", "Other fleet-related expenses"),
]


async def create_schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Schema ensured (create_all) for local/dev usage.")


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        # ---- Roles ----
        role_map: dict[str, Role] = {}
        for name, description in ROLES:
            result = await db.execute(select(Role).where(Role.name == name))
            role = result.scalar_one_or_none()
            if not role:
                role = Role(name=name, description=description)
                db.add(role)
                await db.flush()
            role_map[name] = role
        await db.commit()
        logger.info("Seeded roles: %s", list(role_map.keys()))

        # ---- Users (admin, manager, 3 drivers) ----
        async def get_or_create_user(full_name, email, phone, password, role_name) -> User:
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if user:
                return user
            user = User(
                full_name=full_name,
                email=email,
                phone=phone,
                hashed_password=hash_password(password),
                role_id=role_map[role_name].id,
            )
            db.add(user)
            await db.flush()
            return user

        admin = await get_or_create_user(
            "Ahmed Al Fleet", "admin@fleetflow.com", "+971500000001", "Admin@123", RoleName.ADMIN.value
        )
        manager = await get_or_create_user(
            "Sara Manager", "manager@fleetflow.com", "+971500000002", "Manager@123", RoleName.MANAGER.value
        )
        driver_defs = [
            ("Rahul Driver", "driver1@fleetflow.com", "+971500000011", "LIC-100234"),
            ("Imran Driver", "driver2@fleetflow.com", "+971500000012", "LIC-100235"),
            ("John Driver", "driver3@fleetflow.com", "+971500000013", "LIC-100236"),
        ]
        driver_users: list[User] = []
        for full_name, email, phone, _ in driver_defs:
            u = await get_or_create_user(full_name, email, phone, "Driver@123", RoleName.DRIVER.value)
            driver_users.append(u)
        await db.commit()
        logger.info("Seeded users: admin, manager, %d drivers", len(driver_users))

        # ---- Driver profiles ----
        drivers: list[Driver] = []
        for user, (_, _, _, license_number) in zip(driver_users, driver_defs):
            result = await db.execute(select(Driver).where(Driver.user_id == user.id))
            driver = result.scalar_one_or_none()
            if not driver:
                driver = Driver(
                    user_id=user.id,
                    license_number=license_number,
                    license_expiry=date.today() + timedelta(days=365),
                    address="Dubai, UAE",
                    emergency_contact="+971500000099",
                )
                db.add(driver)
                await db.flush()
            drivers.append(driver)
        await db.commit()
        logger.info("Seeded %d driver profiles", len(drivers))

        # ---- Vehicles ----
        vehicle_defs = [
            ("DXB-A-12345", "Toyota", "Hiace", 2022, "White", 15000.0),
            ("DXB-B-54321", "Nissan", "Urvan", 2021, "Silver", 32000.0),
            ("DXB-C-99887", "Ford", "Transit", 2023, "Blue", 5000.0),
        ]
        vehicles: list[Vehicle] = []
        for reg, make, model, year, color, odometer in vehicle_defs:
            result = await db.execute(select(Vehicle).where(Vehicle.registration_number == reg))
            vehicle = result.scalar_one_or_none()
            if not vehicle:
                vehicle = Vehicle(
                    registration_number=reg,
                    make=make,
                    model=model,
                    year=year,
                    color=color,
                    current_odometer=odometer,
                    mulkiya_number=f"MLK-{reg}",
                    mulkiya_expiry=date.today() + timedelta(days=20),
                    insurance_provider="Gulf Insurance Co.",
                    insurance_policy_number=f"POL-{reg}",
                    insurance_expiry=date.today() + timedelta(days=45),
                    status=VehicleStatus.ACTIVE,
                )
                db.add(vehicle)
                await db.flush()
            vehicles.append(vehicle)
        await db.commit()
        logger.info("Seeded %d vehicles", len(vehicles))

        # ---- Vehicle assignments (assign first two vehicles to first two drivers) ----
        for vehicle, driver in zip(vehicles[:2], drivers[:2]):
            result = await db.execute(
                select(VehicleAssignment).where(
                    VehicleAssignment.vehicle_id == vehicle.id,
                    VehicleAssignment.driver_id == driver.id,
                )
            )
            assignment = result.scalar_one_or_none()
            if not assignment:
                assignment = VehicleAssignment(
                    vehicle_id=vehicle.id,
                    driver_id=driver.id,
                    assigned_date=date.today() - timedelta(days=30),
                    status=AssignmentStatus.ACTIVE,
                    notes="Initial seed assignment",
                )
                db.add(assignment)
                driver.is_available = False
        await db.commit()
        logger.info("Seeded vehicle assignments")

        # ---- Expense categories ----
        categories: dict[str, ExpenseCategory] = {}
        for name, description in EXPENSE_CATEGORIES:
            result = await db.execute(select(ExpenseCategory).where(ExpenseCategory.name == name))
            category = result.scalar_one_or_none()
            if not category:
                category = ExpenseCategory(name=name, description=description)
                db.add(category)
                await db.flush()
            categories[name] = category
        await db.commit()
        logger.info("Seeded %d expense categories", len(categories))

        # ---- KM logs (last 5 days for the first assigned vehicle/driver) ----
        if vehicles and drivers:
            vehicle = vehicles[0]
            driver = drivers[0]
            odometer_cursor = vehicle.current_odometer - 500
            for day_offset in range(5, 0, -1):
                log_date = date.today() - timedelta(days=day_offset)
                start_odo = odometer_cursor
                end_odo = start_odo + 95.5
                result = await db.execute(
                    select(KmLog).where(KmLog.vehicle_id == vehicle.id, KmLog.log_date == log_date)
                )
                if not result.scalar_one_or_none():
                    db.add(
                        KmLog(
                            vehicle_id=vehicle.id,
                            driver_id=driver.id,
                            log_date=log_date,
                            start_odometer=start_odo,
                            end_odometer=end_odo,
                            distance_covered=round(end_odo - start_odo, 2),
                            trip_purpose="Daily delivery route",
                        )
                    )
                odometer_cursor = end_odo
            await db.commit()
            logger.info("Seeded KM logs")

        # ---- Expenses ----
        if vehicles and drivers and categories:
            sample_expenses = [
                (vehicles[0], drivers[0], categories["Fuel"], 250.0, "Full tank refuel", ExpenseStatus.APPROVED),
                (vehicles[0], drivers[0], categories["Salik"], 40.0, "Salik toll charges", ExpenseStatus.PENDING),
                (vehicles[1], drivers[1], categories["Repair"], 600.0, "Brake pad replacement", ExpenseStatus.PENDING),
                (vehicles[1], drivers[1], categories["Parking"], 30.0, "Mall parking", ExpenseStatus.REJECTED),
            ]
            for vehicle, driver, category, amount, description, status in sample_expenses:
                existing = await db.execute(
                    select(Expense).where(
                        Expense.vehicle_id == vehicle.id, Expense.description == description
                    )
                )
                if not existing.scalar_one_or_none():
                    db.add(
                        Expense(
                            vehicle_id=vehicle.id,
                            driver_id=driver.id,
                            category_id=category.id,
                            amount=amount,
                            expense_date=date.today() - timedelta(days=2),
                            description=description,
                            status=status,
                        )
                    )
            await db.commit()
            logger.info("Seeded sample expenses")

        # ---- Tyres ----
        if vehicles:
            for position in ["front-left", "front-right", "rear-left", "rear-right"]:
                existing = await db.execute(
                    select(Tyre).where(Tyre.vehicle_id == vehicles[0].id, Tyre.position == position)
                )
                if not existing.scalar_one_or_none():
                    db.add(
                        Tyre(
                            vehicle_id=vehicles[0].id,
                            brand="Bridgestone",
                            position=position,
                            installed_date=date.today() - timedelta(days=200),
                            installed_odometer=vehicles[0].current_odometer - 10000,
                            expected_life_km=50000.0,
                            cost=350.0,
                            condition="good",
                        )
                    )
            await db.commit()
            logger.info("Seeded tyres for vehicle %s", vehicles[0].registration_number)

        # ---- Services ----
        if vehicles:
            existing = await db.execute(
                select(Service).where(Service.vehicle_id == vehicles[0].id, Service.service_type == "Oil Change")
            )
            if not existing.scalar_one_or_none():
                db.add(
                    Service(
                        vehicle_id=vehicles[0].id,
                        service_type="Oil Change",
                        service_date=date.today() - timedelta(days=60),
                        odometer_reading=vehicles[0].current_odometer - 8000,
                        cost=180.0,
                        workshop_name="FleetFlow Garage",
                        next_service_due_km=vehicles[0].current_odometer + 2000,
                        next_service_due_date=date.today() + timedelta(days=90),
                        notes="Routine oil and filter change",
                    )
                )
                await db.commit()
                logger.info("Seeded service history for vehicle %s", vehicles[0].registration_number)

        # ---- Reminders ----
        if vehicles:
            for vehicle in vehicles:
                for reminder_type, due_date, title in [
                    (ReminderType.INSURANCE_EXPIRY, vehicle.insurance_expiry, "Insurance expiry approaching"),
                    (ReminderType.MULKIYA_EXPIRY, vehicle.mulkiya_expiry, "Mulkiya expiry approaching"),
                ]:
                    existing = await db.execute(
                        select(Reminder).where(
                            Reminder.vehicle_id == vehicle.id,
                            Reminder.reminder_type == reminder_type,
                        )
                    )
                    if not existing.scalar_one_or_none():
                        db.add(
                            Reminder(
                                vehicle_id=vehicle.id,
                                reminder_type=reminder_type,
                                title=title,
                                description=f"{title} for {vehicle.registration_number}",
                                due_date=due_date,
                                status=ReminderStatus.PENDING,
                            )
                        )
            await db.commit()
            logger.info("Seeded reminders")

    logger.info("=" * 60)
    logger.info("Seed complete. Demo credentials:")
    logger.info("  Admin   -> admin@fleetflow.com / Admin@123")
    logger.info("  Manager -> manager@fleetflow.com / Manager@123")
    logger.info("  Driver  -> driver1@fleetflow.com / Driver@123")
    logger.info("=" * 60)


async def main() -> None:
    await create_schema()
    await seed()


if __name__ == "__main__":
    asyncio.run(main())
