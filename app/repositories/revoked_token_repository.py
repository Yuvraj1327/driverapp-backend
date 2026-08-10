from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.revoked_token import RevokedToken
from app.repositories.base import BaseRepository


class RevokedTokenRepository(BaseRepository[RevokedToken]):
    def __init__(self, db: AsyncSession):
        super().__init__(RevokedToken, db)

    async def is_revoked(self, token_hash: str) -> bool:
        result = await self.db.execute(
            select(RevokedToken).where(RevokedToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none() is not None

    async def revoke(self, token_hash: str, expires_at: datetime) -> RevokedToken:
        return await self.create({"token_hash": token_hash, "expires_at": expires_at})

    async def purge_expired(self) -> None:
        await self.db.execute(delete(RevokedToken).where(RevokedToken.expires_at < datetime.now(timezone.utc)))
        await self.db.commit()
