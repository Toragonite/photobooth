"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .adapters.api import admin, health, print_jobs, session, setup
from .config import get_settings
from .infrastructure.database import init_db
from .infrastructure.scheduler import init_scheduler

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.log_file),
    ],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    await init_db()
    logger.info("Database initialized")

    # Start scheduler (disabled in debug mode for faster dev restarts)
    scheduler = init_scheduler(enabled=not settings.debug)
    scheduler.start()

    yield

    # Shutdown
    scheduler.shutdown()
    logger.info("Shutting down application")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="4-cut photo booth application for missionary locations",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(session.router, prefix="/api", tags=["Session"])
app.include_router(print_jobs.router, prefix="/api", tags=["Print"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(setup.router, prefix="/api", tags=["Setup"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }
