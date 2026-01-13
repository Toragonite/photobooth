# Domain Entities Specification

> Core business objects and value objects for the PhotoBooth system

---

## Entity Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DOMAIN MODEL                                      │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         ENTITIES                                    │   │
│  │                                                                     │   │
│  │   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐        │   │
│  │   │   Photo     │      │  PhotoSess. │      │  PrintJob   │        │   │
│  │   │             │◄────►│             │◄────►│             │        │   │
│  │   └─────────────┘      └─────────────┘      └─────────────┘        │   │
│  │                                                                     │   │
│  │   ┌─────────────┐      ┌─────────────┐                             │   │
│  │   │  Composite  │      │  Settings   │                             │   │
│  │   │   Image     │      │             │                             │   │
│  │   └─────────────┘      └─────────────┘                             │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      VALUE OBJECTS                                  │   │
│  │                                                                     │   │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │   │
│  │   │  JobId   │  │SessionId │  │PrintStatus│ │Dimensions│           │   │
│  │   └──────────┘  └──────────┘  └──────────┘  └──────────┘           │   │
│  │                                                                     │   │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │   │
│  │   │ Language │  │ ErrorCode│  │FilePath  │  │Timestamp │           │   │
│  │   └──────────┘  └──────────┘  └──────────┘  └──────────┘           │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Photo Entity

### Description

Represents a single captured photograph with metadata.

### Attributes

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | PhotoId | Yes | Unique identifier |
| `session_id` | SessionId | Yes | Parent session |
| `index` | int (0-3) | Yes | Position in session |
| `data` | bytes | Yes | Raw image data (JPEG) |
| `width` | int | Yes | Image width in pixels |
| `height` | int | Yes | Image height in pixels |
| `size_bytes` | int | Yes | File size |
| `captured_at` | datetime | Yes | Capture timestamp |

### Business Rules

| ID | Rule |
|----|------|
| PHOTO-BR-1 | Data must be valid JPEG format |
| PHOTO-BR-2 | Maximum size: 5MB |
| PHOTO-BR-3 | Index must be 0, 1, 2, or 3 |
| PHOTO-BR-4 | Minimum dimensions: 640x480 |

### Python Implementation

```python
# domain/entities/photo.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from ..value_objects import PhotoId, SessionId
from ..exceptions import InvalidPhotoError

@dataclass
class Photo:
    """A captured photograph"""

    id: PhotoId
    session_id: SessionId
    index: int
    data: bytes
    width: int
    height: int
    size_bytes: int
    captured_at: datetime

    MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
    MIN_WIDTH = 640
    MIN_HEIGHT = 480
    VALID_INDICES = (0, 1, 2, 3)

    def __post_init__(self):
        self._validate()

    def _validate(self):
        if self.index not in self.VALID_INDICES:
            raise InvalidPhotoError(f"Index must be 0-3, got {self.index}")

        if self.size_bytes > self.MAX_SIZE_BYTES:
            raise InvalidPhotoError(f"Photo exceeds max size of {self.MAX_SIZE_BYTES} bytes")

        if self.width < self.MIN_WIDTH or self.height < self.MIN_HEIGHT:
            raise InvalidPhotoError(
                f"Photo dimensions {self.width}x{self.height} below minimum"
            )

    @classmethod
    def create(
        cls,
        session_id: SessionId,
        index: int,
        data: bytes,
        captured_at: Optional[datetime] = None,
    ) -> "Photo":
        """Factory method to create a Photo with validation"""
        from PIL import Image
        import io

        # Validate JPEG
        try:
            img = Image.open(io.BytesIO(data))
            if img.format != 'JPEG':
                raise InvalidPhotoError("Photo must be JPEG format")
            width, height = img.size
        except Exception as e:
            raise InvalidPhotoError(f"Invalid image data: {e}")

        return cls(
            id=PhotoId.generate(),
            session_id=session_id,
            index=index,
            data=data,
            width=width,
            height=height,
            size_bytes=len(data),
            captured_at=captured_at or datetime.now(),
        )
```

