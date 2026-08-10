"""
User management service (Admin only in practice, enforced at router level).
"""
from __future__ import annotations
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import Page
from app.schemas.user import UserChangePassword, UserCreate, UserUpdate
from app.services.exceptions import ConflictError, NotFoundError, ValidationError


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.role_repo = RoleRepository(db)

    async def create_user(self, data: UserCreate) -> User:
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise ConflictError(f"A user with email '{data.email}' already exists")

        role = await self.role_repo.get_by_name(data.role.value)
        if not role:
            raise NotFoundError("Role", data.role.value)

        user = await self.user_repo.create(
            {
                "full_name": data.full_name,
                "email": data.email,
                "phone": data.phone,
                "hashed_password": hash_password(data.password),
                "role_id": role.id,
            }
        )
        return await self.user_repo.get_with_role(user.id)

    async def get_user(self, user_id: uuid.UUID) -> User:
        user = await self.user_repo.get_with_role(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))
        return user

    async def list_users(self, page: int, page_size: int) -> Page[User]:
        items, total = await self.user_repo.list(page=page, page_size=page_size)
        return Page.create(items=items, total=total, page=page, page_size=page_size)

    async def update_user(self, user_id: uuid.UUID, data: UserUpdate) -> User:
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))

        update_data = data.model_dump(exclude_unset=True, exclude={"role"})
        if data.role is not None:
            role = await self.role_repo.get_by_name(data.role.value)
            if not role:
                raise NotFoundError("Role", data.role.value)
            update_data["role_id"] = role.id

        user = await self.user_repo.update(user, update_data)
        return await self.user_repo.get_with_role(user.id)

    async def delete_user(self, user_id: uuid.UUID) -> None:
        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))
        await self.user_repo.delete(user)

    async def change_password(self, user: User, data: UserChangePassword) -> None:
        if not verify_password(data.old_password, user.hashed_password):
            raise ValidationError("Old password is incorrect")
        await self.user_repo.update(user, {"hashed_password": hash_password(data.new_password)})
