"""Admin use cases."""

from app.application.use_cases.admin.authenticate import (AuthenticateInput,
                                                          AuthenticateUseCase)
from app.application.use_cases.admin.get_logs import (GetLogsInput,
                                                      GetLogsUseCase)
from app.application.use_cases.admin.get_print_history import (
    GetPrintHistoryInput, GetPrintHistoryUseCase)
from app.application.use_cases.admin.get_system_status import \
    GetSystemStatusUseCase
from app.application.use_cases.admin.reboot_system import (RebootSystemInput,
                                                           RebootSystemUseCase)
from app.application.use_cases.admin.test_print import (TestPrintInput,
                                                        TestPrintUseCase)

__all__ = [
    "AuthenticateUseCase",
    "AuthenticateInput",
    "GetSystemStatusUseCase",
    "GetPrintHistoryUseCase",
    "GetPrintHistoryInput",
    "GetLogsUseCase",
    "GetLogsInput",
    "TestPrintUseCase",
    "TestPrintInput",
    "RebootSystemUseCase",
    "RebootSystemInput",
]
