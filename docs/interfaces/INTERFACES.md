# Interface Specifications

> Port definitions for Clean Architecture boundaries

---

## 1. Interface Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                            APPLICATION LAYER                                │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                             PORTS                                     │ │
│  │                                                                       │ │
│  │   ┌─────────────────────────┐     ┌─────────────────────────┐        │ │
│  │   │      REPOSITORIES       │     │        SERVICES         │        │ │
│  │   │     (Data Access)       │     │   (External Systems)    │        │ │
│  │   │                         │     │                         │        │ │
│  │   │  • PrintJobRepository   │     │  • PrinterService       │        │ │
│  │   │  • SessionRepository    │     │  • ImageProcessor       │        │ │
│  │   │  • SettingsRepository   │     │  • StorageService       │        │ │
│  │   │  • LogRepository        │     │  • SystemService        │        │ │
│  │   │                         │     │                         │        │ │
│  │   └───────────┬─────────────┘     └───────────┬─────────────┘        │ │
│  │               │                               │                       │ │
│  └───────────────┼───────────────────────────────┼───────────────────────┘ │
│                  │                               │                         │
│                  │ implements                    │ implements              │
│                  │                               │                         │
│  ┌───────────────┼───────────────────────────────┼───────────────────────┐ │
│  │               │     INFRASTRUCTURE LAYER      │                       │ │
│  │               │                               │                       │ │
│  │   ┌───────────▼─────────────┐     ┌───────────▼─────────────┐        │ │
│  │   │  SqlitePrintJobRepo     │     │  CupsPrinterService     │        │ │
│  │   │  SqliteSessionRepo      │     │  PillowImageProcessor   │        │ │
│  │   │  SqliteSettingsRepo     │     │  FileStorageService     │        │ │
│  │   │  SqliteLogRepo          │     │  LinuxSystemService     │        │ │
│  │   └─────────────────────────┘     └─────────────────────────┘        │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Repository Interfaces

### 2.1 PrintJobRepository

```python
# application/ports/repositories/print_job_repository.py

from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime
from domain.entities import PrintJob
from domain.value_objects import JobId, SessionId, PrintStatus

class PrintJobRepository(ABC):
    """
    Port for PrintJob persistence operations.

    Implementations must be thread-safe as multiple
    requests may access the repository concurrently.
    """

    @abstractmethod
    def save(self, job: PrintJob) -> None:
        """
        Persist a new print job.

        Args:
            job: PrintJob entity to save

        Raises:
            RepositoryError: If save fails
            DuplicateKeyError: If job_id already exists
        """
        pass

    @abstractmethod
    def update(self, job: PrintJob) -> None:
        """
        Update an existing print job.

        Args:
            job: PrintJob entity with updated values

        Raises:
            RepositoryError: If update fails
            NotFoundError: If job doesn't exist
        """
        pass

    @abstractmethod
    def find_by_id(self, job_id: JobId) -> Optional[PrintJob]:
        """
        Find a print job by its ID.

        Args:
            job_id: The job identifier

        Returns:
            PrintJob if found, None otherwise
        """
        pass

    @abstractmethod
    def find_by_session(self, session_id: SessionId) -> Optional[PrintJob]:
        """
        Find print job for a session.

        Args:
            session_id: The session identifier

        Returns:
            Most recent PrintJob for session, None if not found
        """
        pass

    @abstractmethod
    def find_active(self) -> List[PrintJob]:
        """
        Find all non-terminal jobs.

        Returns:
            List of jobs in PROCESSING, SENDING, PRINTING, or ERROR status
        """
        pass

    @abstractmethod
    def find_by_status(
        self,
        status: PrintStatus,
        limit: int = 100
    ) -> List[PrintJob]:
        """
        Find jobs by status.

        Args:
            status: The status to filter by
            limit: Maximum number of results

        Returns:
            List of matching PrintJobs, ordered by created_at DESC
        """
        pass

    @abstractmethod
    def find_recent(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[PrintJob]:
        """
        Find most recent jobs (for admin view).

        Args:
            limit: Maximum number of results
            offset: Number of records to skip

        Returns:
            List of PrintJobs ordered by created_at DESC
        """
        pass

    @abstractmethod
    def find_for_retry(self) -> List[PrintJob]:
        """
        Find jobs eligible for auto-retry.

        Returns:
            Jobs in ERROR status with retry_count < MAX_RETRIES
        """
        pass

    @abstractmethod
    def count_by_status(self) -> dict[PrintStatus, int]:
        """
        Get count of jobs per status.

        Returns:
            Dictionary mapping status to count
        """
        pass

    @abstractmethod
    def delete_older_than(self, cutoff: datetime) -> int:
        """
        Delete jobs older than cutoff (cleanup).

        Args:
            cutoff: Delete jobs created before this time

        Returns:
            Number of jobs deleted
        """
        pass
```

