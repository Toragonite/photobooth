# API Specification

> Complete REST API documentation for PhotoBooth backend

---

## Base URL

```
http://photobooth.local/api
```

---

## Authentication

### Public Endpoints (No Auth Required)
- All `/api/session/*` endpoints
- All `/api/print/*` endpoints (user-facing)
- `GET /api/health`
- `GET /api/settings/public`

### Admin Endpoints (JWT Required)
- All `/api/admin/*` endpoints

**Header Format:**
```
Authorization: Bearer <jwt_token>
```

**Token Expiry:** 30 minutes

---

## Response Format

### Success Response
```json
{
  "success": true,
  "data": { ... }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message"
  }
}
```

---

## Endpoints

### Session Management

#### POST /api/session
Create a new photo session.

**Request Body:**
```json
{
  "language": "ko"  // "ko" | "en", optional, default from settings
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "language": "ko",
    "status": "ACTIVE",
    "created_at": "2024-01-13T10:30:00Z",
    "photos": [],
    "photo_count": 0,
    "max_photos": 4
  }
}
```

---

#### GET /api/session/{session_id}
Get session details.

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "language": "ko",
    "status": "ACTIVE",
    "created_at": "2024-01-13T10:30:00Z",
    "photos": [
      {
        "id": "photo-1",
        "index": 0,
        "thumbnail_url": "/api/photos/photo-1/thumbnail",
        "captured_at": "2024-01-13T10:31:00Z"
      }
    ],
    "photo_count": 1,
    "max_photos": 4,
    "composite_url": null
  }
}
```

**Errors:**
- `404` - Session not found

---

#### PATCH /api/session/{session_id}/language
Change session language.

**Request Body:**
```json
{
  "language": "en"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "session_id": "...",
    "language": "en"
  }
}
```

---

#### DELETE /api/session/{session_id}
Abandon/delete a session.

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "session_id": "...",
    "status": "ABANDONED"
  }
}
```

---

### Photo Capture

#### POST /api/session/{session_id}/photos
Upload a captured photo.

**Request:** `multipart/form-data`
```
photo: <binary image data>
index: 0  // 0-3, which photo slot
```

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "photo_id": "photo-550e8400",
    "index": 0,
    "thumbnail_url": "/api/photos/photo-550e8400/thumbnail",
    "captured_at": "2024-01-13T10:31:00Z",
    "session_photo_count": 1
  }
}
```

**Errors:**
- `400` - Invalid image format or size
- `404` - Session not found
- `409` - Photo slot already filled (use PUT to replace)

---

#### PUT /api/session/{session_id}/photos/{index}
Replace/retake a photo at specific index.

**Request:** `multipart/form-data`
```
photo: <binary image data>
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "photo_id": "photo-new-id",
    "index": 0,
    "thumbnail_url": "/api/photos/photo-new-id/thumbnail",
    "captured_at": "2024-01-13T10:35:00Z",
    "replaced_photo_id": "photo-old-id"
  }
}
```

---

#### GET /api/photos/{photo_id}/thumbnail
Get photo thumbnail (300px).

**Response:** `200 OK`
- Content-Type: `image/jpeg`
- Body: Binary image data

---

#### GET /api/photos/{photo_id}/full
Get full resolution photo.

**Response:** `200 OK`
- Content-Type: `image/jpeg`
- Body: Binary image data

---

### Composite Generation

#### POST /api/session/{session_id}/composite
Generate composite image from 4 photos.

**Request Body:**
```json
{
  "include_logo": true,
  "include_date": true
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "composite_id": "comp-550e8400",
    "composite_url": "/api/composite/comp-550e8400",
    "thumbnail_url": "/api/composite/comp-550e8400/thumbnail",
    "dimensions": {
      "width": 1200,
      "height": 1800,
      "dpi": 300
    }
  }
}
```

**Errors:**
- `400` - Session doesn't have 4 photos
- `404` - Session not found
- `500` - Image processing failed

---

#### GET /api/composite/{composite_id}
Get composite image.

**Response:** `200 OK`
- Content-Type: `image/jpeg`
- Body: Binary image data

---

### Print Management

#### POST /api/print
Submit a print job.

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "copies": 1
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "job_id": "job-550e8400",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "PENDING",
    "copies": 1,
    "created_at": "2024-01-13T10:35:00Z"
  }
}
```

