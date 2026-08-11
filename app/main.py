"""
FleetFlow FastAPI application entrypoint.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging_config import get_logger, setup_logging
from app.jobs.scheduler import shutdown_scheduler, start_scheduler
from app.middleware.error_handler import register_exception_handlers
from app.middleware.logging_middleware import RequestLoggingMiddleware

setup_logging(debug=settings.DEBUG)
logger = get_logger("fleetflow.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s in %s mode", settings.APP_NAME, settings.APP_ENV)
    start_scheduler()
    yield
    shutdown_scheduler()
    logger.info("%s shut down", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "FleetFlow — Fleet Management & Driver Expense System API. "
        "Manage vehicles, drivers, assignments, KM logs, expenses, tyres, "
        "service history, reminders, notifications, and reports."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    # `flutter run -d chrome` (and `flutter run -d web-server`) serve the app
    # on a dynamically-assigned localhost port, so a fixed origin allowlist
    # blocks local development entirely (verified: Starlette's CORSMiddleware
    # returns 400 "Disallowed CORS origin" with no CORS headers for any
    # origin not in `allow_origins`, and a browser refuses to read the
    # response — this is *not* the same failure mode as a 401/404, it never
    # reaches our routes at all). Accept any localhost/127.0.0.1 port in
    # addition to the explicit production allowlist above.
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

register_exception_handlers(app)

app.mount(f"/{settings.UPLOAD_DIR}", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Health"], summary="Root health check")
async def root() -> dict:
    return {"app": settings.APP_NAME, "status": "ok", "docs": "/docs"}


@app.get("/health", tags=["Health"], summary="Liveness/readiness probe")
async def health() -> dict:
    return {"status": "healthy"}
