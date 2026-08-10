"""
Aggregates all v1 routers into a single APIRouter mounted in main.py.
"""
from fastapi import APIRouter

from app.api.v1 import (
    assignments,
    auth,
    drivers,
    expense_categories,
    expenses,
    km_logs,
    notifications,
    reminders,
    reports,
    services,
    tyres,
    users,
    vehicles,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(drivers.router)
api_router.include_router(vehicles.router)
api_router.include_router(assignments.router)
api_router.include_router(km_logs.router)
api_router.include_router(expense_categories.router)
api_router.include_router(expenses.router)
api_router.include_router(tyres.router)
api_router.include_router(services.router)
api_router.include_router(reminders.router)
api_router.include_router(notifications.router)
api_router.include_router(reports.router)