**Errors:**
- `400` - Invalid copies count (must be 1-3)
- `404` - Session not found or no composite
- `503` - Printer offline

---

#### GET /api/print/{job_id}
Get print job status.

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "job_id": "job-550e8400",
    "session_id": "550e8400-...",
    "status": "PRINTING",
    "copies": 1,
    "progress": 75,
    "created_at": "2024-01-13T10:35:00Z",
    "started_at": "2024-01-13T10:35:05Z",
    "completed_at": null,
    "error": null,
    "retry_count": 0
  }
}
```

**Status Values:**
- `PENDING` - Waiting in queue
- `PROCESSING` - Preparing for print
- `PRINTING` - Currently printing
- `COMPLETED` - Successfully printed
- `FAILED` - Print failed (see error)
- `CANCELLED` - Cancelled by user
- `RETRY_PENDING` - Waiting for retry

---

#### POST /api/print/{job_id}/retry
Manually retry a failed print job.

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "job_id": "job-550e8400",
    "status": "PENDING",
    "retry_count": 0,
    "message": "Job queued for retry"
  }
}
```

**Errors:**
- `404` - Job not found
- `409` - Job not in retriable state

---

#### POST /api/print/{job_id}/cancel
Cancel a print job.

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "job_id": "job-550e8400",
    "status": "CANCELLED",
    "previous_status": "PENDING"
  }
}
```

**Errors:**
- `404` - Job not found
- `409` - Job already completed

---

### Settings (Public)

#### GET /api/settings/public
Get public settings for UI.

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "default_language": "ko",
    "countdown_options": [3, 5, 8, 10],
    "default_countdown": 5,
    "max_copies": 3,
    "sound_enabled": true,
    "logo_enabled": true,
    "date_format": "YYYY.MM.DD"
  }
}
```

---

### Health Check

#### GET /api/health
Simple health check.

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2024-01-13T10:30:00Z"
}
```

**Response:** `503 Service Unavailable`
```json
{
  "status": "unhealthy",
  "timestamp": "2024-01-13T10:30:00Z"
}
```

---

#### GET /api/health/detailed
Detailed health check (requires admin auth).

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-13T10:30:00Z",
    "uptime_seconds": 86400,
    "components": {
      "database": {
        "status": "healthy",
        "latency_ms": 5
      },
      "printer": {
        "status": "healthy",
        "name": "Canon_Selphy_CP1500",
        "state": "idle"
      },
      "storage": {
        "status": "healthy",
        "percent_used": 45.2,
        "free_gb": 140.3
      },
      "cups": {
        "status": "healthy"
      },
      "wifi": {
        "status": "healthy",
        "clients": 2
      },
      "system": {
        "status": "healthy",
        "cpu_temp_celsius": 48,
        "memory_percent": 26
      }
    }
  }
}
```

---

## Admin Endpoints

### Authentication

#### POST /api/admin/login
Authenticate admin.

**Request Body:**
```json
{
  "pin": "1234"  // Example - use your configured ADMIN_PIN
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_at": "2024-01-13T11:00:00Z"
  }
}
```

**Errors:**
- `401` - Invalid PIN
- `429` - Too many attempts (locked out)

---

#### POST /api/admin/logout
Invalidate token.

**Response:** `200 OK`
```json
{
  "success": true
}
```

---

### System Status

