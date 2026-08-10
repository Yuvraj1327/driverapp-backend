from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    def __init__(self, db: AsyncSession):
        super().__init__(Report, db)