### TypeScript Implementation

```typescript
// domain/entities/Photo.ts

export interface PhotoProps {
  id: string;
  sessionId: string;
  index: number;
  dataUrl: string;  // base64 data URL
  width: number;
  height: number;
  sizeBytes: number;
  capturedAt: Date;
}

export class Photo {
  private constructor(private readonly props: PhotoProps) {
    this.validate();
  }

  static readonly MAX_SIZE_BYTES = 5 * 1024 * 1024;
  static readonly VALID_INDICES = [0, 1, 2, 3] as const;

  private validate(): void {
    if (!Photo.VALID_INDICES.includes(this.props.index as any)) {
      throw new InvalidPhotoError(`Index must be 0-3`);
    }
    if (this.props.sizeBytes > Photo.MAX_SIZE_BYTES) {
      throw new InvalidPhotoError(`Photo exceeds max size`);
    }
  }

  static create(
    sessionId: string,
    index: number,
    dataUrl: string,
  ): Photo {
    return new Photo({
      id: generateUUID(),
      sessionId,
      index,
      dataUrl,
      width: 0,  // Set after image load
      height: 0,
      sizeBytes: Math.ceil((dataUrl.length - 22) * 0.75), // Estimate
      capturedAt: new Date(),
    });
  }

  get id(): string { return this.props.id; }
  get index(): number { return this.props.index; }
  get dataUrl(): string { return this.props.dataUrl; }
  // ... other getters
}
```

---

## 2. PhotoSession Entity

### Description

Represents a complete photo booth session containing up to 4 photos.

### Attributes

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | SessionId | Yes | Unique identifier |
| `photos` | List[Photo] | Yes | Captured photos (0-4) |
| `settings` | SessionSettings | Yes | User preferences |
| `language` | Language | Yes | Selected UI language |
| `status` | SessionStatus | Yes | Current state |
| `created_at` | datetime | Yes | Session start |
| `completed_at` | datetime | No | When 4 photos captured |

### Session Status Enum

```python
class SessionStatus(str, Enum):
    ACTIVE = "active"           # Capturing photos
    COMPLETE = "complete"       # 4 photos captured
    PRINTED = "printed"         # Print submitted
    ABANDONED = "abandoned"     # Timeout/cancelled
```

### Business Rules

| ID | Rule |
|----|------|
| SESS-BR-1 | Maximum 4 photos per session |
| SESS-BR-2 | Photos must have unique indices 0-3 |
| SESS-BR-3 | Cannot add photos after status is COMPLETE |
| SESS-BR-4 | Session expires after 10 minutes of inactivity |

### State Transitions

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   ┌────────┐   add photo (< 4)   ┌────────┐                    │
│   │ ACTIVE │◄───────────────────►│ ACTIVE │                    │
│   └────┬───┘                     └────┬───┘                    │
│        │                              │                         │
│        │ add 4th photo               │ timeout                 │
│        ▼                              ▼                         │
│   ┌────────────┐               ┌────────────┐                  │
│   │  COMPLETE  │               │ ABANDONED  │                  │
│   └─────┬──────┘               └────────────┘                  │
│         │                                                       │
│         │ submit print                                         │
│         ▼                                                       │
│   ┌────────────┐                                               │
│   │  PRINTED   │                                               │
│   └────────────┘                                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Python Implementation