#### GET /api/admin/status
Get full system status.

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "timestamp": "2024-01-13T10:30:00Z",
    "overall_health": "healthy",
    "warnings": [],
    "errors": [],
    "printer": {
      "name": "Canon_Selphy_CP1500",
      "model": "Selphy CP1500",
      "status": "idle",
      "health": "healthy",
      "queue_count": 0,
      "today_completed": 15,
      "today_failed": 0
    },
    "storage": {
      "total_bytes": 256000000000,
      "used_bytes": 45200000000,
      "free_bytes": 210800000000,
      "percent_used": 17.7,
      "health": "healthy",
      "session_count": 1234
    },
    "system": {
      "cpu_temp_celsius": 48,
      "memory_total_bytes": 8000000000,
      "memory_used_bytes": 2100000000,
      "memory_percent": 26,
      "uptime_seconds": 302400,
      "health": "healthy"
    },
    "services": [
      {"name": "Backend API", "status": "running"},
      {"name": "CUPS Service", "status": "running"},
      {"name": "Database", "status": "running", "details": "SQLite"},
      {"name": "Wi-Fi AP", "status": "running", "details": "3 clients"}
    ],
    "activity": {
      "date": "2024-01-13",
      "sessions_started": 23,
      "sessions_completed": 21,
      "sessions_abandoned": 2,
      "prints_total": 21,
      "prints_success": 19,
      "prints_failed": 2,
      "success_rate": 90.5
    }
  }
}
```

---

### Print History

#### GET /api/admin/print-history
Get paginated print history.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| page | int | 1 | Page number |
| limit | int | 20 | Items per page (max 100) |
| status | string | all | Filter: all, completed, failed, cancelled |
| from_date | string | -7d | ISO date or relative |
| to_date | string | now | ISO date or relative |
| search | string | | Search session ID |

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "jobs": [
      {
        "id": "job-123",
        "session_id": "sess-456",
        "status": "COMPLETED",
        "copies": 1,
        "created_at": "2024-01-13T10:30:00Z",
        "completed_at": "2024-01-13T10:31:15Z",
        "duration_seconds": 75,
        "composite_thumbnail_url": "/api/composite/comp-789/thumbnail"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 156,
      "total_pages": 8
    },
    "summary": {
      "total": 156,
      "completed": 149,
      "failed": 5,
      "cancelled": 2,
      "success_rate": 95.5
    }
  }
}
```

---

#### GET /api/admin/print-history/{job_id}
Get detailed job info with timeline.

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "job": {
      "id": "job-123",
      "session_id": "sess-456",
      "status": "FAILED",
      "copies": 2,
      "created_at": "2024-01-13T10:30:00Z",
      "error_code": "PRINTER_OFFLINE",
      "error_message": "Printer is offline",
      "retry_count": 3,
      "cups_job_id": 456
    },
    "session": {
      "id": "sess-456",
      "composite_url": "/api/composite/comp-789"
    },
    "timeline": [
      {"timestamp": "2024-01-13T10:30:00Z", "event": "Job created"},
      {"timestamp": "2024-01-13T10:30:01Z", "event": "Submitted to CUPS"},
      {"timestamp": "2024-01-13T10:30:03Z", "event": "Printer offline detected"},
      {"timestamp": "2024-01-13T10:30:06Z", "event": "Retry 1 scheduled"},
      {"timestamp": "2024-01-13T10:30:09Z", "event": "Retry 1 failed"},
      {"timestamp": "2024-01-13T10:30:17Z", "event": "Retry 2 failed"},
      {"timestamp": "2024-01-13T10:30:25Z", "event": "Retry 3 failed"},
      {"timestamp": "2024-01-13T10:30:25Z", "event": "Job failed - max retries"}
    ]
  }
}
```

---

### Settings Management

#### GET /api/admin/settings
Get all settings.

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "display": {
      "default_language": "ko",
      "countdown_options": [3, 5, 8, 10],
      "default_countdown": 5,
      "sound_enabled": true
    },
    "print": {
      "max_copies": 3,
      "paper_size": "4x6",
      "quality": "high",
      "logo_enabled": true,
      "date_enabled": true,
      "date_format": "YYYY.MM.DD"
    },
    "system": {
      "timezone": "Africa/Kigali",
      "admin_pin": "****",
      "auto_cleanup_days": 30,
      "log_level": "error"
    },
    "network": {
      "ssid": "photobooth",
      "password": "********",
      "channel": 6
    }
  }
}
```

---

#### PATCH /api/admin/settings
Update settings.

**Request Body:** (partial update)
```json
{
  "display": {
    "default_countdown": 8
  },
  "print": {
    "logo_enabled": false
  }
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "updated_fields": ["display.default_countdown", "print.logo_enabled"],
    "restart_required": false
  }
}
```

---

#### POST /api/admin/settings/pin
Change admin PIN.

**Request Body:**
```json
{
  "current_pin": "1234",  // Example - use your current ADMIN_PIN
  "new_pin": "5678"       // Example - set your new PIN
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "PIN updated successfully"
}
```

---

### Service Management

#### POST /api/admin/service/{service}/restart
Restart a service.

