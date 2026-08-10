"""
FastAPI dependencies for authentication and role-based access control.
"""
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.jwt_handler import InvalidTokenError, parse_token
from app.core.constants import RoleName
from app.database.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=True)


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token_data = parse_token(token, expected_type="access")
    except InvalidTokenError:
        raise credentials_exception

    try:
        user_id = uuid.UUID(token_data.sub)
    except ValueError:
        raise credentials_exception

    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


class RoleChecker:
    """Dependency factory that restricts an endpoint to a set of roles."""

    def __init__(self, allowed_roles: list[RoleName]):
        self.allowed_roles = {r.value for r in allowed_roles}

    async def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        role_name = current_user.role.name if current_user.role else None
        if role_name not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user


require_admin = RoleChecker([RoleName.ADMIN])
require_manager = RoleChecker([RoleName.ADMIN, RoleName.MANAGER])
require_any_role = RoleChecker([RoleName.ADMIN, RoleName.MANAGER, RoleName.DRIVER])
