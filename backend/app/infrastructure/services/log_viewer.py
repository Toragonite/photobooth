"""Log viewer service for reading system and application logs."""

import io
import logging
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional

from ...config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class LogSource(str, Enum):
    """Available log sources."""

    APP = "app"
    PRINT = "print"
    CUPS = "cups"
    SYSTEM = "system"


class LogLevel(str, Enum):
    """Log levels for filtering."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    ALL = "all"


@dataclass
class LogEntry:
    """Single log entry."""

    timestamp: Optional[datetime]
    level: str
    source: str
    message: str
    raw: str


@dataclass
class LogResult:
    """Result of log query."""

    entries: List[LogEntry]
    total_count: int
    has_more: bool
    source: str
    level_filter: str


class LogViewerService:
    """Service for reading and filtering logs."""

    def __init__(self):
        self.mock_mode = settings.debug
        self.log_file = Path(settings.log_file)

        # Log patterns for parsing
        self.log_pattern = re.compile(
            r"^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d{3})\s+-\s+(\S+)\s+-\s+(\S+)\s+-\s+(.*)$"
        )

    def get_logs(
        self,
        source: LogSource = LogSource.APP,
        level: LogLevel = LogLevel.ALL,
        lines: int = 100,
        search: Optional[str] = None,
        offset: int = 0,
    ) -> LogResult:
        """Get logs from specified source.

        Args:
            source: Log source (app, print, cups, system)
            level: Minimum log level to return
            lines: Number of lines to return
            search: Optional search term
            offset: Offset for pagination

        Returns:
            LogResult with entries and metadata
        """
        if source == LogSource.APP:
            return self._get_app_logs(level, lines, search, offset)
        elif source == LogSource.PRINT:
            return self._get_print_logs(level, lines, search, offset)
        elif source == LogSource.CUPS:
            return self._get_cups_logs(lines, search, offset)
        elif source == LogSource.SYSTEM:
            return self._get_system_logs(lines, search, offset)
        else:
            return LogResult(
                entries=[],
                total_count=0,
                has_more=False,
                source=source.value,
                level_filter=level.value,
            )

    def _get_app_logs(
        self,
        level: LogLevel,
        lines: int,
        search: Optional[str],
        offset: int,
    ) -> LogResult:
        """Get application logs from log file."""
        entries = []

        if not self.log_file.exists():
            logger.warning(f"Log file not found: {self.log_file}")
            return LogResult(
                entries=[],
                total_count=0,
                has_more=False,
                source=LogSource.APP.value,
                level_filter=level.value,
            )

        try:
            # Read log file
            with open(self.log_file, "r") as f:
                all_lines = f.readlines()

            # Parse and filter
            level_order = {
                LogLevel.DEBUG.value: 0,
                LogLevel.INFO.value: 1,
                LogLevel.WARNING.value: 2,
                LogLevel.ERROR.value: 3,
                LogLevel.CRITICAL.value: 4,
            }
            min_level = level_order.get(level.value, -1)

            for line in reversed(all_lines):
                line = line.strip()
                if not line:
                    continue

                entry = self._parse_log_line(line, LogSource.APP.value)

                # Level filter
                if level != LogLevel.ALL:
                    entry_level = level_order.get(entry.level.lower(), 0)
                    if entry_level < min_level:
                        continue

                # Search filter
                if search and search.lower() not in line.lower():
                    continue

                entries.append(entry)

            total_count = len(entries)

            # Apply pagination
            paginated = entries[offset : offset + lines]
            has_more = offset + lines < total_count

            return LogResult(
                entries=paginated,
                total_count=total_count,
                has_more=has_more,
                source=LogSource.APP.value,
                level_filter=level.value,
            )

        except Exception as e:
            logger.error(f"Error reading app logs: {e}")
            return LogResult(
                entries=[],
                total_count=0,
                has_more=False,
                source=LogSource.APP.value,
                level_filter=level.value,
            )

    def _get_print_logs(
        self,
        level: LogLevel,
        lines: int,
        search: Optional[str],
        offset: int,
    ) -> LogResult:
        """Get print-related logs (filtered from app logs)."""
        result = self._get_app_logs(LogLevel.ALL, lines * 10, None, 0)

        # Filter for print-related entries
        print_keywords = ["print", "cups", "printer", "job"]
        entries = []

        for entry in result.entries:
            is_print_related = any(
                kw in entry.message.lower() or kw in entry.source.lower()
                for kw in print_keywords
            )
            if is_print_related:
                if search and search.lower() not in entry.raw.lower():
                    continue
                entries.append(entry)

        total_count = len(entries)
        paginated = entries[offset : offset + lines]
        has_more = offset + lines < total_count

        return LogResult(
            entries=paginated,
            total_count=total_count,
            has_more=has_more,
            source=LogSource.PRINT.value,
            level_filter=level.value,
        )

    def _get_cups_logs(
        self,
        lines: int,
        search: Optional[str],
        offset: int,
    ) -> LogResult:
        """Get CUPS logs."""
        entries = []

        if self.mock_mode:
            # Return mock CUPS logs
            entries = [
                LogEntry(
                    timestamp=datetime.now(),
                    level="INFO",
                    source="cupsd",
                    message="Printer Canon_Selphy_CP1500 is idle",
                    raw="I [13/Jan/2026:00:00:00 +0200] Printer Canon_Selphy_CP1500 is idle",
                ),
            ]
        else:
            try:
                # Try to read from CUPS log file
                cups_log_paths = [
                    "/var/log/cups/error_log",
                    "/var/log/cups/access_log",
                ]

                for log_path in cups_log_paths:
                    if os.path.exists(log_path):
                        result = subprocess.run(
                            ["sudo", "tail", "-n", str(lines * 2), log_path],
                            capture_output=True,
                            text=True,
                            timeout=5,
                        )
                        if result.returncode == 0:
                            for line in result.stdout.splitlines():
                                if search and search.lower() not in line.lower():
                                    continue
                                entry = self._parse_cups_log_line(line)
                                entries.append(entry)

            except Exception as e:
                logger.error(f"Error reading CUPS logs: {e}")

        # Reverse to show most recent first
        entries.reverse()
        total_count = len(entries)
        paginated = entries[offset : offset + lines]
        has_more = offset + lines < total_count

        return LogResult(
            entries=paginated,
            total_count=total_count,
            has_more=has_more,
            source=LogSource.CUPS.value,
            level_filter=LogLevel.ALL.value,
        )

    def _get_system_logs(
        self,
        lines: int,
        search: Optional[str],
        offset: int,
    ) -> LogResult:
        """Get system logs via journalctl."""
        entries = []

        if self.mock_mode:
            # Return mock system logs
            entries = [
                LogEntry(
                    timestamp=datetime.now(),
                    level="INFO",
                    source="systemd",
                    message="Started PhotoBooth Backend Service",
                    raw="Jan 13 00:00:00 photobooth systemd[1]: Started PhotoBooth Backend Service",
                ),
            ]
        else:
            try:
                # Use journalctl to get system logs
                cmd = [
                    "journalctl",
                    "-u",
                    "photobooth*",
                    "-n",
                    str(lines * 2),
                    "--no-pager",
                    "-o",
                    "short-iso",
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0:
                    for line in result.stdout.splitlines():
                        if search and search.lower() not in line.lower():
                            continue
                        entry = self._parse_journal_line(line)
                        if entry:
                            entries.append(entry)

            except Exception as e:
                logger.error(f"Error reading system logs: {e}")

        # Reverse to show most recent first
        entries.reverse()
        total_count = len(entries)
        paginated = entries[offset : offset + lines]
        has_more = offset + lines < total_count

        return LogResult(
            entries=paginated,
            total_count=total_count,
            has_more=has_more,
            source=LogSource.SYSTEM.value,
            level_filter=LogLevel.ALL.value,
        )

    def _parse_log_line(self, line: str, source: str) -> LogEntry:
        """Parse a standard Python logging line."""
        match = self.log_pattern.match(line)
        if match:
            timestamp_str, logger_name, level, message = match.groups()
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
            except ValueError:
                timestamp = None

            return LogEntry(
                timestamp=timestamp,
                level=level.upper(),
                source=logger_name,
                message=message,
                raw=line,
            )

        return LogEntry(
            timestamp=None,
            level="INFO",
            source=source,
            message=line,
            raw=line,
        )

    def _parse_cups_log_line(self, line: str) -> LogEntry:
        """Parse a CUPS log line."""
        # CUPS format: E [date:time location] message
        # or: I [date:time location] message
        level_map = {"E": "ERROR", "W": "WARNING", "I": "INFO", "D": "DEBUG"}
        level = "INFO"

        if line and line[0] in level_map:
            level = level_map[line[0]]

        return LogEntry(
            timestamp=None,  # Could parse CUPS timestamp format
            level=level,
            source="cups",
            message=line,
            raw=line,
        )

    def _parse_journal_line(self, line: str) -> Optional[LogEntry]:
        """Parse a journalctl line."""
        if not line or line.startswith("--"):
            return None

        # journalctl short-iso format: 2026-01-13T00:00:00+0200 hostname unit[pid]: message
        parts = line.split(" ", 3)
        if len(parts) < 4:
            return LogEntry(
                timestamp=None,
                level="INFO",
                source="system",
                message=line,
                raw=line,
            )

        try:
            timestamp = datetime.fromisoformat(parts[0].replace("+0200", ""))
        except ValueError:
            timestamp = None

        return LogEntry(
            timestamp=timestamp,
            level="INFO",
            source=parts[2].split("[")[0] if "[" in parts[2] else parts[2],
            message=parts[3] if len(parts) > 3 else line,
            raw=line,
        )

    def download_logs(
        self,
        source: LogSource = LogSource.APP,
        hours: int = 24,
    ) -> bytes:
        """Download logs as a file.

        Args:
            source: Log source
            hours: Number of hours of logs to include

        Returns:
            Log content as bytes
        """
        result = self.get_logs(source=source, level=LogLevel.ALL, lines=10000)

        output = io.BytesIO()
        output.write(f"# PhotoBooth Logs - {source.value}\n".encode())
        output.write(f"# Generated: {datetime.now().isoformat()}\n".encode())
        output.write(f"# Total entries: {result.total_count}\n\n".encode())

        for entry in result.entries:
            output.write(f"{entry.raw}\n".encode())

        return output.getvalue()