### 2.2 SessionRepository

```python
# application/ports/repositories/session_repository.py

from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime
from domain.entities import PhotoSession
from domain.value_objects import SessionId, SessionStatus

class SessionRepository(ABC):
    """Port for PhotoSession persistence operations."""

    @abstractmethod
    def save(self, session: PhotoSession) -> None:
        """
        Persist a new session.

        Note: Also persists associated photos.
        """
        pass

    @abstractmethod
    def update(self, session: PhotoSession) -> None:
        """Update an existing session."""
        pass

    @abstractmethod
    def find_by_id(self, session_id: SessionId) -> Optional[PhotoSession]:
        """
        Find session by ID.

        Returns session with all associated photos loaded.
        """
        pass

    @abstractmethod
    def find_active(self) -> List[PhotoSession]:
        """Find all active (non-abandoned, non-printed) sessions."""
        pass

    @abstractmethod
    def find_abandoned(
        self,
        older_than_minutes: int = 10
    ) -> List[PhotoSession]:
        """Find sessions to mark as abandoned."""
        pass

    @abstractmethod
    def mark_abandoned(self, session_id: SessionId) -> None:
        """Mark a session as abandoned."""
        pass
```

### 2.3 SettingsRepository

```python
# application/ports/repositories/settings_repository.py

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict

class SettingsRepository(ABC):
    """Port for application settings persistence."""

    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """
        Get a setting value.

        Args:
            key: Setting key

        Returns:
            Setting value as string, None if not found
        """
        pass

    @abstractmethod
    def get_int(self, key: str, default: int = 0) -> int:
        """Get setting as integer."""
        pass

    @abstractmethod
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get setting as boolean."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """
        Set a setting value.

        Args:
            key: Setting key
            value: Value (will be converted to string)
        """
        pass

    @abstractmethod
    def get_all(self) -> Dict[str, str]:
        """Get all settings as dictionary."""
        pass

    @abstractmethod
    def set_many(self, settings: Dict[str, Any]) -> None:
        """Set multiple settings at once."""
        pass
```

---

## 3. Service Interfaces

### 3.1 PrinterService

```python
# application/ports/services/printer_service.py

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

class PrinterState(str, Enum):
    IDLE = "idle"
    PRINTING = "printing"
    ERROR = "error"
    OFFLINE = "offline"

class JobState(str, Enum):
    PENDING = "pending"
    HELD = "held"
    PROCESSING = "processing"
    STOPPED = "stopped"
    CANCELED = "canceled"
    ABORTED = "aborted"
    COMPLETED = "completed"

@dataclass
class PrinterInfo:
    """Printer status information"""
    name: str
    state: PrinterState
    state_message: str
    is_accepting_jobs: bool
    paper_status: Optional[str] = None  # "ok", "low", "empty", "unknown"
    ink_status: Optional[str] = None
    error_message: Optional[str] = None

@dataclass
class PrintOptions:
    """Print job options"""
    copies: int = 1
    media_size: str = "4x6"
    quality: str = "high"  # "draft", "normal", "high"
    fit_to_page: bool = True

@dataclass
class PrintResult:
    """Result of a print operation"""
    success: bool
    cups_job_id: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

@dataclass
class JobStatus:
    """Status of a CUPS job"""
    cups_job_id: int
    state: JobState
    state_message: str
    progress_percent: Optional[int] = None

class PrinterService(ABC):
    """
    Port for printer operations.

    This interface abstracts all printer communication,
    allowing different implementations (CUPS, mock, etc.)
    """

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to print service.

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to print service."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to print service."""
        pass

    @abstractmethod
    def get_printers(self) -> List[PrinterInfo]:
        """
        Get list of available printers.

        Returns:
            List of PrinterInfo for each printer
        """
        pass

    @abstractmethod
    def get_default_printer(self) -> Optional[str]:
        """Get name of default printer."""
        pass

    @abstractmethod
    def get_printer_status(
        self,
        printer_name: Optional[str] = None
    ) -> PrinterInfo:
        """
        Get status of a specific printer.

        Args:
            printer_name: Printer to query, or default if None

        Returns:
            PrinterInfo with current status

        Raises:
            PrinterNotFoundError: If printer doesn't exist
        """
        pass

    @abstractmethod
    def is_ready(self, printer_name: Optional[str] = None) -> bool:
        """
        Check if printer is ready to accept jobs.

        Args:
            printer_name: Printer to check, or default if None

        Returns:
            True if printer is idle and accepting jobs
        """
        pass

    @abstractmethod
    def print_file(
        self,
        file_path: Path,
        options: Optional[PrintOptions] = None,
        printer_name: Optional[str] = None,
    ) -> PrintResult:
        """
        Send a file to the printer.

        Args:
            file_path: Path to file to print
            options: Print options (copies, quality, etc.)
            printer_name: Target printer, or default if None

        Returns:
            PrintResult with success status and job ID

        Raises:
            FileNotFoundError: If file doesn't exist
            PrinterError: If print submission fails
        """
        pass

    @abstractmethod
    def get_job_status(self, cups_job_id: int) -> JobStatus:
        """
        Get status of a print job.

        Args:
            cups_job_id: CUPS job identifier

        Returns:
            JobStatus with current state

        Raises:
            JobNotFoundError: If job doesn't exist
        """
        pass

    @abstractmethod
    def cancel_job(self, cups_job_id: int) -> bool:
        """
        Cancel a print job.

        Args:
            cups_job_id: CUPS job identifier

        Returns:
            True if cancellation successful
        """
        pass

    @abstractmethod
    def get_active_jobs(
        self,
        printer_name: Optional[str] = None
    ) -> List[JobStatus]:
        """Get all active (non-completed) jobs."""
        pass
```

