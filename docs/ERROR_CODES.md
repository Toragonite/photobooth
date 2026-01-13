# Error Codes Reference

> Centralized error codes for PhotoBooth application

---

## Overview

All errors follow a consistent format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {}  // Optional additional context
  }
}
```

---

## Error Code Categories

| Prefix | Category | HTTP Status Range |
|--------|----------|-------------------|
| `AUTH_` | Authentication | 401, 403 |
| `SESSION_` | Session management | 400, 404, 409 |
| `PHOTO_` | Photo capture | 400, 404, 413 |
| `PRINT_` | Print operations | 400, 404, 409, 503 |
| `PRINTER_` | Printer hardware | 503 |
| `STORAGE_` | Storage/disk | 500, 507 |
| `SYSTEM_` | System errors | 500, 503 |
| `VALIDATION_` | Input validation | 400 |
| `RATE_` | Rate limiting | 429 |

---

## Authentication Errors

### AUTH_REQUIRED
**HTTP Status:** 401 Unauthorized

**Description:** Request requires authentication but no token provided.

**Response:**
```json
{
  "error": {
    "code": "AUTH_REQUIRED",
    "message": "Authentication required"
  }
}
```

**Resolution:** Include `Authorization: Bearer <token>` header.

---

### AUTH_INVALID_TOKEN
**HTTP Status:** 401 Unauthorized

**Description:** Token is malformed or signature invalid.

**Response:**
```json
{
  "error": {
    "code": "AUTH_INVALID_TOKEN",
    "message": "Invalid authentication token"
  }
}
```

**Resolution:** Obtain new token via login.

---

### AUTH_TOKEN_EXPIRED
**HTTP Status:** 401 Unauthorized

**Description:** Token has expired (30 minute lifetime).

**Response:**
```json
{
  "error": {
    "code": "AUTH_TOKEN_EXPIRED",
    "message": "Authentication token has expired",
    "details": {
      "expired_at": "2024-01-13T10:30:00Z"
    }
  }
}
```

**Resolution:** Re-authenticate to obtain new token.

---

### AUTH_INVALID_PIN
**HTTP Status:** 401 Unauthorized

**Description:** Login PIN is incorrect.

**Response:**
```json
{
  "error": {
    "code": "AUTH_INVALID_PIN",
    "message": "Invalid PIN",
    "details": {
      "attempts_remaining": 3
    }
  }
}
```

**Resolution:** Enter correct PIN.

---

### AUTH_LOCKED_OUT
**HTTP Status:** 429 Too Many Requests

**Description:** Too many failed login attempts.

**Response:**
```json
{
  "error": {
    "code": "AUTH_LOCKED_OUT",
    "message": "Account locked due to too many failed attempts",
    "details": {
      "locked_until": "2024-01-13T10:35:00Z",
      "remaining_seconds": 300
    }
  }
}
```

**Resolution:** Wait for lockout period to expire.

---

## Session Errors

### SESSION_NOT_FOUND
**HTTP Status:** 404 Not Found

**Description:** Session ID does not exist.

**Response:**
```json
{
  "error": {
    "code": "SESSION_NOT_FOUND",
    "message": "Session not found",
    "details": {
      "session_id": "550e8400-e29b-41d4-a716-446655440000"
    }
  }
}
```

**Resolution:** Create new session or verify session ID.

---

### SESSION_EXPIRED
**HTTP Status:** 410 Gone

**Description:** Session has been abandoned or expired.

**Response:**
```json
{
  "error": {
    "code": "SESSION_EXPIRED",
    "message": "Session has expired or been abandoned",
    "details": {
      "session_id": "...",
      "status": "ABANDONED"
    }
  }
}
```

**Resolution:** Start new session.

---

### SESSION_FULL
**HTTP Status:** 409 Conflict

**Description:** Session already has 4 photos.

**Response:**
```json
{
  "error": {
    "code": "SESSION_FULL",
    "message": "Session already has maximum photos",
    "details": {
      "photo_count": 4,
      "max_photos": 4
    }
  }
}
```

**Resolution:** Use PUT to replace existing photos.

---

### SESSION_INCOMPLETE
**HTTP Status:** 400 Bad Request

**Description:** Operation requires 4 photos but session has fewer.

**Response:**
```json
{
  "error": {
    "code": "SESSION_INCOMPLETE",
    "message": "Session requires 4 photos for this operation",
    "details": {
      "photo_count": 2,
      "required": 4
    }
  }
}
```

**Resolution:** Capture remaining photos.

---

## Photo Errors

### PHOTO_NOT_FOUND
**HTTP Status:** 404 Not Found

**Description:** Photo ID does not exist.

**Response:**
```json
{
  "error": {
    "code": "PHOTO_NOT_FOUND",
    "message": "Photo not found",
    "details": {
      "photo_id": "photo-123"
    }
  }
}
```

---

### PHOTO_INVALID_FORMAT
**HTTP Status:** 400 Bad Request

**Description:** Uploaded image is not a supported format.

**Response:**
```json
{
  "error": {
    "code": "PHOTO_INVALID_FORMAT",
    "message": "Invalid image format. Supported: JPEG, PNG",
    "details": {
      "received_type": "image/gif",
      "supported_types": ["image/jpeg", "image/png"]
    }
  }
}
```

---

### PHOTO_TOO_LARGE
**HTTP Status:** 413 Payload Too Large

**Description:** Uploaded image exceeds size limit.

**Response:**
```json
{
  "error": {
    "code": "PHOTO_TOO_LARGE",
    "message": "Image file too large",
    "details": {
      "size_bytes": 6000000,
      "max_bytes": 5000000
    }
  }
}
```

---

### PHOTO_TOO_SMALL
**HTTP Status:** 400 Bad Request

**Description:** Image resolution too low.

**Response:**
```json
{
  "error": {
    "code": "PHOTO_TOO_SMALL",
    "message": "Image resolution too low",
    "details": {
      "width": 320,
      "height": 240,
      "min_width": 640,
      "min_height": 480
    }
  }
}
```

---

### PHOTO_PROCESSING_FAILED
**HTTP Status:** 500 Internal Server Error

**Description:** Failed to process/save uploaded image.

**Response:**
```json
{
  "error": {
    "code": "PHOTO_PROCESSING_FAILED",
    "message": "Failed to process image",
    "details": {
      "reason": "Unable to decode image data"
    }
  }
}
```

---

## Print Errors

### PRINT_JOB_NOT_FOUND
**HTTP Status:** 404 Not Found

**Description:** Print job ID does not exist.

**Response:**
```json
{
  "error": {
    "code": "PRINT_JOB_NOT_FOUND",
    "message": "Print job not found",
    "details": {
      "job_id": "job-123"
    }
  }
}
```

---

### PRINT_NO_COMPOSITE
**HTTP Status:** 400 Bad Request

**Description:** Cannot print - no composite image generated.

**Response:**
```json
{
  "error": {
    "code": "PRINT_NO_COMPOSITE",
    "message": "No composite image available for printing",
    "details": {
      "session_id": "..."
    }
  }
}
```

**Resolution:** Generate composite first.

---

### PRINT_INVALID_COPIES
**HTTP Status:** 400 Bad Request

**Description:** Copies count out of allowed range.

**Response:**
```json
{
  "error": {
    "code": "PRINT_INVALID_COPIES",
    "message": "Invalid number of copies",
    "details": {
      "requested": 5,
      "min": 1,
      "max": 3
    }
  }
}
```

---

### PRINT_JOB_COMPLETED
**HTTP Status:** 409 Conflict

**Description:** Cannot modify/cancel - job already completed.

**Response:**
```json
{
  "error": {
    "code": "PRINT_JOB_COMPLETED",
    "message": "Print job has already completed",
    "details": {
      "job_id": "job-123",
      "completed_at": "2024-01-13T10:30:00Z"
    }
  }
}
```

---

### PRINT_JOB_NOT_RETRIABLE
**HTTP Status:** 409 Conflict

**Description:** Job is not in a state that allows retry.

**Response:**
```json
{
  "error": {
    "code": "PRINT_JOB_NOT_RETRIABLE",
    "message": "Print job cannot be retried in current state",
    "details": {
      "job_id": "job-123",
      "status": "PRINTING"
    }
  }
}
```

---

## Printer Hardware Errors

### PRINTER_OFFLINE
**HTTP Status:** 503 Service Unavailable

**Retryable:** Yes

**Description:** Printer is not responding or powered off.

**Response:**
```json
{
  "error": {
    "code": "PRINTER_OFFLINE",
    "message": "Printer is offline",
    "details": {
      "printer_name": "Canon_Selphy_CP1500",
      "last_seen": "2024-01-13T10:25:00Z"
    }
  }
}
```

**Resolution:** Check printer power and USB connection.

---

### PRINTER_BUSY
**HTTP Status:** 503 Service Unavailable

**Retryable:** Yes

**Description:** Printer is busy with another job.

**Response:**
```json
{
  "error": {
    "code": "PRINTER_BUSY",
    "message": "Printer is busy",
    "details": {
      "current_job_id": "job-456"
    }
  }
}
```

**Resolution:** Wait for current job to complete.

---

### PRINTER_PAPER_EMPTY
**HTTP Status:** 503 Service Unavailable

**Retryable:** Yes

**Description:** Printer paper tray is empty.

**Response:**
```json
{
  "error": {
    "code": "PRINTER_PAPER_EMPTY",
    "message": "Printer is out of paper",
    "details": {
      "paper_size": "4x6"
    }
  }
}
```

**Resolution:** Load paper into printer.

---

### PRINTER_INK_EMPTY
**HTTP Status:** 503 Service Unavailable

**Retryable:** Yes

**Description:** Printer ink/ribbon is depleted.

**Response:**
```json
{
  "error": {
    "code": "PRINTER_INK_EMPTY",
    "message": "Printer is out of ink"
  }
}
```

**Resolution:** Replace ink ribbon cartridge.

---

### PRINTER_PAPER_JAM
**HTTP Status:** 503 Service Unavailable

**Retryable:** No (requires physical intervention)

**Description:** Paper is jammed in printer.

**Response:**
```json
{
  "error": {
    "code": "PRINTER_PAPER_JAM",
    "message": "Paper jam detected"
  }
}
```

**Resolution:** Clear paper jam and restart print.

---

### PRINTER_DOOR_OPEN
**HTTP Status:** 503 Service Unavailable

**Retryable:** Yes

**Description:** Printer cover/door is open.

**Response:**
```json
{
  "error": {
    "code": "PRINTER_DOOR_OPEN",
    "message": "Printer door is open"
  }
}
```

**Resolution:** Close printer door.

---

## CUPS Errors

### CUPS_UNAVAILABLE
**HTTP Status:** 503 Service Unavailable

**Retryable:** Yes

**Description:** CUPS service is not running.

**Response:**
```json
{
  "error": {
    "code": "CUPS_UNAVAILABLE",
    "message": "Print service is unavailable"
  }
}
```

**Resolution:** Restart CUPS service.

---

### CUPS_REJECTED
**HTTP Status:** 500 Internal Server Error

**Retryable:** Yes

**Description:** CUPS rejected the print job.

**Response:**
```json
{
  "error": {
    "code": "CUPS_REJECTED",
    "message": "Print job was rejected",
    "details": {
      "cups_message": "client-error-document-format-not-supported"
    }
  }
}
```

---

## Storage Errors

### STORAGE_FULL
**HTTP Status:** 507 Insufficient Storage

**Retryable:** No

**Description:** Disk space critically low.

**Response:**
```json
{
  "error": {
    "code": "STORAGE_FULL",
    "message": "Storage is full",
    "details": {
      "free_bytes": 1000000,
      "required_bytes": 5000000
    }
  }
}
```

**Resolution:** Clean old data via admin dashboard.

---

### STORAGE_WRITE_FAILED
**HTTP Status:** 500 Internal Server Error

**Description:** Failed to write file to disk.

**Response:**
```json
{
  "error": {
    "code": "STORAGE_WRITE_FAILED",
    "message": "Failed to save file",
    "details": {
      "reason": "Permission denied"
    }
  }
}
```

---

### STORAGE_READ_FAILED
**HTTP Status:** 500 Internal Server Error

**Description:** Failed to read file from disk.

**Response:**
```json
{
  "error": {
    "code": "STORAGE_READ_FAILED",
    "message": "Failed to read file",
    "details": {
      "path": "/data/photos/..."
    }
  }
}
```

---

## System Errors

### SYSTEM_ERROR
**HTTP Status:** 500 Internal Server Error

**Description:** Generic internal server error.

**Response:**
```json
{
  "error": {
    "code": "SYSTEM_ERROR",
    "message": "Internal server error",
    "details": {
      "request_id": "req-123"
    }
  }
}
```

---

### SYSTEM_OVERLOADED
**HTTP Status:** 503 Service Unavailable

**Retryable:** Yes

**Description:** System resources exhausted.

**Response:**
```json
{
  "error": {
    "code": "SYSTEM_OVERLOADED",
    "message": "System is overloaded, please try again",
    "details": {
      "cpu_percent": 95,
      "memory_percent": 92
    }
  }
}
```

---

### SYSTEM_MAINTENANCE
**HTTP Status:** 503 Service Unavailable

**Description:** System is under maintenance.

**Response:**
```json
{
  "error": {
    "code": "SYSTEM_MAINTENANCE",
    "message": "System is under maintenance",
    "details": {
      "estimated_end": "2024-01-13T11:00:00Z"
    }
  }
}
```

---

## Validation Errors

### VALIDATION_FAILED
**HTTP Status:** 400 Bad Request

**Description:** Request body validation failed.

**Response:**
```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Validation failed",
    "details": {
      "errors": [
        {"field": "copies", "message": "Must be between 1 and 3"},
        {"field": "session_id", "message": "Required field"}
      ]
    }
  }
}
```

---

### VALIDATION_INVALID_UUID
**HTTP Status:** 400 Bad Request

**Description:** Provided ID is not a valid UUID.

**Response:**
```json
{
  "error": {
    "code": "VALIDATION_INVALID_UUID",
    "message": "Invalid ID format",
    "details": {
      "field": "session_id",
      "value": "not-a-uuid"
    }
  }
}
```

---

## Rate Limiting

### RATE_LIMIT_EXCEEDED
**HTTP Status:** 429 Too Many Requests

**Description:** Request rate limit exceeded.

**Response:**
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "details": {
      "limit": 60,
      "window_seconds": 60,
      "retry_after_seconds": 30
    }
  }
}
```