```python
# domain/entities/photo_session.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from ..value_objects import SessionId, Language
from ..exceptions import SessionError
from .photo import Photo

@dataclass
class SessionSettings:
    countdown_seconds: int = 5
    sound_enabled: bool = True

@dataclass
class PhotoSession:
    """A photo booth session with up to 4 photos"""

    id: SessionId
    photos: List[Photo] = field(default_factory=list)
    settings: SessionSettings = field(default_factory=SessionSettings)
    language: Language = Language.KOREAN
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    MAX_PHOTOS = 4

    @classmethod
    def create(
        cls,
        language: Language = Language.KOREAN,
        settings: Optional[SessionSettings] = None,
    ) -> "PhotoSession":
        """Create a new session"""
        return cls(
            id=SessionId.generate(),
            language=language,
            settings=settings or SessionSettings(),
        )

    def add_photo(self, photo: Photo) -> None:
        """Add a photo to the session"""
        if self.status != SessionStatus.ACTIVE:
            raise SessionError("Cannot add photos to non-active session")

        if len(self.photos) >= self.MAX_PHOTOS:
            raise SessionError("Session already has maximum photos")

        if any(p.index == photo.index for p in self.photos):
            raise SessionError(f"Photo at index {photo.index} already exists")

        self.photos.append(photo)
        self.photos.sort(key=lambda p: p.index)

        if len(self.photos) == self.MAX_PHOTOS:
            self.status = SessionStatus.COMPLETE
            self.completed_at = datetime.now()

    def replace_photo(self, photo: Photo) -> None:
        """Replace a photo at the given index"""
        if self.status not in (SessionStatus.ACTIVE, SessionStatus.COMPLETE):
            raise SessionError("Cannot replace photos in this session state")

        # Remove existing photo at this index
        self.photos = [p for p in self.photos if p.index != photo.index]

        # If was complete, go back to active
        if self.status == SessionStatus.COMPLETE:
            self.status = SessionStatus.ACTIVE
            self.completed_at = None

        self.add_photo(photo)

    def mark_printed(self) -> None:
        """Mark session as printed"""
        if self.status != SessionStatus.COMPLETE:
            raise SessionError("Can only print complete sessions")
        self.status = SessionStatus.PRINTED

    def abandon(self) -> None:
        """Abandon the session"""
        if self.status == SessionStatus.PRINTED:
            raise SessionError("Cannot abandon printed session")
        self.status = SessionStatus.ABANDONED

    @property
    def is_complete(self) -> bool:
        return len(self.photos) == self.MAX_PHOTOS

    @property
    def photo_count(self) -> int:
        return len(self.photos)

    def get_photo(self, index: int) -> Optional[Photo]:
        """Get photo by index"""
        for photo in self.photos:
            if photo.index == index:
                return photo
        return None
```

---

## 3. PrintJob Entity

### Description

Represents a print request with full lifecycle management.

### Attributes

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | JobId | Yes | Unique job identifier |
| `session_id` | SessionId | Yes | Source session |
| `status` | PrintStatus | Yes | Current state |
| `copies` | int | Yes | Number of copies (1-4) |
| `add_date` | bool | Yes | Include date stamp |
| `add_logo` | bool | Yes | Include logo |
| `cups_job_id` | int | No | CUPS job reference |
| `composite_path` | Path | No | Generated image path |
| `originals_path` | Path | No | Archived originals path |
| `error_code` | str | No | Error identifier |
| `error_message` | str | No | Human-readable error |
| `retry_count` | int | Yes | Auto-retry attempts |
| `created_at` | datetime | Yes | Job creation time |
| `updated_at` | datetime | Yes | Last state change |
| `completed_at` | datetime | No | Completion time |

### Print Status Enum

```python
class PrintStatus(str, Enum):
    PROCESSING = "processing"   # Creating composite
    SENDING = "sending"         # Sending to CUPS
    PRINTING = "printing"       # CUPS job active
    COMPLETED = "completed"     # Successfully printed
    ERROR = "error"             # Failed (may retry)
    FAILED = "failed"           # Failed after max retries
    ABORTED = "aborted"         # User cancelled
```

### Error Codes

| Code | Description | Retryable |
|------|-------------|-----------|
| `PRINTER_OFFLINE` | Printer not responding | Yes |
| `PRINTER_BUSY` | Printer queue full | Yes |
| `PAPER_EMPTY` | No paper loaded | Yes |
| `INK_EMPTY` | Ink depleted | Yes |
| `CUPS_UNAVAILABLE` | CUPS daemon down | Yes |
| `CUPS_REJECTED` | CUPS rejected job | Yes |
| `PROCESSING_ERROR` | Image processing failed | No |
| `INVALID_IMAGE` | Bad image data | No |
| `STORAGE_FULL` | Disk full | No |
| `TIMEOUT` | Job timed out | No |