### 3.2 ImageProcessor

```python
# application/ports/services/image_processor.py

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class CompositeOptions:
    """Options for composite image creation"""
    width: int = 1200           # 4 inches at 300 DPI
    height: int = 1800          # 6 inches at 300 DPI
    padding: int = 30           # Pixels between photos
    background_color: str = "#FFFFFF"
    add_date: bool = True
    date_format: str = "%Y.%m.%d"
    date_font_size: int = 28
    add_logo: bool = False
    logo_path: Optional[Path] = None
    logo_position: str = "bottom_center"  # or "bottom_right"
    logo_size: Tuple[int, int] = (100, 50)
    output_quality: int = 95    # JPEG quality

@dataclass
class ProcessingResult:
    """Result of image processing"""
    success: bool
    output_path: Optional[Path] = None
    output_bytes: Optional[bytes] = None
    width: int = 0
    height: int = 0
    size_bytes: int = 0
    error_message: Optional[str] = None

class ImageProcessor(ABC):
    """
    Port for image processing operations.

    Handles composite image creation for 4-cut photo layout.
    """

    @abstractmethod
    def create_composite(
        self,
        images: List[bytes],
        options: Optional[CompositeOptions] = None,
    ) -> ProcessingResult:
        """
        Create a 4-cut composite image.

        Args:
            images: List of exactly 4 JPEG images as bytes
            options: Composite creation options

        Returns:
            ProcessingResult with composite image

        Raises:
            InvalidImageError: If images are invalid
            ProcessingError: If composition fails
        """
        pass

    @abstractmethod
    def validate_image(self, image_data: bytes) -> Tuple[bool, str]:
        """
        Validate image data.

        Args:
            image_data: Raw image bytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

    @abstractmethod
    def get_dimensions(self, image_data: bytes) -> Tuple[int, int]:
        """
        Get image dimensions.

        Args:
            image_data: Raw image bytes

        Returns:
            Tuple of (width, height)

        Raises:
            InvalidImageError: If image is invalid
        """
        pass

    @abstractmethod
    def resize_image(
        self,
        image_data: bytes,
        max_width: int,
        max_height: int,
        quality: int = 90,
    ) -> bytes:
        """
        Resize image maintaining aspect ratio.

        Args:
            image_data: Raw image bytes
            max_width: Maximum width
            max_height: Maximum height
            quality: Output JPEG quality

        Returns:
            Resized image as bytes
        """
        pass

    @abstractmethod
    def compress_image(
        self,
        image_data: bytes,
        quality: int = 85,
    ) -> bytes:
        """
        Compress image to reduce file size.

        Args:
            image_data: Raw image bytes
            quality: Target JPEG quality

        Returns:
            Compressed image as bytes
        """
        pass

    @abstractmethod
    def to_base64(self, image_data: bytes) -> str:
        """Convert image bytes to base64 string."""
        pass

    @abstractmethod
    def from_base64(self, base64_string: str) -> bytes:
        """Convert base64 string to image bytes."""
        pass
```

