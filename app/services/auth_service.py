"""
Authentication service: login, token refresh, current-user resolution.
"""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_handler import InvalidTokenError, parse_token
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse
from app.services.exceptions import NotFoundError, ValidationError


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise ValidationError("Invalid email or password")
        if not user.is_active:
            raise ValidationError("User account is inactive")
        return user

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.authenticate(email, password)
        role_name = user.role.name if user.role else "driver"
        access_token = create_access_token(str(user.id), role_name)
        refresh_token = create_refresh_token(str(user.id), role_name)
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            token_data = parse_token(refresh_token, expected_type="refresh")
        except InvalidTokenError as exc:
            raise ValidationError(str(exc)) from exc

        user = await self.user_repo.get_with_role(uuid.UUID(token_data.sub))
        if not user or not user.is_active:
            raise NotFoundError("User", token_data.sub)

        role_name = user.role.name if user.role else "driver"
        access_token = create_access_token(str(user.id), role_name)
        new_refresh_token = create_refresh_token(str(user.id), role_name)
        return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)
