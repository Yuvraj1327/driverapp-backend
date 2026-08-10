"""
Generic async repository providing common CRUD + pagination operations.
"""
import uuid
from typing import Any, Generic, Sequence, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: uuid.UUID) -> ModelType | None:
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: dict[str, Any] | None = None,
        order_by: Any = None,
    ) -> tuple[Sequence[ModelType], int]:
        stmt = select(self.model)
        count_stmt = select(func.count()).select_from(self.model)

        if filters:
            for field, value in filters.items():
                if value is not None:
                    column = getattr(self.model, field)
                    stmt = stmt.where(column == value)
                    count_stmt = count_stmt.where(column == value)

        if order_by is not None:
            stmt = stmt.order_by(order_by)

        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        items = result.scalars().all()
        return items, total

    async def create(self, obj_in: dict[str, Any]) -> ModelType:
        obj = self.model(**obj_in)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def update(self, db_obj: ModelType, obj_in: dict[str, Any]) -> ModelType:
        for field, value in obj_in.items():
            if value is not None:
                setattr(db_obj, field, value)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, db_obj: ModelType) -> None:
        await self.db.delete(db_obj)
        await self.db.commit()