### 3.3 StorageService

```python
# application/ports/services/storage_service.py

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime, date

@dataclass
class StorageInfo:
    """Storage status information"""
    total_bytes: int
    used_bytes: int
    free_bytes: int
    photo_count: int

@dataclass
class SavedPaths:
    """Paths for saved print job files"""
    composite: Path
    originals: Path

class StorageService(ABC):
    """
    Port for file storage operations.

    Manages saving and organizing output files.
    """

    @abstractmethod
    def get_info(self) -> StorageInfo:
        """Get current storage status."""
        pass

    @abstractmethod
    def save_composite(
        self,
        job_id: str,
        image_data: bytes,
        date: Optional[date] = None,
    ) -> Path:
        """
        Save composite image.

        Args:
            job_id: Print job identifier
            image_data: JPEG image bytes
            date: Date for directory organization

        Returns:
            Path to saved file

        Raises:
            StorageError: If save fails
            StorageFullError: If disk is full
        """
        pass

    @abstractmethod
    def save_originals(
        self,
        job_id: str,
        images: List[bytes],
        date: Optional[date] = None,
    ) -> Path:
        """
        Save original photos as ZIP archive.

        Args:
            job_id: Print job identifier
            images: List of 4 JPEG images
            date: Date for directory organization

        Returns:
            Path to ZIP archive
        """
        pass

    @abstractmethod
    def save_print_job(
        self,
        job_id: str,
        composite: bytes,
        originals: List[bytes],
    ) -> SavedPaths:
        """
        Save all files for a print job.

        Convenience method that saves composite and originals.

        Returns:
            SavedPaths with both paths
        """
        pass

    @abstractmethod
    def get_composite(self, job_id: str) -> Optional[bytes]:
        """
        Retrieve composite image.

        Args:
            job_id: Print job identifier

        Returns:
            Image bytes if found, None otherwise
        """
        pass

    @abstractmethod
    def delete_job_files(self, job_id: str) -> bool:
        """
        Delete all files for a job.

        Returns:
            True if files were deleted
        """
        pass

    @abstractmethod
    def cleanup_old_files(
        self,
        older_than_days: int = 30
    ) -> Tuple[int, int]:
        """
        Delete files older than threshold.

        Args:
            older_than_days: Age threshold in days

        Returns:
            Tuple of (files_deleted, bytes_freed)
        """
        pass

    @abstractmethod
    def compress_old_files(
        self,
        older_than_days: int = 1,
        quality: int = 85
    ) -> int:
        """
        Compress old composites to save space.

        Returns:
            Number of files compressed
        """
        pass

    @abstractmethod
    def list_files(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Path]:
        """List composite files in date range."""
        pass

    @abstractmethod
    def create_archive(
        self,
        start_date: date,
        end_date: date,
    ) -> Path:
        """
        Create ZIP archive of files in date range.

        Returns:
            Path to created archive
        """
        pass
```

### 3.4 SystemService

