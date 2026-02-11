"""Printer service with CUPS integration and mock mode for development.

Supports multiple printers with configurable selection strategies.
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from ...application.ports.services.printer_port import PrinterPort
from ...application.ports.services.printer_port import \
    PrinterStatus as PortPrinterStatus
from ...application.ports.services.printer_port import \
    PrintResult as PortPrintResult
from ...config import get_settings
from ...domain.value_objects import ErrorCode

settings = get_settings()
logger = logging.getLogger(__name__)


class PrinterState(str, Enum):
    """Printer state."""

    IDLE = "idle"
    PROCESSING = "processing"
    PRINTING = "printing"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class PrinterInfo:
    """Printer information."""

    name: str
    model: str
    state: PrinterState
    state_message: str
    is_default: bool
    is_shared: bool


@dataclass
class PrintResult:
    """Result of a print operation."""

    success: bool
    job_id: Optional[int] = None
    printer_name: Optional[str] = None
    error_code: Optional[ErrorCode] = None
    error_message: Optional[str] = None


class PrinterService(PrinterPort):
    """Service for printer operations with CUPS or mock mode.

    Supports multiple printers with round-robin, least-busy, or failover strategies.
    """

    def __init__(self):
        self.mock_mode = settings.printer_mock_mode
        self.selection_strategy = settings.printer_selection_strategy
        self.name_pattern = settings.printer_name_pattern.lower()
        self._cups = None
        self._mock_job_counter = 1000
        self._round_robin_index = 0
        self._discovered_printers: List[str] = []
        self._last_troubleshoot_attempt = 0

        if not self.mock_mode:
            try:
                import cups

                self._cups = cups.Connection()

                # Always try to auto-discover printers from CUPS first
                self._discovered_printers = self._discover_printers()

                if self._discovered_printers:
                    logger.info(
                        f"Auto-discovered {len(self._discovered_printers)} printer(s): "
                        f"{self._discovered_printers}"
                    )
                else:
                    # No printers found - attempt auto-troubleshooting
                    logger.warning(
                        f"No printers matching pattern '{self.name_pattern}' found in CUPS. "
                        "Attempting auto-troubleshooting..."
                    )
                    self._auto_troubleshoot()

                    # Re-discover after troubleshooting
                    self._discovered_printers = self._discover_printers()
                    if self._discovered_printers:
                        logger.info(
                            f"After troubleshooting, discovered: {self._discovered_printers}"
                        )
                    else:
                        logger.error(
                            "No printers found after troubleshooting. "
                            "Please check USB connections and run manual troubleshooting."
                        )

                logger.info(
                    f"CUPS connection established. "
                    f"Active printers: {self.printer_names}, "
                    f"strategy: {self.selection_strategy}"
                )
            except ImportError:
                logger.warning("pycups not installed, using mock mode")
                self.mock_mode = True
            except Exception as e:
                logger.error(f"Failed to connect to CUPS: {e}")
                self.mock_mode = True

        if self.mock_mode:
            # In mock mode, create mock printers for testing
            self._discovered_printers = ["SelphyCP1500-Mock", "SelphyCP1500-Mock-2"]
            logger.info(
                f"Printer service running in MOCK mode. "
                f"Active printers: {self.printer_names}"
            )

    def _discover_printers(self) -> List[str]:
        """Discover printers from CUPS matching the name pattern."""
        if self._cups is None:
            return []

        try:
            cups_printers = self._cups.getPrinters()
            discovered = [
                name for name in cups_printers.keys()
                if self.name_pattern in name.lower()
            ]
            # Sort to ensure consistent ordering (SelphyCP1500, SelphyCP1500-2, etc.)
            return sorted(discovered)
        except Exception as e:
            logger.error(f"Failed to discover printers: {e}")
            return []

    def refresh_printers(self, auto_troubleshoot: bool = False) -> List[str]:
        """Refresh the list of discovered printers from CUPS.

        Args:
            auto_troubleshoot: If True and no printers found, attempt auto-troubleshooting
        """
        if self.mock_mode:
            return self.printer_names

        self._discovered_printers = self._discover_printers()
        logger.info(f"Refreshed printer list: {self._discovered_printers}")

        # If no printers found and auto_troubleshoot requested
        if not self._discovered_printers and auto_troubleshoot:
            logger.warning("No printers found during refresh, attempting auto-troubleshoot...")
            self._auto_troubleshoot()
            self._discovered_printers = self._discover_printers()

        return self.printer_names

    def _auto_troubleshoot(self) -> bool:
        """Attempt automatic troubleshooting when no printers are found.

        Returns:
            True if troubleshooting was attempted, False if skipped
        """
        import time
        import subprocess

        # Rate limit: don't troubleshoot more than once per minute
        current_time = time.time()
        if current_time - self._last_troubleshoot_attempt < 60:
            logger.debug("Skipping auto-troubleshoot (rate limited)")
            return False

        self._last_troubleshoot_attempt = current_time
        logger.info("Starting automatic printer troubleshooting...")

        try:
            # Step 1: Check if ipp-usb is interfering
            result = subprocess.run(
                ["systemctl", "is-active", "ipp-usb"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.stdout.strip() == "active":
                logger.info("Auto-troubleshoot: Stopping ipp-usb service...")
                subprocess.run(
                    ["sudo", "systemctl", "stop", "ipp-usb"],
                    capture_output=True,
                    timeout=10
                )
                subprocess.run(
                    ["sudo", "pkill", "-9", "ipp-usb"],
                    capture_output=True,
                    timeout=5
                )
                time.sleep(1)

            # Step 2: Load usblp module
            logger.info("Auto-troubleshoot: Loading usblp module...")
            subprocess.run(
                ["sudo", "modprobe", "usblp"],
                capture_output=True,
                timeout=5
            )

            # Step 3: Find and rebind Canon USB devices
            logger.info("Auto-troubleshoot: Rebinding USB devices...")
            self._rebind_usb_devices()

            # Step 4: Wait for devices to settle
            time.sleep(3)

            # Step 5: Try to auto-register any detected printers
            logger.info("Auto-troubleshoot: Checking for unregistered printers...")
            self._auto_register_printers()

            logger.info("Auto-troubleshoot: Complete")
            return True

        except Exception as e:
            logger.error(f"Auto-troubleshoot failed: {e}")
            return False

    def _rebind_usb_devices(self):
        """Rebind Canon USB devices to reset their state."""
        import subprocess
        import os

        canon_vendor_id = "04a9"

        try:
            # Find USB devices with Canon vendor ID
            usb_devices_path = "/sys/bus/usb/devices"
            if not os.path.exists(usb_devices_path):
                return

            for device in os.listdir(usb_devices_path):
                vendor_path = os.path.join(usb_devices_path, device, "idVendor")
                if os.path.exists(vendor_path):
                    try:
                        with open(vendor_path, "r") as f:
                            vendor = f.read().strip()
                        if vendor == canon_vendor_id:
                            logger.info(f"Rebinding USB device: {device}")
                            # Unbind
                            unbind_path = "/sys/bus/usb/drivers/usb/unbind"
                            subprocess.run(
                                ["sudo", "tee", unbind_path],
                                input=device.encode(),
                                capture_output=True,
                                timeout=5
                            )
                            import time
                            time.sleep(1)
                            # Bind
                            bind_path = "/sys/bus/usb/drivers/usb/bind"
                            subprocess.run(
                                ["sudo", "tee", bind_path],
                                input=device.encode(),
                                capture_output=True,
                                timeout=5
                            )
                    except Exception as e:
                        logger.debug(f"Could not check device {device}: {e}")
        except Exception as e:
            logger.error(f"Failed to rebind USB devices: {e}")

    def _auto_register_printers(self):
        """Auto-register any detected but unregistered Canon Selphy printers."""
        import subprocess

        try:
            # Get list of USB-connected Canon printers
            result = subprocess.run(
                ["lsusb", "-v"],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Parse serial numbers from lsusb output
            serials = []
            lines = result.stdout.split("\n")
            in_canon_device = False
            for line in lines:
                if "04a9:3302" in line:  # Canon Selphy CP1500
                    in_canon_device = True
                elif in_canon_device and "iSerial" in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        serials.append(parts[-1])
                    in_canon_device = False

            if not serials:
                logger.info("No Canon Selphy CP1500 detected on USB")
                return

            # Get already registered printer serials
            registered_serials = set()
            if self._cups:
                try:
                    for name, info in self._cups.getPrinters().items():
                        uri = info.get("device-uri", "")
                        if "serial=" in uri:
                            serial = uri.split("serial=")[1].split("&")[0]
                            registered_serials.add(serial)
                except Exception:
                    pass

            # Register unregistered printers
            for serial in serials:
                if serial in registered_serials:
                    logger.debug(f"Printer with serial {serial} already registered")
                    continue

                # Determine printer name
                existing_count = len([
                    n for n in (self._cups.getPrinters().keys() if self._cups else [])
                    if self.name_pattern in n.lower()
                ])
                printer_name = "SelphyCP1500"
                if existing_count > 0:
                    printer_name = f"SelphyCP1500-{existing_count + 1}"

                uri = f"usb://Canon/SELPHY%20CP1500?serial={serial}"

                logger.info(f"Auto-registering printer: {printer_name} (serial: {serial})")

                try:
                    # Try using existing PPD first
                    ppd_path = "/etc/cups/ppd/SelphyCP1500.ppd"
                    import os
                    if os.path.exists(ppd_path):
                        subprocess.run(
                            ["sudo", "lpadmin", "-p", printer_name, "-E",
                             "-v", uri, "-P", ppd_path,
                             "-D", f"Canon Selphy CP1500 (Serial: {serial})",
                             "-L", "PhotoBooth"],
                            capture_output=True,
                            timeout=15
                        )
                    else:
                        # Use gutenprint driver
                        subprocess.run(
                            ["sudo", "lpadmin", "-p", printer_name, "-E",
                             "-v", uri,
                             "-m", "gutenprint.5.3://canon-cp1300/expert",
                             "-D", f"Canon Selphy CP1500 (Serial: {serial})",
                             "-L", "PhotoBooth"],
                            capture_output=True,
                            timeout=15
                        )

                    # Enable the printer
                    subprocess.run(
                        ["sudo", "cupsenable", printer_name],
                        capture_output=True,
                        timeout=5
                    )
                    subprocess.run(
                        ["sudo", "cupsaccept", printer_name],
                        capture_output=True,
                        timeout=5
                    )

                    logger.info(f"Successfully registered printer: {printer_name}")

                except Exception as e:
                    logger.error(f"Failed to register printer {printer_name}: {e}")

        except Exception as e:
            logger.error(f"Auto-register printers failed: {e}")

    @property
    def printer_names(self) -> List[str]:
        """Get list of active printer names from auto-discovery."""
        return self._discovered_printers

    @property
    def has_printers(self) -> bool:
        """Check if any printers are available."""
        return len(self.printer_names) > 0

    @property
    def primary_printer_name(self) -> Optional[str]:
        """Get the first available printer name, or None if no printers."""
        names = self.printer_names
        return names[0] if names else None

    def is_available(self, printer_name: Optional[str] = None) -> bool:
        """Check if a specific printer (or any configured printer) is available."""
        if self.mock_mode:
            return True

        try:
            cups_printers = self._cups.getPrinters()
            if printer_name:
                return printer_name in cups_printers
            return any(name in cups_printers for name in self.printer_names)
        except Exception as e:
            logger.error(f"Failed to check printer availability: {e}")
            return False

    def get_printers(self) -> List[PrinterInfo]:
        """Get list of available printers (only configured ones)."""
        if self.mock_mode:
            return [
                PrinterInfo(
                    name=name,
                    model="Canon Selphy CP1500 (Mock)",
                    state=PrinterState.IDLE,
                    state_message="Ready",
                    is_default=(i == 0),
                    is_shared=False,
                )
                for i, name in enumerate(self.printer_names)
            ]

        try:
            cups_printers = self._cups.getPrinters()
            default = self._cups.getDefault()

            result = []
            for name in self.printer_names:
                if name in cups_printers:
                    info = cups_printers[name]
                    result.append(
                        PrinterInfo(
                            name=name,
                            model=info.get("printer-make-and-model", "Unknown"),
                            state=self._map_cups_state(info.get("printer-state", 3)),
                            state_message=info.get("printer-state-message", ""),
                            is_default=name == default,
                            is_shared=info.get("printer-is-shared", False),
                        )
                    )
                else:
                    result.append(
                        PrinterInfo(
                            name=name,
                            model="Unknown",
                            state=PrinterState.OFFLINE,
                            state_message="Not found in CUPS",
                            is_default=False,
                            is_shared=False,
                        )
                    )
            return result
        except Exception as e:
            logger.error(f"Failed to get printers: {e}")
            return []

    def get_printer_info(self, name: Optional[str] = None) -> Optional[PrinterInfo]:
        """Get info of a specific printer (internal)."""
        name = name or self.primary_printer_name
        printers = self.get_printers()

        for printer in printers:
            if printer.name == name:
                return printer

        return None

    def _get_cups_queue_length(self, printer_name: str) -> int:
        """Get number of active jobs for a printer from CUPS."""
        if self.mock_mode:
            return 0
        try:
            jobs = self._cups.getJobs()
            count = 0
            for _job_id, job_info in jobs.items():
                if job_info.get("printer-uri", "").endswith(f"/{printer_name}"):
                    count += 1
            return count
        except Exception:
            return 0

    def _select_printer_sync(self) -> Optional[str]:
        """Select best printer based on strategy (sync internal)."""
        printers = self.get_printers()
        available = [p for p in printers if p.state in (PrinterState.IDLE, PrinterState.PROCESSING)]

        if not available:
            # Fallback: try any non-offline printer
            available = [p for p in printers if p.state != PrinterState.OFFLINE]
            if not available:
                return None

        if self.selection_strategy == "round-robin":
            idx = self._round_robin_index % len(available)
            self._round_robin_index += 1
            return available[idx].name

        elif self.selection_strategy == "least-busy":
            # Pick printer with shortest queue
            best = available[0]
            best_queue = self._get_cups_queue_length(best.name)
            for p in available[1:]:
                q = self._get_cups_queue_length(p.name)
                if q < best_queue:
                    best = p
                    best_queue = q
            return best.name

        else:  # failover
            # Use first available printer in order
            return available[0].name

    async def print_file(
        self, file_path: str, copies: int = 1, printer_name: Optional[str] = None
    ) -> PrintResult:
        """Submit a print job to a specific printer.

        If no printers are available, attempts auto-troubleshooting first.
        """
        # If no specific printer requested, select the best available one
        if printer_name:
            target = printer_name
        else:
            target = self._select_printer_sync()

        # If still no printer available, try auto-troubleshooting
        if not target:
            logger.warning("No printers available for print job. Attempting auto-troubleshoot...")
            self._auto_troubleshoot()
            self._discovered_printers = self._discover_printers()
            target = self._select_printer_sync()

            if not target:
                return PrintResult(
                    success=False,
                    printer_name=None,
                    error_code=ErrorCode.PRINTER_OFFLINE,
                    error_message="No printers available. Please check USB connections and printer power.",
                )

        if self.mock_mode:
            return await self._mock_print(file_path, copies, target)

        try:
            # Check printer is available
            status = self.get_printer_info(target)
            if not status:
                # Try to auto-discover again
                self.refresh_printers(auto_troubleshoot=True)
                status = self.get_printer_info(target)

                if not status:
                    return PrintResult(
                        success=False,
                        printer_name=target,
                        error_code=ErrorCode.PRINTER_OFFLINE,
                        error_message=f"Printer '{target}' not found",
                    )

            if status.state == PrinterState.OFFLINE:
                return PrintResult(
                    success=False,
                    printer_name=target,
                    error_code=ErrorCode.PRINTER_OFFLINE,
                    error_message=f"Printer '{target}' is offline",
                )

            # Submit job to CUPS
            options = {
                "copies": str(copies),
                "media": "Postcard.Fullbleed",  # Canon Selphy 4x6
                "print-quality": "5",  # High quality
            }

            job_id = self._cups.printFile(
                target,
                file_path,
                "PhotoBooth Print",
                options,
            )

            logger.info(f"Print job submitted: {job_id} to printer '{target}'")
            return PrintResult(success=True, job_id=job_id, printer_name=target)

        except Exception as e:
            logger.error(f"Print failed on '{target}': {e}")
            return PrintResult(
                success=False,
                printer_name=target,
                error_code=ErrorCode.CUPS_REJECTED,
                error_message=str(e),
            )

    async def _get_job_status_internal(self, job_id: int) -> Optional[dict]:
        """Get status of a print job (internal)."""
        if self.mock_mode:
            return await self._mock_job_status(job_id)

        try:
            jobs = self._cups.getJobs()
            if job_id in jobs:
                job = jobs[job_id]
                return {
                    "id": job_id,
                    "state": self._map_job_state(job.get("job-state", 0)),
                    "state_message": job.get("job-state-message", ""),
                    "completed": job.get("job-state", 0) >= 9,
                }

            # Job not in active jobs, check completed
            jobs = self._cups.getJobs(which_jobs="completed")
            if job_id in jobs:
                return {
                    "id": job_id,
                    "state": "completed",
                    "state_message": "Job completed",
                    "completed": True,
                }

            return None
        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            return None

    async def cancel_job(self, job_id: int) -> bool:
        """Cancel a print job."""
        if self.mock_mode:
            logger.info(f"Mock: Cancelled job {job_id}")
            return True

        try:
            self._cups.cancelJob(job_id)
            logger.info(f"Cancelled job {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel job: {e}")
            return False

    # Mock mode implementations
    async def _mock_print(
        self, file_path: str, copies: int, printer_name: str
    ) -> PrintResult:
        """Simulate a print job."""
        self._mock_job_counter += 1
        job_id = self._mock_job_counter

        logger.info(f"Mock print job {job_id}: {file_path} x{copies} on '{printer_name}'")

        # Simulate processing time
        await asyncio.sleep(0.5)

        return PrintResult(success=True, job_id=job_id, printer_name=printer_name)

    async def _mock_job_status(self, job_id: int) -> dict:
        """Simulate job status progression."""
        # In mock mode, jobs complete quickly
        return {
            "id": job_id,
            "state": "completed",
            "state_message": "Mock job completed",
            "completed": True,
        }

    def _map_cups_state(self, state: int) -> PrinterState:
        """Map CUPS printer state to PrinterState."""
        # CUPS states: 3=idle, 4=processing, 5=stopped
        mapping = {
            3: PrinterState.IDLE,
            4: PrinterState.PROCESSING,
            5: PrinterState.ERROR,
        }
        return mapping.get(state, PrinterState.OFFLINE)

    def _map_job_state(self, state: int) -> str:
        """Map CUPS job state to string.

        CUPS job states: 3=pending, 4=held, 5=processing,
        6=stopped, 7=canceled, 8=aborted, 9=completed
        """
        mapping = {
            3: "pending",
            4: "held",
            5: "processing",
            6: "stopped",
            7: "cancelled",
            8: "failed",
            9: "completed",
        }
        return mapping.get(state, "unknown")

    def _to_port_status(self, info: PrinterInfo) -> PortPrinterStatus:
        """Convert PrinterInfo to port PrinterStatus."""
        status_map = {
            PrinterState.IDLE: "ready",
            PrinterState.PROCESSING: "processing",
            PrinterState.PRINTING: "printing",
            PrinterState.ERROR: "error",
            PrinterState.OFFLINE: "offline",
        }
        return PortPrinterStatus(
            name=info.name,
            connected=info.state != PrinterState.OFFLINE,
            status=status_map.get(info.state, "unknown"),
            paper_status="ok",
            ink_status="ok",
            error_message=info.state_message if info.state == PrinterState.ERROR else None,
            queue_length=self._get_cups_queue_length(info.name),
        )

    # ─────────────────────────────────────────────────────────────────
    # PrinterPort interface implementation
    # ─────────────────────────────────────────────────────────────────

    async def print_image(
        self, image_path: str, copies: int = 1, printer_name: Optional[str] = None
    ) -> PortPrintResult:
        """Submit an image for printing (PrinterPort interface)."""
        result = await self.print_file(image_path, copies, printer_name)
        return PortPrintResult(
            success=result.success,
            cups_job_id=result.job_id,
            printer_name=result.printer_name,
            error_code=result.error_code.value if result.error_code else None,
            error_message=result.error_message,
        )

    async def get_job_status(self, cups_job_id: int) -> str:
        """Get the current status of a CUPS print job (PrinterPort interface)."""
        status = await self._get_job_status_internal(cups_job_id)
        if status is None:
            return "unknown"
        return status.get("state", "unknown")

    async def get_printer_status(
        self, printer_name: Optional[str] = None
    ) -> PortPrinterStatus:
        """Get status of a specific printer (PrinterPort interface)."""
        target = printer_name or self.primary_printer_name
        info = self.get_printer_info(target)
        if info is None:
            return PortPrinterStatus(
                name=target,
                connected=False,
                status="offline",
                paper_status="unknown",
                ink_status="unknown",
                error_message="Printer not found",
                queue_length=0,
            )
        return self._to_port_status(info)

    async def get_all_printer_statuses(self) -> List[PortPrinterStatus]:
        """Get statuses of all configured printers (PrinterPort interface)."""
        printers = self.get_printers()
        return [self._to_port_status(p) for p in printers]

    async def is_ready(self, printer_name: Optional[str] = None) -> bool:
        """Check if a printer is ready (PrinterPort interface)."""
        if printer_name:
            return self.is_available(printer_name)
        # If no specific printer, check if any configured printer is available
        return self.is_available()

    async def select_printer(self) -> Optional[str]:
        """Select the best available printer (PrinterPort interface)."""
        return self._select_printer_sync()

    # ─────────────────────────────────────────────────────────────────
    # Queue-based copy processing methods
    # ─────────────────────────────────────────────────────────────────

    async def print_single_copy(
        self, file_path: str, printer_name: str
    ) -> PrintResult:
        """Submit exactly one copy to the specified printer.

        This is used by the queue manager to print one copy at a time,
        bypassing the CUPS copies option which may be ignored by some printers.
        """
        return await self.print_file(file_path, copies=1, printer_name=printer_name)

    async def wait_for_job_completion(
        self, cups_job_id: int, timeout_seconds: int = 120
    ) -> tuple:
        """Wait for a CUPS job to complete.

        Args:
            cups_job_id: The CUPS job ID to monitor
            timeout_seconds: Maximum time to wait (default 120 seconds)

        Returns:
            Tuple of (success: bool, status_message: str)
        """
        poll_interval = 2
        elapsed = 0
        physical_print_time = 25  # Canon Selphy takes ~25 seconds per print

        while elapsed < timeout_seconds:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            status = await self.get_job_status(cups_job_id)
            logger.debug(f"CUPS job {cups_job_id} status: {status}")

            if status == "completed":
                # CUPS reports completed when data is sent to printer
                # Wait additional time for physical printing
                logger.info(
                    f"CUPS job {cups_job_id} data sent, "
                    f"waiting {physical_print_time}s for physical print"
                )
                await asyncio.sleep(physical_print_time)
                return (True, "completed")

            elif status in ("cancelled", "failed", "aborted"):
                return (False, status)

            elif status == "unknown":
                # Job might have completed and been removed from queue
                logger.info(
                    f"CUPS job {cups_job_id} not in queue, assuming completed"
                )
                await asyncio.sleep(physical_print_time)
                return (True, "completed")

        # Timeout
        logger.warning(f"CUPS job {cups_job_id} timed out after {timeout_seconds}s")
        return (False, "timeout")
