"""
User management endpoints (Admin only).
"""
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_admin
from app.api.v1.deps import pagination_params
from app.database.session import get_db
from app.models.user import User
from app.schemas.common import Message, Page
from app.schemas.user import UserChangePassword, UserCreate, UserRead, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> UserRead:
    service = UserService(db)
    user = await service.create_user(payload)
    return UserRead.model_validate(user)


@router.get("/", response_model=Page[UserRead], dependencies=[Depends(require_admin)])
async def list_users(
    pagination: tuple[int, int] = Depends(pagination_params), db: AsyncSession = Depends(get_db)
) -> Page[UserRead]:
    page, page_size = pagination
    service = UserService(db)
    result = await service.list_users(page, page_size)
    return Page[UserRead](
        items=[UserRead.model_validate(u) for u in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        pages=result.pages,
    )


@router.get("/{user_id}", response_model=UserRead, dependencies=[Depends(require_admin)])
async def get_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> UserRead:
    service = UserService(db)
    user = await service.get_user(user_id)
    return UserRead.model_validate(user)


@router.put("/{user_id}", response_model=UserRead, dependencies=[Depends(require_admin)])
async def update_user(user_id: uuid.UUID, payload: UserUpdate, db: AsyncSession = Depends(get_db)) -> UserRead:
    service = UserService(db)
    user = await service.update_user(user_id, payload)
    return UserRead.model_validate(user)


@router.delete("/{user_id}", response_model=Message, dependencies=[Depends(require_admin)])
async def delete_user(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Message:
    service = UserService(db)
    await service.delete_user(user_id)
    return Message(detail="User deleted successfully")


@router.post("/me/change-password", response_model=Message)
async def change_my_password(
    payload: UserChangePassword,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Message:
    service = UserService(db)
    await service.change_password(current_user, payload)
    return Message(detail="Password updated successfully")
