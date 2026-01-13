"""Admin use cases."""

from app.application.use_cases.admin.authenticate import AuthenticateUseCase
from app.application.use_cases.admin.get_logs import GetLogsUseCase
from app.application.use_cases.admin.get_print_history import GetPrintHistoryUseCase
from app.application.use_cases.admin.get_system_status import GetSystemStatusUseCase
from app.application.use_cases.admin.reboot_system import RebootSystemUseCase
from app.application.use_cases.admin.test_print import TestPrintUseCase

__all__ = [
    "AuthenticateUseCase",
    "GetSystemStatusUseCase",
    "GetPrintHistoryUseCase",
    "GetLogsUseCase",
    "TestPrintUseCase",
    "RebootSystemUseCase",
]
