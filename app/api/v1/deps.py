"""
Shared query-parameter schemas for pagination used across routers.
"""
from fastapi import Query

from app.core.config import settings


def pagination_params(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
) -> tuple[int, int]:
    return page, page_size
