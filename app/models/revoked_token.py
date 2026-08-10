"""
Revoked (blacklisted) refresh tokens — enables real logout semantics for an
otherwise-stateless JWT setup. Only refresh tokens are blacklisted (access
tokens are short-lived by design and simply expire).
"""
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDMixin


class RevokedToken(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "revoked_tokens"

    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        return f"<RevokedToken {self.token_hash[:8]}...>"
