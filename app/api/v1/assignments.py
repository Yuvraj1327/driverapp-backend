"""
Vehicle <-> Driver assignment endpoints.
"""
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import pagination_params
from app.auth.dependencies import require_any_role, require_manager
from app.database.session import get_db
from app.schemas.common import Page
from app.schemas.vehicle_assignment import AssignmentCreate, AssignmentRead
from app.services.assignment_service import AssignmentService

router = APIRouter(prefix="/assignments", tags=["Vehicle Assignments"])


@router.post(
    "", include_in_schema=False, response_model=AssignmentRead, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_manager)],
)
@router.post(
    "/", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_manager)],
)
async def assign_driver(payload: AssignmentCreate, db: AsyncSession = Depends(get_db)) -> AssignmentRead:
    service = AssignmentService(db)
    assignment = await service.assign(payload)
    return AssignmentRead.model_validate(assignment)


@router.post(
    "/{assignment_id}/unassign", response_model=AssignmentRead, dependencies=[Depends(require_manager)]
)
async def unassign_driver(assignment_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> AssignmentRead:
    service = AssignmentService(db)
    assignment = await service.unassign(assignment_id)
    return AssignmentRead.model_validate(assignment)


@router.get("", include_in_schema=False, response_model=Page[AssignmentRead], dependencies=[Depends(require_any_role)])
@router.get("/", response_model=Page[AssignmentRead], dependencies=[Depends(require_any_role)])
async def list_assignments(
    pagination: tuple[int, int] = Depends(pagination_params),
    vehicle_id: uuid.UUID | None = Query(default=None),
    driver_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> Page[AssignmentRead]:
    page, page_size = pagination
    service = AssignmentService(db)
    result = await service.list_assignments(page, page_size, vehicle_id, driver_id)
    return Page[AssignmentRead](
        items=[AssignmentRead.model_validate(a) for a in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        pages=result.pages,
    )
