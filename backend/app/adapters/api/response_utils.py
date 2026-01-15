"""Utilities for mapping UseCaseResult to HTTP responses."""

from dataclasses import asdict, is_dataclass
from typing import Any, Callable, Dict, Optional, TypeVar

from fastapi import HTTPException

from app.application.use_cases.base import UseCaseResult

T = TypeVar("T")

# Error code to HTTP status code mapping
ERROR_STATUS_MAP: Dict[str, int] = {
    # 400 Bad Request - Invalid input
    "INVALID_SESSION_ID": 400,
    "INVALID_JOB_ID": 400,
    "INVALID_INDEX": 400,
    "INVALID_COPIES": 400,
    "INVALID_PIN": 400,
    "INVALID_IMAGE": 400,
    "INVALID_LANGUAGE": 400,
    "INCOMPLETE_SESSION": 400,
    "NO_COMPOSITE": 400,
    "SESSION_NOT_COMPLETE": 400,
    "MISSING_PHOTOS": 400,
    # 401 Unauthorized
    "AUTHENTICATION_FAILED": 401,
    "INVALID_TOKEN": 401,
    "TOKEN_EXPIRED": 401,
    # 404 Not Found
    "SESSION_NOT_FOUND": 404,
    "JOB_NOT_FOUND": 404,
    "PHOTO_NOT_FOUND": 404,
    "FILE_NOT_FOUND": 404,
    # 409 Conflict - State conflicts
    "INVALID_STATE": 409,
    "PHOTO_EXISTS": 409,
    "JOB_ALREADY_COMPLETED": 409,
    "JOB_ALREADY_CANCELLED": 409,
    "CANNOT_ABANDON": 409,
    # 503 Service Unavailable - External service issues
    "PRINTER_OFFLINE": 503,
    "PRINTER_BUSY": 503,
    "PRINTER_PAPER_EMPTY": 503,
    "PRINTER_INK_EMPTY": 503,
    "PRINTER_DOOR_OPEN": 503,
    "CUPS_UNAVAILABLE": 503,
    "CUPS_REJECTED": 503,
    # 500 Internal Server Error (default for unknown)
    "PROCESSING_ERROR": 500,
    "STORAGE_ERROR": 500,
    "UNKNOWN_ERROR": 500,
}


def get_status_code(error_code: Optional[str]) -> int:
    """Get HTTP status code for an error code."""
    if not error_code:
        return 500
    return ERROR_STATUS_MAP.get(error_code, 500)


def to_dict(obj: Any) -> Any:
    """Convert object to dictionary, handling dataclasses and nested structures."""
    if obj is None:
        return None
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_dict(item) for item in obj]
    return obj


def handle_result(
    result: UseCaseResult[T],
    transform: Optional[Callable[[T], Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Convert UseCaseResult to API response dict.

    Args:
        result: The use case result
        transform: Optional function to transform the data to response dict

    Returns:
        Response dict with success and data fields

    Raises:
        HTTPException: On failure with appropriate status code
    """
    if result.success:
        data = result.data
        if transform and data is not None:
            data = transform(data)
        else:
            data = to_dict(data)
        return {"success": True, "data": data}

    # Handle failure
    status_code = get_status_code(result.error_code)
    raise HTTPException(
        status_code=status_code,
        detail={
            "code": result.error_code,
            "message": result.error_message,
        },
    )


def handle_result_raw(result: UseCaseResult[T]) -> T:
    """Get raw data from UseCaseResult or raise HTTPException.

    Use this when you need the raw data object (e.g., for file responses).

    Args:
        result: The use case result

    Returns:
        The raw data from the result

    Raises:
        HTTPException: On failure with appropriate status code
    """
    if result.success:
        return result.data

    status_code = get_status_code(result.error_code)
    raise HTTPException(
        status_code=status_code,
        detail={
            "code": result.error_code,
            "message": result.error_message,
        },
    )
