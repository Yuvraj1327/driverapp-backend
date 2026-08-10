"""
Vehicle <-> Driver assignment service.
Ensures a vehicle/driver can only have one ACTIVE assignment at a time.
"""
import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import AssignmentStatus
from app.models.vehicle_assignment import VehicleAssignment
from app.repositories.driver_repository import DriverRepository
from app.repositories.vehicle_assignment_repository import VehicleAssignmentRepository
from app.repositories.vehicle_repository import VehicleRepository
from app.schemas.vehicle_assignment import AssignmentCreate
from app.services.exceptions import ConflictError, NotFoundError


class AssignmentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.assignment_repo = VehicleAssignmentRepository(db)
        self.vehicle_repo = VehicleRepository(db)
        self.driver_repo = DriverRepository(db)

    async def assign(self, data: AssignmentCreate) -> VehicleAssignment:
        vehicle = await self.vehicle_repo.get(data.vehicle_id)
        if not vehicle:
            raise NotFoundError("Vehicle", str(data.vehicle_id))
        driver = await self.driver_repo.get(data.driver_id)
        if not driver:
            raise NotFoundError("Driver", str(data.driver_id))

        active_vehicle_assignment = await self.assignment_repo.get_active_for_vehicle(data.vehicle_id)
        if active_vehicle_assignment:
            raise ConflictError("This vehicle is already assigned to a driver")

        active_driver_assignment = await self.assignment_repo.get_active_for_driver(data.driver_id)
        if active_driver_assignment:
            raise ConflictError("This driver is already assigned to a vehicle")

        assignment = await self.assignment_repo.create(
            {
                "vehicle_id": data.vehicle_id,
                "driver_id": data.driver_id,
                "assigned_date": data.assigned_date,
                "notes": data.notes,
                "status": AssignmentStatus.ACTIVE,
            }
        )
        driver.is_available = False
        await self.db.commit()
        return assignment

    async def unassign(self, assignment_id: uuid.UUID) -> VehicleAssignment:
        assignment = await self.assignment_repo.get(assignment_id)
        if not assignment:
            raise NotFoundError("VehicleAssignment", str(assignment_id))
        if assignment.status != AssignmentStatus.ACTIVE:
            raise ConflictError("This assignment is already inactive")

        assignment = await self.assignment_repo.update(
            assignment, {"status": AssignmentStatus.UNASSIGNED, "unassigned_date": date.today()}
        )
        driver = await self.driver_repo.get(assignment.driver_id)
        if driver:
            driver.is_available = True
            await self.db.commit()
        return assignment

    async def list_assignments(self, page: int, page_size: int, vehicle_id=None, driver_id=None):
        from app.schemas.common import Page

        filters = {}
        if vehicle_id:
            filters["vehicle_id"] = vehicle_id
        if driver_id:
            filters["driver_id"] = driver_id
        items, total = await self.assignment_repo.list(
            page=page, page_size=page_size, filters=filters or None
        )
        return Page.create(items=items, total=total, page=page, page_size=page_size)