### State Machine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌────────────┐                                                             │
│  │ PROCESSING │─────────────────────────────┐                               │
│  └─────┬──────┘                             │                               │
│        │                                    │                               │
│        │ composite created                  │ error (non-retryable)         │
│        ▼                                    │                               │
│  ┌────────────┐                             │                               │
│  │  SENDING   │───────────────────┐         │                               │
│  └─────┬──────┘                   │         │                               │
│        │                          │         │                               │
│        │ CUPS accepted            │ error   │                               │
│        ▼                          │         │                               │
│  ┌────────────┐                   │         │                               │
│  │  PRINTING  │───────────┐       │         │                               │
│  └─────┬──────┘           │       │         │                               │
│        │                  │       │         │                               │
│        │ CUPS done        │error  │         │                               │
│        ▼                  │       │         │                               │
│  ┌────────────┐     ┌─────▼──────┐│         │                               │
│  │ COMPLETED  │     │   ERROR    │◄─────────┘                               │
│  └────────────┘     └─────┬──────┘                                          │
│                           │                                                 │
│                           ├── retry_count < 3 ──► auto-retry ──► SENDING    │
│                           │                                                 │
│                           └── retry_count >= 3                              │
│                                    │                                        │
│                                    ▼                                        │
│                             ┌────────────┐                                  │
│                             │  FAILED    │ (needs user action)              │
│                             └─────┬──────┘                                  │
│                                   │                                         │
│                                   ├── user retry ──► SENDING (reset count)  │
│                                   │                                         │
│                                   └── user abort                            │
│                                          │                                  │
│                                          ▼                                  │
│                                   ┌────────────┐                            │
│                                   │  ABORTED   │                            │
│                                   └────────────┘                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Business Rules

| ID | Rule |
|----|------|
| JOB-BR-1 | Copies must be 1-4 |
| JOB-BR-2 | Maximum 3 auto-retries |
| JOB-BR-3 | Only retryable errors trigger auto-retry |
| JOB-BR-4 | User retry resets retry counter |
| JOB-BR-5 | Cannot abort completed or already aborted jobs |
| JOB-BR-6 | Job timeout: 120 seconds from creation |

### Python Implementation