```python
# application/ports/services/system_service.py

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class ServiceState(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    UNKNOWN = "unknown"

@dataclass
class ServiceInfo:
    """System service information"""
    name: str
    state: ServiceState
    uptime_seconds: Optional[int] = None
    memory_bytes: Optional[int] = None
    error_message: Optional[str] = None

@dataclass
class SystemInfo:
    """Overall system information"""
    hostname: str
    uptime_seconds: int
    memory_total_bytes: int
    memory_used_bytes: int
    cpu_percent: float
    disk_total_bytes: int
    disk_used_bytes: int
    temperature_celsius: Optional[float] = None

class SystemService(ABC):
    """
    Port for system operations.

    Handles service management and system control for admin functions.
    """

    @abstractmethod
    def get_system_info(self) -> SystemInfo:
        """Get overall system information."""
        pass

    @abstractmethod
    def get_service_status(self, service_name: str) -> ServiceInfo:
        """
        Get status of a specific service.

        Args:
            service_name: Name of service (e.g., "nginx", "cups")

        Returns:
            ServiceInfo with current state
        """
        pass

    @abstractmethod
    def get_all_services_status(self) -> Dict[str, ServiceInfo]:
        """Get status of all monitored services."""
        pass

    @abstractmethod
    def restart_service(self, service_name: str) -> bool:
        """
        Restart a system service.

        Args:
            service_name: Service to restart

        Returns:
            True if restart command succeeded

        Raises:
            ServiceError: If restart fails
            PermissionError: If not authorized
        """
        pass

    @abstractmethod
    def restart_all_services(self) -> Dict[str, bool]:
        """
        Restart all application services.

        Returns:
            Dictionary mapping service name to restart success
        """
        pass

    @abstractmethod
    def reboot_system(self, delay_seconds: int = 5) -> bool:
        """
        Schedule system reboot.

        Args:
            delay_seconds: Delay before reboot

        Returns:
            True if reboot scheduled
        """
        pass

    @abstractmethod
    def shutdown_system(self, delay_seconds: int = 5) -> bool:
        """
        Schedule system shutdown.

        Args:
            delay_seconds: Delay before shutdown

        Returns:
            True if shutdown scheduled
        """
        pass

    @abstractmethod
    def get_logs(
        self,
        service_name: Optional[str] = None,
        level: Optional[str] = None,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> List[Dict]:
        """
        Get log entries.

        Args:
            service_name: Filter by service
            level: Filter by level (error, warning, info, debug)
            limit: Maximum entries to return
            since: Only entries after this time

        Returns:
            List of log entry dictionaries
        """
        pass

    @abstractmethod
    def get_timezone(self) -> str:
        """Get current system timezone."""
        pass

    @abstractmethod
    def set_timezone(self, timezone: str) -> bool:
        """
        Set system timezone.

        Args:
            timezone: Timezone string (e.g., "Africa/Kigali")

        Returns:
            True if timezone was set
        """
        pass
```

---

## 4. Frontend Service Interfaces (TypeScript)

### 4.1 ApiService

```typescript
// application/ports/ApiService.ts

export interface ApiService {
  // System
  getSystemStatus(): Promise<SystemStatus>;
  healthCheck(): Promise<HealthResponse>;

  // Print
  submitPrintJob(request: SubmitPrintRequest): Promise<PrintJob>;
  getPrintJobStatus(jobId: string): Promise<PrintJobStatus>;
  retryPrintJob(jobId: string): Promise<PrintJob>;
  abortPrintJob(jobId: string): Promise<void>;

  // Admin
  adminLogin(pin: string): Promise<AuthToken>;
  adminLogout(): Promise<void>;
  getAdminJobs(params: PaginationParams): Promise<PaginatedJobs>;
  getSettings(): Promise<Settings>;
  updateSettings(settings: Partial<Settings>): Promise<Settings>;
  restartService(serviceName: string): Promise<void>;
  testPrint(): Promise<PrintJob>;
  rebootSystem(): Promise<void>;
  shutdownSystem(): Promise<void>;
  getLogs(params: LogParams): Promise<LogEntry[]>;
  downloadPhotos(dateRange: DateRange): Promise<Blob>;
}
```

### 4.2 CameraService

```typescript
// application/ports/CameraService.ts

export interface CameraService {
  /**
   * Initialize camera with given options
   */
  initialize(options: CameraOptions): Promise<void>;

  /**
   * Start camera preview stream
   */
  startPreview(videoElement: HTMLVideoElement): Promise<void>;

  /**
   * Stop camera and release resources
   */
  stop(): void;

  /**
   * Capture current frame as JPEG
   */
  capture(options?: CaptureOptions): Promise<CapturedImage>;

  /**
   * Check if camera is available
   */
  isAvailable(): Promise<boolean>;

  /**
   * Get current camera state
   */
  getState(): CameraState;

  /**
   * Get camera capabilities
   */
  getCapabilities(): MediaTrackCapabilities | null;
}

export interface CameraOptions {
  facingMode: 'user' | 'environment';
  width: number;
  height: number;
  mirrored: boolean;
}

export interface CaptureOptions {
  quality: number;  // 0-1
  mimeType: string;
  maxWidth?: number;
  maxHeight?: number;
}

export interface CapturedImage {
  dataUrl: string;
  width: number;
  height: number;
  sizeBytes: number;
}

export type CameraState =
  | { status: 'idle' }
  | { status: 'initializing' }
  | { status: 'ready'; stream: MediaStream }
  | { status: 'error'; error: CameraError };

export type CameraError =
  | { code: 'permission_denied'; message: string }
  | { code: 'not_found'; message: string }
  | { code: 'not_supported'; message: string }
  | { code: 'in_use'; message: string }
  | { code: 'unknown'; message: string };
```

