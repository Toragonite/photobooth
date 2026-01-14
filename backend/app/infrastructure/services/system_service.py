"""System management service for reboot and service operations."""

import asyncio
import logging
import os
import psutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from ...application.ports.services.system_service_port import (
    LogEntry,
    SystemHealth,
    SystemServicePort,
)
from ...config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class ServiceName(str, Enum):
    """System services that can be managed."""

    CUPS = "cups"
    BACKEND = "photobooth-backend"
    HOSTAPD = "hostapd"
    DNSMASQ = "dnsmasq"


class ServiceStatus(str, Enum):
    """Service status."""

    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class ServiceInfo:
    """Service information."""

    name: str
    display_name: str
    status: ServiceStatus
    description: str
    can_restart: bool
    warning_level: str  # "low", "medium", "high"


@dataclass
class RebootStatus:
    """Reboot status."""

    scheduled: bool
    scheduled_at: Optional[datetime] = None
    delay_seconds: int = 10
    can_cancel: bool = True


class SystemService(SystemServicePort):
    """Service for system management operations.

    Implements SystemServicePort interface for Clean Architecture compatibility.
    """

    # Scheduled reboot task
    _reboot_task: Optional[asyncio.Task] = None
    _reboot_scheduled_at: Optional[datetime] = None

    def __init__(self):
        self.mock_mode = settings.debug  # Mock mode in debug
        logger.info(f"SystemService initialized (mock_mode={self.mock_mode})")

    def get_services(self) -> List[ServiceInfo]:
        """Get list of manageable services."""
        services = [
            ServiceInfo(
                name=ServiceName.CUPS.value,
                display_name="Print Service (CUPS)",
                status=self._get_service_status(ServiceName.CUPS),
                description="Manages print queue and printer communication",
                can_restart=True,
                warning_level="low",
            ),
            ServiceInfo(
                name=ServiceName.BACKEND.value,
                display_name="PhotoBooth Backend",
                status=self._get_service_status(ServiceName.BACKEND),
                description="Main application server",
                can_restart=True,
                warning_level="high",  # Will disconnect admin
            ),
            ServiceInfo(
                name=ServiceName.HOSTAPD.value,
                display_name="Wi-Fi Access Point",
                status=self._get_service_status(ServiceName.HOSTAPD),
                description="Wi-Fi access point for client devices",
                can_restart=True,
                warning_level="medium",
            ),
            ServiceInfo(
                name=ServiceName.DNSMASQ.value,
                display_name="DHCP Server",
                status=self._get_service_status(ServiceName.DNSMASQ),
                description="Provides IP addresses to connected devices",
                can_restart=True,
                warning_level="medium",
            ),
        ]
        return services

    def _get_service_status(self, service: ServiceName) -> ServiceStatus:
        """Get status of a service."""
        if self.mock_mode:
            return ServiceStatus.RUNNING

        try:
            result = subprocess.run(
                ["systemctl", "is-active", service.value],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.stdout.strip() == "active":
                return ServiceStatus.RUNNING
            elif result.stdout.strip() == "inactive":
                return ServiceStatus.STOPPED
            elif result.stdout.strip() == "failed":
                return ServiceStatus.FAILED
            else:
                return ServiceStatus.UNKNOWN
        except Exception as e:
            logger.error(f"Failed to get status of {service.value}: {e}")
            return ServiceStatus.UNKNOWN

    async def restart_service(self, service_name: str) -> Dict:
        """Restart a system service.

        Args:
            service_name: Name of service to restart

        Returns:
            Dict with result info
        """
        # Validate service name
        try:
            service = ServiceName(service_name)
        except ValueError:
            return {
                "success": False,
                "error": f"Unknown service: {service_name}",
            }

        logger.warning(f"Restarting service: {service_name}")

        if self.mock_mode:
            # Simulate restart
            await asyncio.sleep(1)
            logger.info(f"Mock: Service {service_name} restarted")
            return {
                "success": True,
                "service": service_name,
                "message": f"Service {service_name} restarted (mock mode)",
                "new_status": ServiceStatus.RUNNING.value,
            }

        try:
            # Execute systemctl restart
            result = subprocess.run(
                ["sudo", "systemctl", "restart", service.value],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                # Wait a moment for service to start
                await asyncio.sleep(2)
                new_status = self._get_service_status(service)

                logger.info(f"Service {service_name} restarted successfully")
                return {
                    "success": True,
                    "service": service_name,
                    "message": f"Service {service_name} restarted",
                    "new_status": new_status.value,
                }
            else:
                logger.error(f"Failed to restart {service_name}: {result.stderr}")
                return {
                    "success": False,
                    "service": service_name,
                    "error": result.stderr.strip() or "Restart command failed",
                }

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout restarting {service_name}")
            return {
                "success": False,
                "service": service_name,
                "error": "Restart command timed out",
            }
        except Exception as e:
            logger.error(f"Exception restarting {service_name}: {e}")
            return {
                "success": False,
                "service": service_name,
                "error": str(e),
            }

    async def schedule_reboot(
        self, delay_seconds: int = 10, force: bool = False
    ) -> Dict:
        """Schedule a system reboot.

        Args:
            delay_seconds: Seconds before reboot
            force: Force reboot even with active jobs

        Returns:
            Dict with scheduling info
        """
        logger.warning(f"System reboot scheduled in {delay_seconds} seconds")

        # Cancel any existing reboot
        await self.cancel_reboot()

        SystemService._reboot_scheduled_at = datetime.now()

        if self.mock_mode:
            # Create mock reboot task
            async def mock_reboot():
                await asyncio.sleep(delay_seconds)
                logger.warning("Mock: System would reboot now")

            SystemService._reboot_task = asyncio.create_task(mock_reboot())

            return {
                "success": True,
                "message": f"Reboot scheduled in {delay_seconds} seconds (mock mode)",
                "scheduled_at": SystemService._reboot_scheduled_at.isoformat(),
                "delay_seconds": delay_seconds,
                "can_cancel": True,
                "mock_mode": True,
            }

        # Create actual reboot task
        async def do_reboot():
            await asyncio.sleep(delay_seconds)
            logger.warning("Executing system reboot")
            os.system("sudo reboot")

        SystemService._reboot_task = asyncio.create_task(do_reboot())

        return {
            "success": True,
            "message": f"Reboot scheduled in {delay_seconds} seconds",
            "scheduled_at": SystemService._reboot_scheduled_at.isoformat(),
            "delay_seconds": delay_seconds,
            "can_cancel": True,
            "mock_mode": False,
        }

    async def cancel_reboot(self) -> Dict:
        """Cancel a scheduled reboot.

        Returns:
            Dict with cancellation result
        """
        if SystemService._reboot_task is not None:
            SystemService._reboot_task.cancel()
            try:
                await SystemService._reboot_task
            except asyncio.CancelledError:
                pass

            SystemService._reboot_task = None
            SystemService._reboot_scheduled_at = None

            logger.info("Scheduled reboot cancelled")
            return {
                "success": True,
                "message": "Reboot cancelled",
                "was_scheduled": True,
            }

        return {
            "success": True,
            "message": "No reboot was scheduled",
            "was_scheduled": False,
        }

    def get_reboot_status(self) -> RebootStatus:
        """Get current reboot status.

        Returns:
            RebootStatus object
        """
        if (
            SystemService._reboot_task is not None
            and not SystemService._reboot_task.done()
        ):
            return RebootStatus(
                scheduled=True,
                scheduled_at=SystemService._reboot_scheduled_at,
                can_cancel=True,
            )

        return RebootStatus(scheduled=False)

    async def shutdown_system(self, delay_seconds: int = 10) -> Dict:
        """Schedule a system shutdown.

        Args:
            delay_seconds: Seconds before shutdown

        Returns:
            Dict with scheduling info
        """
        logger.warning(f"System shutdown scheduled in {delay_seconds} seconds")

        if self.mock_mode:
            logger.info("Mock: Shutdown scheduled")
            return {
                "success": True,
                "message": f"Shutdown scheduled in {delay_seconds} seconds (mock mode)",
                "delay_seconds": delay_seconds,
                "mock_mode": True,
            }

        # Schedule shutdown
        async def do_shutdown():
            await asyncio.sleep(delay_seconds)
            logger.warning("Executing system shutdown")
            os.system("sudo shutdown -h now")

        asyncio.create_task(do_shutdown())

        return {
            "success": True,
            "message": f"Shutdown scheduled in {delay_seconds} seconds",
            "delay_seconds": delay_seconds,
            "mock_mode": False,
        }

    # ─────────────────────────────────────────────────────────────────
    # SystemServicePort interface implementation
    # ─────────────────────────────────────────────────────────────────

    async def get_health(self) -> SystemHealth:
        """Get current system health metrics (Port interface)."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Try to get CPU temperature (Raspberry Pi specific)
            temperature = None
            try:
                with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                    temperature = int(f.read().strip()) / 1000.0
            except (FileNotFoundError, PermissionError):
                pass

            # Determine overall health
            if disk.percent > 95 or memory.percent > 95:
                overall = "critical"
            elif disk.percent > 85 or memory.percent > 85 or cpu_percent > 90:
                overall = "degraded"
            else:
                overall = "healthy"

            return SystemHealth(
                overall=overall,
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk.percent,
                temperature=temperature,
            )

        except Exception as e:
            logger.error(f"Failed to get health: {e}")
            return SystemHealth(
                overall="critical",
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
            )

    async def restart_service(self, service_name: str) -> bool:
        """Restart a system service (Port interface)."""
        result = await self._restart_service_internal(service_name)
        return result.get("success", False)

    async def _restart_service_internal(self, service_name: str) -> Dict:
        """Internal restart service implementation."""
        # Validate service name
        try:
            service = ServiceName(service_name)
        except ValueError:
            return {
                "success": False,
                "error": f"Unknown service: {service_name}",
            }

        logger.warning(f"Restarting service: {service_name}")

        if self.mock_mode:
            await asyncio.sleep(1)
            logger.info(f"Mock: Service {service_name} restarted")
            return {
                "success": True,
                "service": service_name,
                "message": f"Service {service_name} restarted (mock mode)",
                "new_status": ServiceStatus.RUNNING.value,
            }

        try:
            result = subprocess.run(
                ["sudo", "systemctl", "restart", service.value],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                await asyncio.sleep(2)
                new_status = self._get_service_status(service)
                logger.info(f"Service {service_name} restarted successfully")
                return {
                    "success": True,
                    "service": service_name,
                    "message": f"Service {service_name} restarted",
                    "new_status": new_status.value,
                }
            else:
                logger.error(f"Failed to restart {service_name}: {result.stderr}")
                return {
                    "success": False,
                    "service": service_name,
                    "error": result.stderr.strip() or "Restart command failed",
                }

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout restarting {service_name}")
            return {
                "success": False,
                "service": service_name,
                "error": "Restart command timed out",
            }
        except Exception as e:
            logger.error(f"Exception restarting {service_name}: {e}")
            return {
                "success": False,
                "service": service_name,
                "error": str(e),
            }

    async def reboot_system(self, delay_seconds: int = 0) -> bool:
        """Reboot the system (Port interface)."""
        result = await self.schedule_reboot(delay_seconds=delay_seconds)
        return result.get("success", False)

    async def get_logs(
        self,
        source: str,
        limit: int = 100,
        level: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> List[LogEntry]:
        """Retrieve system logs (Port interface)."""
        # Import the log viewer service
        from .log_viewer import LogViewerService

        viewer = LogViewerService()

        try:
            logs = await viewer.get_logs(
                source=source,
                limit=limit,
                level=level,
                since=since,
            )

            return [
                LogEntry(
                    timestamp=log.get("timestamp", ""),
                    level=log.get("level", "info"),
                    source=source,
                    message=log.get("message", ""),
                )
                for log in logs
            ]
        except Exception as e:
            logger.error(f"Failed to get logs: {e}")
            return []

    async def cancel_scheduled_reboot(self) -> bool:
        """Cancel a scheduled reboot (Port interface)."""
        result = await self.cancel_reboot()
        return result.get("success", False)