```python
# domain/entities/print_job.py

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from ..value_objects import JobId, SessionId, PrintStatus, ErrorCode
from ..exceptions import PrintJobError

@dataclass
class PrintJob:
    """A print job with full lifecycle"""

    id: JobId
    session_id: SessionId
    status: PrintStatus
    copies: int
    add_date: bool
    add_logo: bool
    cups_job_id: Optional[int] = None
    composite_path: Optional[Path] = None
    originals_path: Optional[Path] = None
    error_code: Optional[ErrorCode] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    MAX_RETRIES = 3
    TIMEOUT_SECONDS = 120

    RETRYABLE_ERRORS = {
        ErrorCode.PRINTER_OFFLINE,
        ErrorCode.PRINTER_BUSY,
        ErrorCode.PAPER_EMPTY,
        ErrorCode.INK_EMPTY,
        ErrorCode.CUPS_UNAVAILABLE,
        ErrorCode.CUPS_REJECTED,
    }

    @classmethod
    def create(
        cls,
        session_id: SessionId,
        copies: int,
        add_date: bool = True,
        add_logo: bool = False,
    ) -> "PrintJob":
        """Create a new print job"""
        if not 1 <= copies <= 4:
            raise PrintJobError("Copies must be between 1 and 4")

        return cls(
            id=JobId.generate(),
            session_id=session_id,
            status=PrintStatus.PROCESSING,
            copies=copies,
            add_date=add_date,
            add_logo=add_logo,
        )

    def transition_to(self, new_status: PrintStatus) -> None:
        """Transition to a new status with validation"""
        valid_transitions = {
            PrintStatus.PROCESSING: {PrintStatus.SENDING, PrintStatus.ERROR},
            PrintStatus.SENDING: {PrintStatus.PRINTING, PrintStatus.ERROR},
            PrintStatus.PRINTING: {PrintStatus.COMPLETED, PrintStatus.ERROR},
            PrintStatus.ERROR: {PrintStatus.SENDING, PrintStatus.FAILED, PrintStatus.ABORTED},
            PrintStatus.FAILED: {PrintStatus.SENDING, PrintStatus.ABORTED},
        }

        allowed = valid_transitions.get(self.status, set())
        if new_status not in allowed:
            raise PrintJobError(
                f"Cannot transition from {self.status} to {new_status}"
            )

        self.status = new_status
        self.updated_at = datetime.now()

        if new_status == PrintStatus.COMPLETED:
            self.completed_at = datetime.now()

    def set_cups_job_id(self, cups_job_id: int) -> None:
        """Set CUPS job reference"""
        self.cups_job_id = cups_job_id
        self.updated_at = datetime.now()

    def set_paths(self, composite: Path, originals: Path) -> None:
        """Set file paths"""
        self.composite_path = composite
        self.originals_path = originals
        self.updated_at = datetime.now()

    def mark_error(
        self,
        error_code: ErrorCode,
        error_message: str,
    ) -> None:
        """Mark job as error with details"""
        self.error_code = error_code
        self.error_message = error_message
        self.retry_count += 1
        self.updated_at = datetime.now()

        if self.can_auto_retry:
            self.status = PrintStatus.ERROR
        else:
            self.status = PrintStatus.FAILED

    @property
    def can_auto_retry(self) -> bool:
        """Check if auto-retry is possible"""
        return (
            self.error_code in self.RETRYABLE_ERRORS and
            self.retry_count < self.MAX_RETRIES
        )

    @property
    def needs_user_retry(self) -> bool:
        """Check if user action is needed"""
        return self.status == PrintStatus.FAILED

    def user_retry(self) -> None:
        """User-initiated retry (resets counter)"""
        if self.status != PrintStatus.FAILED:
            raise PrintJobError("Can only retry failed jobs")

        self.retry_count = 0
        self.error_code = None
        self.error_message = None
        self.status = PrintStatus.SENDING
        self.updated_at = datetime.now()

    def abort(self) -> None:
        """Abort the job"""
        if self.status in (PrintStatus.COMPLETED, PrintStatus.ABORTED):
            raise PrintJobError(f"Cannot abort job in {self.status} state")

        self.status = PrintStatus.ABORTED
        self.updated_at = datetime.now()

    @property
    def is_terminal(self) -> bool:
        """Check if job is in terminal state"""
        return self.status in (
            PrintStatus.COMPLETED,
            PrintStatus.ABORTED,
            PrintStatus.FAILED,
        )

    @property
    def can_go_home(self) -> bool:
        """Check if user can navigate away"""
        return self.is_terminal

    @property
    def progress_percent(self) -> int:
        """Calculate progress percentage"""
        return {
            PrintStatus.PROCESSING: 25,
            PrintStatus.SENDING: 50,
            PrintStatus.PRINTING: 75,
            PrintStatus.COMPLETED: 100,
            PrintStatus.ERROR: self.retry_count * 25,  # Shows retry progress
            PrintStatus.FAILED: 0,
            PrintStatus.ABORTED: 0,
        }.get(self.status, 0)
```

---

## 4. Value Objects

### 4.1 JobId

```python
# domain/value_objects/job_id.py

import uuid
from dataclasses import dataclass

@dataclass(frozen=True)
class JobId:
    """Unique identifier for print jobs"""
    value: str

    def __post_init__(self):
        if not self.value or len(self.value) != 8:
            raise ValueError("JobId must be 8 characters")

    @classmethod
    def generate(cls) -> "JobId":
        """Generate a new JobId"""
        return cls(uuid.uuid4().hex[:8])

    @classmethod
    def from_string(cls, value: str) -> "JobId":
        """Create from string"""
        return cls(value)

    def __str__(self) -> str:
        return self.value
```