### 4.3 SoundService

```typescript
// application/ports/SoundService.ts

export interface SoundService {
  /**
   * Initialize audio context (must be called after user interaction)
   */
  initialize(): Promise<void>;

  /**
   * Play a predefined sound effect
   */
  play(sound: SoundEffect): Promise<void>;

  /**
   * Play countdown tick
   */
  playTick(): Promise<void>;

  /**
   * Play capture shutter sound
   */
  playShutter(): Promise<void>;

  /**
   * Play success sound
   */
  playSuccess(): Promise<void>;

  /**
   * Play error sound
   */
  playError(): Promise<void>;

  /**
   * Set volume (0-1)
   */
  setVolume(volume: number): void;

  /**
   * Mute/unmute
   */
  setMuted(muted: boolean): void;

  /**
   * Check if sound is enabled
   */
  isEnabled(): boolean;
}

export type SoundEffect =
  | 'tick'
  | 'shutter'
  | 'success'
  | 'error'
  | 'notification';
```

---

## 5. DTOs (Data Transfer Objects)

### 5.1 PrintJob DTOs

```python
# application/dto/print_job_dto.py

from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from domain.value_objects import PrintStatus, ErrorCode

@dataclass
class SubmitPrintRequest:
    """Request to submit a print job"""
    session_id: str
    images: list[str]  # Base64 encoded
    copies: int
    add_date: bool
    add_logo: bool

@dataclass
class PrintJobDTO:
    """Print job data for API responses"""
    job_id: str
    status: str
    status_display: str
    status_display_ko: str
    progress: int
    message: str
    message_ko: str
    can_go_home: bool
    needs_user_retry: bool
    retry_count: int
    copies: int
    created_at: str
    completed_at: Optional[str]
    preview_image: Optional[str]  # Base64
    error_code: Optional[str]

    @classmethod
    def from_entity(
        cls,
        job: PrintJob,
        preview_image: Optional[str] = None
    ) -> "PrintJobDTO":
        return cls(
            job_id=str(job.id),
            status=job.status.value,
            status_display=job.status.display_name,
            status_display_ko=job.status.display_name_ko,
            progress=job.progress_percent,
            message=cls._get_message(job),
            message_ko=cls._get_message_ko(job),
            can_go_home=job.can_go_home,
            needs_user_retry=job.needs_user_retry,
            retry_count=job.retry_count,
            copies=job.copies,
            created_at=job.created_at.isoformat(),
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            preview_image=preview_image,
            error_code=job.error_code.value if job.error_code else None,
        )

    @staticmethod
    def _get_message(job: PrintJob) -> str:
        if job.error_code:
            return job.error_code.user_message
        return job.status.display_name

    @staticmethod
    def _get_message_ko(job: PrintJob) -> str:
        if job.error_code:
            return job.error_code.user_message_ko
        return job.status.display_name_ko
```

---

## 6. Error Types

```python
# application/exceptions/application_exceptions.py

class ApplicationError(Exception):
    """Base class for application layer errors"""

    def __init__(self, message: str, code: str = "UNKNOWN"):
        self.message = message
        self.code = code
        super().__init__(message)

class ValidationError(ApplicationError):
    """Input validation failed"""

    def __init__(self, message: str, field: str = None):
        super().__init__(message, "VALIDATION_ERROR")
        self.field = field

class NotFoundError(ApplicationError):
    """Resource not found"""

    def __init__(self, resource: str, identifier: str):
        super().__init__(f"{resource} not found: {identifier}", "NOT_FOUND")
        self.resource = resource
        self.identifier = identifier

class PrinterError(ApplicationError):
    """Printer-related error"""

    def __init__(self, message: str, code: str = "PRINTER_ERROR"):
        super().__init__(message, code)

class StorageError(ApplicationError):
    """Storage-related error"""

    def __init__(self, message: str, code: str = "STORAGE_ERROR"):
        super().__init__(message, code)

class AuthenticationError(ApplicationError):
    """Authentication failed"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR")
```

---

*Next: See `docs/infrastructure/IMPLEMENTATIONS.md` for concrete implementations*
