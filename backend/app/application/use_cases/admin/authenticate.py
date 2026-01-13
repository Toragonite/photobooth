"""Admin authentication use case."""

import hashlib
import os
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.application.dto.admin_dto import LoginResponse
from app.application.use_cases.base import UseCase, UseCaseResult


@dataclass
class AuthenticateInput:
    """Input for authentication."""
    pin: str


class AuthenticateUseCase(UseCase[LoginResponse]):
    """Use case for admin authentication."""

    def __init__(self, admin_pin_hash: str, token_expiry_hours: int = 24):
        self._admin_pin_hash = admin_pin_hash
        self._token_expiry_hours = token_expiry_hours

    async def execute(self, input_data: AuthenticateInput) -> UseCaseResult[LoginResponse]:
        if not input_data.pin or len(input_data.pin) < 4:
            return UseCaseResult.fail("INVALID_PIN", "PIN must be at least 4 digits")

        # Hash the provided PIN and compare
        pin_hash = hashlib.sha256(input_data.pin.encode()).hexdigest()

        if pin_hash != self._admin_pin_hash:
            return UseCaseResult.fail("INVALID_PIN", "Invalid PIN")

        # Generate a simple token
        token = hashlib.sha256(
            f"{input_data.pin}:{datetime.now().isoformat()}:{os.urandom(16).hex()}".encode()
        ).hexdigest()

        expires_at = datetime.now() + timedelta(hours=self._token_expiry_hours)

        return UseCaseResult.ok(
            LoginResponse(token=token, expires_at=expires_at)
        )