### 4.2 SessionId

```python
# domain/value_objects/session_id.py

import uuid
from dataclasses import dataclass

@dataclass(frozen=True)
class SessionId:
    """Unique identifier for photo sessions"""
    value: str

    def __post_init__(self):
        # Validate UUID format
        try:
            uuid.UUID(self.value)
        except ValueError:
            raise ValueError("SessionId must be valid UUID")

    @classmethod
    def generate(cls) -> "SessionId":
        return cls(str(uuid.uuid4()))

    def __str__(self) -> str:
        return self.value
```

### 4.3 PrintStatus

```python
# domain/value_objects/print_status.py

from enum import Enum

class PrintStatus(str, Enum):
    PROCESSING = "processing"
    SENDING = "sending"
    PRINTING = "printing"
    COMPLETED = "completed"
    ERROR = "error"
    FAILED = "failed"
    ABORTED = "aborted"

    @property
    def is_terminal(self) -> bool:
        return self in (self.COMPLETED, self.FAILED, self.ABORTED)

    @property
    def is_error(self) -> bool:
        return self in (self.ERROR, self.FAILED)

    @property
    def display_name(self) -> str:
        return {
            self.PROCESSING: "Processing",
            self.SENDING: "Sending",
            self.PRINTING: "Printing",
            self.COMPLETED: "Completed",
            self.ERROR: "Error",
            self.FAILED: "Failed",
            self.ABORTED: "Aborted",
        }[self]

    @property
    def display_name_ko(self) -> str:
        return {
            self.PROCESSING: "처리 중",
            self.SENDING: "전송 중",
            self.PRINTING: "인쇄 중",
            self.COMPLETED: "완료",
            self.ERROR: "오류",
            self.FAILED: "실패",
            self.ABORTED: "취소됨",
        }[self]
```

### 4.4 Language

```python
# domain/value_objects/language.py

from enum import Enum

class Language(str, Enum):
    KOREAN = "ko"
    ENGLISH = "en"

    @property
    def display_name(self) -> str:
        return {
            self.KOREAN: "한국어",
            self.ENGLISH: "English",
        }[self]
```

### 4.5 ErrorCode

```python
# domain/value_objects/error_code.py

from enum import Enum

class ErrorCode(str, Enum):
    # Printer errors (retryable)
    PRINTER_OFFLINE = "printer_offline"
    PRINTER_BUSY = "printer_busy"
    PAPER_EMPTY = "paper_empty"
    INK_EMPTY = "ink_empty"

    # CUPS errors (retryable)
    CUPS_UNAVAILABLE = "cups_unavailable"
    CUPS_REJECTED = "cups_rejected"

    # Processing errors (not retryable)
    PROCESSING_ERROR = "processing_error"
    INVALID_IMAGE = "invalid_image"
    STORAGE_FULL = "storage_full"
    TIMEOUT = "timeout"

    @property
    def is_retryable(self) -> bool:
        return self in {
            self.PRINTER_OFFLINE,
            self.PRINTER_BUSY,
            self.PAPER_EMPTY,
            self.INK_EMPTY,
            self.CUPS_UNAVAILABLE,
            self.CUPS_REJECTED,
        }

    @property
    def user_message(self) -> str:
        return {
            self.PRINTER_OFFLINE: "Printer is offline. Please check the connection.",
            self.PRINTER_BUSY: "Printer is busy. Please wait.",
            self.PAPER_EMPTY: "Please add paper to the printer.",
            self.INK_EMPTY: "Please replace the ink cartridge.",
            self.CUPS_UNAVAILABLE: "Print service unavailable. Retrying...",
            self.CUPS_REJECTED: "Print job rejected. Retrying...",
            self.PROCESSING_ERROR: "Failed to process images.",
            self.INVALID_IMAGE: "Invalid image data.",
            self.STORAGE_FULL: "Storage full. Contact administrator.",
            self.TIMEOUT: "Print job timed out.",
        }[self]

    @property
    def user_message_ko(self) -> str:
        return {
            self.PRINTER_OFFLINE: "프린터가 오프라인입니다. 연결을 확인하세요.",
            self.PRINTER_BUSY: "프린터가 사용 중입니다. 잠시 기다려주세요.",
            self.PAPER_EMPTY: "용지를 넣어주세요.",
            self.INK_EMPTY: "잉크 카트리지를 교체해주세요.",
            self.CUPS_UNAVAILABLE: "인쇄 서비스를 사용할 수 없습니다. 재시도 중...",
            self.CUPS_REJECTED: "인쇄 작업이 거부되었습니다. 재시도 중...",
            self.PROCESSING_ERROR: "이미지 처리에 실패했습니다.",
            self.INVALID_IMAGE: "잘못된 이미지 데이터입니다.",
            self.STORAGE_FULL: "저장 공간이 부족합니다. 관리자에게 문의하세요.",
            self.TIMEOUT: "인쇄 작업 시간이 초과되었습니다.",
        }[self]
```

