"""Background task scheduler for PhotoBooth."""

import logging
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .database import async_session
from .services.cleanup_service import CleanupService
from .services.storage_service import StorageService

logger = logging.getLogger(__name__)


class AppScheduler:
    """Application scheduler for background tasks."""

    def __init__(self, enabled: bool = True):
        """Initialize the scheduler.

        Args:
            enabled: Whether to actually run scheduled jobs
        """
        self.enabled = enabled
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._cleanup_service = CleanupService()
        self._storage_service = StorageService()

    def start(self):
        """Start the scheduler."""
        if not self.enabled:
            logger.info("Scheduler disabled, skipping start")
            return

        self._scheduler = AsyncIOScheduler()
        self._setup_jobs()
        self._scheduler.start()
        logger.info("Scheduler started")

    def shutdown(self):
        """Shutdown the scheduler gracefully."""
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            logger.info("Scheduler shut down")

    def _setup_jobs(self):
        """Configure scheduled jobs."""
        if not self._scheduler:
            return

        # Daily cleanup at 2:00 AM
        self._scheduler.add_job(
            self._daily_cleanup,
            CronTrigger(hour=2, minute=0),
            id="daily_cleanup",
            name="Daily Storage Cleanup",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )

        # Storage monitor every 30 minutes
        self._scheduler.add_job(
            self._check_storage,
            IntervalTrigger(minutes=30),
            id="storage_monitor",
            name="Storage Monitor",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )

        logger.info(
            "Scheduled jobs configured: daily_cleanup (2:00 AM), storage_monitor (30min)"
        )

    async def _daily_cleanup(self):
        """Execute daily cleanup task."""
        logger.info("Starting daily cleanup")

        try:
            async with async_session() as db:
                # Get retention days from settings
                import json

                from sqlalchemy import select

                from .database import SettingsModel

                result = await db.execute(
                    select(SettingsModel).where(
                        SettingsModel.key == "system.auto_cleanup_days"
                    )
                )
                setting = result.scalar_one_or_none()

                retention_days = 30
                if setting:
                    try:
                        retention_days = int(json.loads(setting.value))
                    except (json.JSONDecodeError, ValueError):
                        pass

                # Execute cleanup
                cleanup_result = await self._cleanup_service.execute_cleanup(
                    db, retention_days=retention_days
                )

                if cleanup_result.success:
                    logger.info(
                        f"Daily cleanup completed: {cleanup_result.sessions_cleaned} sessions, "
                        f"{cleanup_result.bytes_freed / (1024*1024):.1f} MB freed"
                    )
                else:
                    logger.warning(
                        f"Daily cleanup completed with errors: {cleanup_result.errors}"
                    )

        except Exception as e:
            logger.error(f"Daily cleanup failed: {str(e)}")

    async def _check_storage(self):
        """Monitor storage and trigger emergency cleanup if needed."""
        try:
            status = self._cleanup_service.get_storage_status()

            if status["health"] == "critical":
                logger.warning(
                    f"Storage critical ({status['percent_used']:.1f}%), "
                    "triggering emergency cleanup"
                )

                async with async_session() as db:
                    result = await self._cleanup_service.emergency_cleanup(db)
                    logger.info(
                        f"Emergency cleanup result: {result.bytes_freed / (1024*1024):.1f} MB freed"
                    )

            elif status["health"] == "warning":
                logger.info(f"Storage warning: {status['percent_used']:.1f}% used")

        except Exception as e:
            logger.error(f"Storage check failed: {str(e)}")

    def get_jobs_info(self) -> list:
        """Get information about scheduled jobs."""
        if not self._scheduler:
            return []

        jobs = []
        for job in self._scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": (
                        job.next_run_time.isoformat() if job.next_run_time else None
                    ),
                }
            )

        return jobs


# Global scheduler instance (will be initialized in main.py)
scheduler: Optional[AppScheduler] = None


def get_scheduler() -> Optional[AppScheduler]:
    """Get the global scheduler instance."""
    return scheduler


def init_scheduler(enabled: bool = True) -> AppScheduler:
    """Initialize and return the global scheduler."""
    global scheduler
    scheduler = AppScheduler(enabled=enabled)
    return scheduler