**Services:** `cups`, `hostapd`, `dnsmasq`, `backend`

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "service": "cups",
    "action": "restart",
    "previous_status": "running",
    "current_status": "running"
  }
}
```

---

#### POST /api/admin/system/reboot
Reboot the system.

**Request Body:**
```json
{
  "force": false
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "message": "Reboot scheduled in 10 seconds",
    "scheduled_at": "2024-01-13T10:30:00Z",
    "delay_seconds": 10
  }
}
```

---

#### POST /api/admin/system/reboot/cancel
Cancel scheduled reboot.

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Reboot cancelled"
}
```

---

### Storage Management

#### GET /api/admin/storage
Get storage details.

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "total_bytes": 256000000000,
    "used_bytes": 45200000000,
    "free_bytes": 210800000000,
    "percent_used": 17.7,
    "breakdown": {
      "photos": 42100000000,
      "composites": 2100000000,
      "logs": 500000000,
      "system": 500000000
    },
    "sessions": {
      "total": 1234,
      "by_month": [
        {"month": "2024-01", "count": 234, "size_bytes": 5000000000}
      ]
    }
  }
}
```

---

#### POST /api/admin/storage/cleanup
Clean old session data.

**Request Body:**
```json
{
  "older_than_days": 30,
  "dry_run": false
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "sessions_deleted": 150,
    "bytes_freed": 15000000000,
    "dry_run": false
  }
}
```

---

### Test Print

#### POST /api/admin/test-print
Send test print.

**Request Body:**
```json
{
  "pattern": "color_bars"  // "color_bars" | "grayscale" | "text"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "job_id": "test-job-123",
    "pattern": "color_bars",
    "status": "PENDING"
  }
}
```

---

### Logs

#### GET /api/admin/logs
Get system logs.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| level | string | all | Filter: all, error, warning, info |
| source | string | all | Filter: backend, cups, system |
| limit | int | 100 | Max lines (max 1000) |
| since | string | -1h | Time range |

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "logs": [
      {
        "timestamp": "2024-01-13T10:30:00Z",
        "level": "ERROR",
        "source": "backend",
        "message": "Printer connection failed",
        "details": {"error": "CUPS timeout"}
      }
    ],
    "total_count": 50,
    "has_more": true
  }
}
```

---

### Photo Export

#### POST /api/admin/export
Create export archive.

**Request Body:**
```json
{
  "session_ids": ["sess-123", "sess-456"],
  "include_originals": true,
  "include_composites": true
}
```

**Response:** `202 Accepted`
```json
{
  "success": true,
  "data": {
    "export_id": "export-789",
    "status": "PROCESSING",
    "estimated_size_bytes": 50000000
  }
}
```

---

#### GET /api/admin/export/{export_id}
Check export status.

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "export_id": "export-789",
    "status": "READY",
    "download_url": "/api/admin/export/export-789/download",
    "size_bytes": 48500000,
    "expires_at": "2024-01-13T11:30:00Z"
  }
}
```

---

#### GET /api/admin/export/{export_id}/download
Download export archive.

**Response:** `200 OK`
- Content-Type: `application/zip`
- Content-Disposition: `attachment; filename="photobooth-export-2024-01-13.zip"`

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `SESSION_NOT_FOUND` | 404 | Session ID doesn't exist |
| `PHOTO_NOT_FOUND` | 404 | Photo ID doesn't exist |
| `JOB_NOT_FOUND` | 404 | Print job ID doesn't exist |
| `INVALID_IMAGE` | 400 | Image format/size invalid |
| `SESSION_FULL` | 409 | Session already has 4 photos |
| `NO_COMPOSITE` | 400 | Session has no composite |
| `PRINTER_OFFLINE` | 503 | Printer not available |
| `AUTH_REQUIRED` | 401 | Missing/invalid auth token |
| `AUTH_FAILED` | 401 | Invalid PIN |
| `RATE_LIMITED` | 429 | Too many attempts |
| `JOB_NOT_RETRIABLE` | 409 | Job can't be retried |
| `JOB_COMPLETED` | 409 | Job already completed |
| `SERVICE_ERROR` | 500 | Internal server error |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| `POST /api/admin/login` | 5 attempts / 5 minutes |
| `POST /api/session/*/photos` | 10 uploads / minute |
| All other endpoints | 60 requests / minute |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
