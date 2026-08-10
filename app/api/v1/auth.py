"""
Auth endpoints: login, refresh, current user info.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.schemas.user import UserWithRole
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse, summary="Login with email and password")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    service = AuthService(db)
    return await service.login(payload.email, payload.password)


@router.post("/refresh", response_model=TokenResponse, summary="Exchange a refresh token for a new pair")
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    service = AuthService(db)
    return await service.refresh(payload.refresh_token)


@router.get("/me", response_model=UserWithRole, summary="Get the current authenticated user")
async def me(current_user: User = Depends(get_current_user)) -> UserWithRole:
    return UserWithRole(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        phone=current_user.phone,
        is_active=current_user.is_active,
        role_id=current_user.role_id,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        role_name=current_user.role.name if current_user.role else None,
    )