**Headers:**
```
Retry-After: 30
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1705142400
```

---

## Error Handling in Code

### Python Backend

```python
from enum import Enum
from dataclasses import dataclass

class ErrorCode(str, Enum):
    # Auth
    AUTH_REQUIRED = "AUTH_REQUIRED"
    AUTH_INVALID_TOKEN = "AUTH_INVALID_TOKEN"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_INVALID_PIN = "AUTH_INVALID_PIN"
    AUTH_LOCKED_OUT = "AUTH_LOCKED_OUT"

    # Session
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    SESSION_FULL = "SESSION_FULL"
    SESSION_INCOMPLETE = "SESSION_INCOMPLETE"

    # Photo
    PHOTO_NOT_FOUND = "PHOTO_NOT_FOUND"
    PHOTO_INVALID_FORMAT = "PHOTO_INVALID_FORMAT"
    PHOTO_TOO_LARGE = "PHOTO_TOO_LARGE"
    PHOTO_TOO_SMALL = "PHOTO_TOO_SMALL"

    # Print
    PRINT_JOB_NOT_FOUND = "PRINT_JOB_NOT_FOUND"
    PRINT_NO_COMPOSITE = "PRINT_NO_COMPOSITE"
    PRINT_JOB_COMPLETED = "PRINT_JOB_COMPLETED"

    # Printer
    PRINTER_OFFLINE = "PRINTER_OFFLINE"
    PRINTER_BUSY = "PRINTER_BUSY"
    PRINTER_PAPER_EMPTY = "PRINTER_PAPER_EMPTY"
    PRINTER_INK_EMPTY = "PRINTER_INK_EMPTY"

    # System
    SYSTEM_ERROR = "SYSTEM_ERROR"
    STORAGE_FULL = "STORAGE_FULL"

@dataclass
class AppError(Exception):
    code: ErrorCode
    message: str
    details: dict = None
    http_status: int = 500

# Retryable errors for auto-retry logic
RETRYABLE_ERRORS = {
    ErrorCode.PRINTER_OFFLINE,
    ErrorCode.PRINTER_BUSY,
    ErrorCode.PRINTER_PAPER_EMPTY,
    ErrorCode.PRINTER_INK_EMPTY,
    ErrorCode.PRINTER_DOOR_OPEN,
    ErrorCode.CUPS_UNAVAILABLE,
    ErrorCode.CUPS_REJECTED,
}
```

### TypeScript Frontend

```typescript
enum ErrorCode {
  // Auth
  AUTH_REQUIRED = 'AUTH_REQUIRED',
  AUTH_INVALID_TOKEN = 'AUTH_INVALID_TOKEN',
  AUTH_TOKEN_EXPIRED = 'AUTH_TOKEN_EXPIRED',

  // Session
  SESSION_NOT_FOUND = 'SESSION_NOT_FOUND',
  SESSION_FULL = 'SESSION_FULL',

  // Print
  PRINTER_OFFLINE = 'PRINTER_OFFLINE',
  // ...
}

interface ApiError {
  code: ErrorCode;
  message: string;
  details?: Record<string, unknown>;
}

// Error messages for UI (bilingual)
const ERROR_MESSAGES: Record<ErrorCode, { ko: string; en: string }> = {
  [ErrorCode.PRINTER_OFFLINE]: {
    ko: '프린터가 오프라인입니다',
    en: 'Printer is offline',
  },
  [ErrorCode.PRINTER_PAPER_EMPTY]: {
    ko: '용지가 부족합니다',
    en: 'Printer is out of paper',
  },
  // ...
};
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
