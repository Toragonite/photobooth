"""Admin-related Data Transfer Objects."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class LoginRequest:
    """Request to login to the admin dashboard."""
    pin: str


@dataclass
class LoginResponse:
    """Response after successful login."""
    token: str
    expires_at: datetime


@dataclass
class SystemStatusDTO:
    """Data transfer object for system status."""
    overall_health: str
    printer: Dict[str, Any] = field(default_factory=dict)
    storage: Dict[str, Any] = field(default_factory=dict)
    activity: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PrintHistoryDTO:
    """Data transfer object for print history."""
    jobs: List[Dict[str, Any]] = field(default_factory=list)
    total: int = 0
    page: int = 1
    per_page: int = 20


@dataclass
class LogsDTO:
    """Data transfer object for system logs."""
    entries: List[Dict[str, Any]] = field(default_factory=list)
    source: str = "all"
    total: int = 0
