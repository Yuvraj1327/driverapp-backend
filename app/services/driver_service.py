"""
Driver management service. Creating a driver also provisions a linked User account.
"""
from __future__ import annotations
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import RoleName
from app.core.security import hash_password
from app.models.driver import Driver
from app.repositories.driver_repository import DriverRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import Page
from app.schemas.driver import DriverCreate, DriverUpdate
from app.services.exceptions import ConflictError, NotFoundError


class DriverService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.driver_repo = DriverRepository(db)
        self.user_repo = UserRepository(db)
        self.role_repo = RoleRepository(db)

    async def create_driver(self, data: DriverCreate) -> Driver:
        existing_user = await self.user_repo.get_by_email(data.email)
        if existing_user:
            raise ConflictError(f"A user with email '{data.email}' already exists")

        role = await self.role_repo.get_by_name(RoleName.DRIVER.value)
        if not role:
            raise NotFoundError("Role", RoleName.DRIVER.value)

        user = await self.user_repo.create(
            {
                "full_name": data.full_name,
                "email": data.email,
                "phone": data.phone,
                "hashed_password": hash_password(data.password),
                "role_id": role.id,
            }
        )

        driver = await self.driver_repo.create(
            {
                "user_id": user.id,
                "license_number": data.license_number,
                "license_expiry": data.license_expiry,
                "address": data.address,
                "emergency_contact": data.emergency_contact,
            }
        )
        return await self.driver_repo.get_with_user(driver.id)

    async def get_driver(self, driver_id: uuid.UUID) -> Driver:
        driver = await self.driver_repo.get_with_user(driver_id)
        if not driver:
            raise NotFoundError("Driver", str(driver_id))
        return driver

    async def list_drivers(self, page: int, page_size: int) -> Page[Driver]:
        items, total = await self.driver_repo.list_with_user(page=page, page_size=page_size)
        return Page.create(items=items, total=total, page=page, page_size=page_size)

    async def update_driver(self, driver_id: uuid.UUID, data: DriverUpdate) -> Driver:
        driver = await self.driver_repo.get(driver_id)
        if not driver:
            raise NotFoundError("Driver", str(driver_id))
        driver = await self.driver_repo.update(driver, data.model_dump(exclude_unset=True))
        return await self.driver_repo.get_with_user(driver.id)

    async def delete_driver(self, driver_id: uuid.UUID) -> None:
        driver = await self.driver_repo.get(driver_id)
        if not driver:
            raise NotFoundError("Driver", str(driver_id))
        await self.driver_repo.delete(driver)