---

## 5. Domain Events

### Event Definitions

```python
# domain/events/print_job_events.py

from dataclasses import dataclass
from datetime import datetime
from ..value_objects import JobId, PrintStatus

@dataclass(frozen=True)
class DomainEvent:
    """Base class for domain events"""
    occurred_at: datetime = field(default_factory=datetime.now)

@dataclass(frozen=True)
class PrintJobCreated(DomainEvent):
    job_id: JobId
    session_id: SessionId
    copies: int

@dataclass(frozen=True)
class PrintJobStatusChanged(DomainEvent):
    job_id: JobId
    old_status: PrintStatus
    new_status: PrintStatus

@dataclass(frozen=True)
class PrintJobCompleted(DomainEvent):
    job_id: JobId
    cups_job_id: int
    duration_seconds: float

@dataclass(frozen=True)
class PrintJobFailed(DomainEvent):
    job_id: JobId
    error_code: str
    error_message: str
    retry_count: int

@dataclass(frozen=True)
class PrintJobRetrying(DomainEvent):
    job_id: JobId
    retry_count: int
    max_retries: int
```

---

## 6. Domain Exceptions

```python
# domain/exceptions/domain_exceptions.py

class DomainError(Exception):
    """Base class for domain errors"""
    pass

class InvalidPhotoError(DomainError):
    """Raised when photo validation fails"""
    pass

class SessionError(DomainError):
    """Raised for session-related errors"""
    pass

class PrintJobError(DomainError):
    """Raised for print job errors"""
    pass

class InvalidStateTransitionError(DomainError):
    """Raised when invalid state transition attempted"""
    pass
```

---

## 7. Entity Relationships

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                         ENTITY RELATIONSHIPS                                │
│                                                                             │
│   ┌────────────────┐                                                        │
│   │  PhotoSession  │                                                        │
│   │                │                                                        │
│   │  - id          │                                                        │
│   │  - status      │                                                        │
│   │  - language    │                                                        │
│   │  - settings    │                                                        │
│   └───────┬────────┘                                                        │
│           │                                                                 │
│           │ 1:N (max 4)                                                     │
│           │                                                                 │
│   ┌───────▼────────┐         1:1         ┌────────────────┐                │
│   │     Photo      │◄───────────────────►│   PrintJob     │                │
│   │                │                     │                │                │
│   │  - index (0-3) │                     │  - status      │                │
│   │  - data        │                     │  - copies      │                │
│   │  - dimensions  │                     │  - retry_count │                │
│   └────────────────┘                     │  - error_code  │                │
│                                          └───────┬────────┘                │
│                                                  │                         │
│                                                  │ 1:1                     │
│                                                  │                         │
│                                          ┌───────▼────────┐                │
│                                          │CompositeImage  │                │
│                                          │                │                │
│                                          │  - file_path   │                │
│                                          │  - dimensions  │                │
│                                          │  - has_date    │                │
│                                          │  - has_logo    │                │
│                                          └────────────────┘                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*Next: See `docs/interfaces/INTERFACES.md` for repository and service interfaces*
