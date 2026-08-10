"""
Authentication service: signup, login, token refresh/revocation, current-user
resolution.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_handler import InvalidTokenError, parse_token
from app.core.constants import RoleName
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.user import User
from app.repositories.revoked_token_repository import RevokedTokenRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import SignupRequest, TokenResponse
from app.services.exceptions import ConflictError, NotFoundError, ValidationError


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.role_repo = RoleRepository(db)
        self.revoked_repo = RevokedTokenRepository(db)

    async def signup(self, data: SignupRequest) -> User:
        """Public self-registration. Always provisions a 'driver' role account."""
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
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
        return await self.user_repo.get_with_role(user.id)

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
        if await self.revoked_repo.is_revoked(hash_token(refresh_token)):
            raise ValidationError("This refresh token has been revoked. Please log in again.")

        try:
            token_data = parse_token(refresh_token, expected_type="refresh")
        except InvalidTokenError as exc:
            raise ValidationError(str(exc)) from exc

        user = await self.user_repo.get_with_role(uuid.UUID(token_data.sub))
        if not user or not user.is_active:
            raise NotFoundError("User", token_data.sub)

        # Rotate: the old refresh token is now spent and blacklisted.
        await self._revoke_raw_token(refresh_token)

        role_name = user.role.name if user.role else "driver"
        access_token = create_access_token(str(user.id), role_name)
        new_refresh_token = create_refresh_token(str(user.id), role_name)
        return TokenResponse(access_token=access_token, refresh_token=new_refresh_token)

    async def logout(self, refresh_token: str) -> None:
        """Blacklists the given refresh token so it can no longer be exchanged
        for new access tokens. The corresponding access token remains valid
        until its own (short) expiry, per standard stateless-JWT practice."""
        try:
            parse_token(refresh_token, expected_type="refresh")
        except InvalidTokenError as exc:
            raise ValidationError(str(exc)) from exc
        await self._revoke_raw_token(refresh_token)

    async def _revoke_raw_token(self, token: str) -> None:
        payload = decode_token(token)
        expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        token_hash = hash_token(token)
        if not await self.revoked_repo.is_revoked(token_hash):
            await self.revoked_repo.revoke(token_hash, expires_at)
