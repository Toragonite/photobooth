"""Domain exceptions."""


class DomainError(Exception):
    """Base class for domain errors."""


class InvalidPhotoError(DomainError):
    """Raised when photo validation fails."""


class SessionError(DomainError):
    """Raised for session-related errors."""


class PrintJobError(DomainError):
    """Raised for print job errors."""


class InvalidStateTransitionError(DomainError):
    """Raised when invalid state transition attempted."""
