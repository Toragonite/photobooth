# UC-204: Cleanup Storage

## Summary

System automatically or manually cleans up old session data to free storage space. Removes photos and composites from sessions older than the configured retention period.

---

## Actors

| Actor | Type | Description |
|-------|------|-------------|
| **System** | Primary | Background cleanup daemon |
| **Admin** | Secondary | Manual cleanup trigger |

---

## Preconditions

| ID | Condition |
|----|-----------|
| PRE-1 | Storage path is accessible |
| PRE-2 | Database is accessible |
| PRE-3 | Cleanup retention period configured |

---

## Trigger

- **Automatic**: Daily scheduled task (2:00 AM local time)
- **Manual**: Admin triggers cleanup from dashboard

---

## Main Flow (Automatic)

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Step                                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ Scheduled task triggers at 2:00 AM                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ Check current storage usage                                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ Query sessions older than retention period (default: 30 days) │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4   │ For each eligible session:                                    │
│     │ - Status must be COMPLETED, ABANDONED, or FAILED              │
│     │ - No pending print jobs                                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5   │ For each session to clean:                                    │
│     │ a. Delete photo files from disk                               │
│     │ b. Delete composite file from disk                            │
│     │ c. Update session record: files_cleaned = true                │
│     │ d. Keep session metadata for statistics                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6   │ Log cleanup summary:                                          │
│     │ - Sessions cleaned                                            │
│     │ - Space freed                                                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7   │ Update storage status cache                                   │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Alternative Flows

### AF-1: Manual Cleanup from Dashboard

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 1a  │ Admin navigates to Storage section on dashboard               │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1b  │ Admin taps [Clean Old Data]                                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1c  │ Dialog shows cleanup options:                                 │
│     │ - Sessions older than: [7] [14] [30] [60] days                │
│     │ - Estimated space to free: 12.5 GB                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1d  │ Admin selects retention period and confirms                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1e  │ Frontend sends: POST /api/admin/cleanup                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1f  │ Backend processes cleanup (may take time)                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1g  │ Return summary: "Cleaned 234 sessions, freed 12.5 GB"         │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-2: Emergency Cleanup (Storage Critical)

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 2a  │ Storage usage exceeds critical threshold (95%)                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2b  │ System triggers emergency cleanup                             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2c  │ Reduce retention period temporarily (7 days)                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2d  │ Process cleanup immediately                                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2e  │ If still critical: Clean sessions older than 3 days           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2f  │ Log emergency cleanup event                                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2g  │ Notify admin via dashboard alert                              │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-3: Cleanup Preview (Dry Run)

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 1a  │ Admin requests cleanup preview                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1b  │ GET /api/admin/cleanup/preview?days=30                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1c  │ Backend calculates without deleting:                          │
│     │ - Number of sessions to clean                                 │
│     │ - Total file size to remove                                   │
│     │ - Estimated new storage usage                                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1d  │ Return preview data for admin review                          │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Exception Flows

### EX-1: File Deletion Fails

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Cannot delete file (permission, file locked, etc.)            │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Log warning with file path                                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Continue with next file (don't stop entire cleanup)           │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Track failed deletions in cleanup report                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ E5  │ Session record NOT marked as cleaned                          │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-2: Database Error

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Cannot query or update database                               │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Log error                                                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Retry with backoff (1s, 2s, 4s)                               │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ If all retries fail: Abort cleanup, schedule retry            │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-3: Cleanup Interrupted

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ System restart during cleanup                                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Partially cleaned sessions may exist                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ On next startup: Run integrity check                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Mark sessions with missing files as cleaned                   │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Postconditions

| ID | Condition |
|----|-----------|
| POST-1 | Old session files deleted from disk |
| POST-2 | Session metadata preserved (for statistics) |
| POST-3 | Storage usage reduced |
| POST-4 | Cleanup logged for audit |

---

## Business Rules

| ID | Rule |
|----|------|
| CLN-BR-1 | Default retention: 30 days |
| CLN-BR-2 | Minimum retention: 1 day (emergency only) |
| CLN-BR-3 | Only clean terminal sessions (COMPLETED/ABANDONED/FAILED) |
| CLN-BR-4 | Never delete sessions with pending print jobs |
| CLN-BR-5 | Keep session records, only delete files |
| CLN-BR-6 | Emergency cleanup at 95% storage |
| CLN-BR-7 | Scheduled cleanup: 2:00 AM daily |

---

## Data Preserved vs Deleted

| Data | Action | Reason |
|------|--------|--------|
| Photo files (.jpg) | **Delete** | Large files, space recovery |
| Composite files (.jpg) | **Delete** | Large files, space recovery |
| Session record | **Keep** | Statistics, audit trail |
| Print job records | **Keep** | History, debugging |
| Thumbnails | **Delete** | No longer needed |

---

## UI/UX Requirements

### Storage Management Section

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ┌─── Storage ──────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │  💾 SD Card (256GB)                                      │   │
│  │                                                          │   │
│  │  Used:     45.2 GB / 256 GB                              │   │
│  │  ████████████░░░░░░░░░░░░░░░░░░░░  17.7%                 │   │
│  │                                                          │   │
│  │  Photos:   1,234 sessions (42.1 GB)                      │   │
│  │  System:   3.1 GB                                        │   │
│  │                                                          │   │
│  │                                                          │   │
│  │  ┌──────────────────────────────────────────────────┐    │   │
│  │  │            Clean Old Sessions                    │    │   │
│  │  │                                                  │    │   │
│  │  │  Remove photos older than:                       │    │   │
│  │  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                │    │   │
│  │  │  │ 7d  │ │ 14d │ │ 30d │ │ 60d │                │    │   │
│  │  │  └─────┘ └─────┘ └─────┘ └─────┘                │    │   │
│  │  │           ↑ selected                             │    │   │
│  │  │                                                  │    │   │
│  │  │  Preview:                                        │    │   │
│  │  │  • 456 sessions will be cleaned                  │    │   │
│  │  │  • ~15.2 GB will be freed                        │    │   │
│  │  │  • New usage: ~30 GB (11.7%)                     │    │   │
│  │  │                                                  │    │   │
│  │  │  ┌────────────────────────────────────────────┐  │    │   │
│  │  │  │          🗑️ Clean Now                      │  │    │   │
│  │  │  └────────────────────────────────────────────┘  │    │   │
│  │  │                                                  │    │   │
│  │  └──────────────────────────────────────────────────┘    │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Cleanup Progress

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│     ┌─────────────────────────────────────────────────────┐     │
│     │                                                     │     │
│     │              Cleaning Storage...                    │     │
│     │                                                     │     │
│     │  ████████████████░░░░░░░░░░░░░░░░  45%              │     │
│     │                                                     │     │
│     │  Processed: 205 / 456 sessions                      │     │
│     │  Space freed: 6.8 GB                                │     │
│     │                                                     │     │
│     │  Please wait...                                     │     │
│     │                                                     │     │
│     └─────────────────────────────────────────────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Cleanup Complete

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│     ┌─────────────────────────────────────────────────────┐     │
│     │                                                     │     │
│     │              ✓ Cleanup Complete                     │     │
│     │                                                     │     │
│     │  Sessions cleaned:  456                             │     │
│     │  Space freed:       15.2 GB                         │     │
│     │  Time taken:        2 min 34 sec                    │     │
│     │                                                     │     │
│     │  New storage usage: 30 GB (11.7%)                   │     │
│     │                                                     │     │
│     │              ┌────────────────┐                     │     │
│     │              │      Done      │                     │     │
│     │              └────────────────┘                     │     │
│     │                                                     │     │
│     └─────────────────────────────────────────────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technical Notes

### API Endpoints

```typescript
// GET /api/admin/cleanup/preview
interface CleanupPreviewRequest {
  days: number;  // Retention period
}

interface CleanupPreviewResponse {
  sessions_count: number;
  files_count: number;
  total_size_bytes: number;
  estimated_new_usage_percent: number;
}

// POST /api/admin/cleanup
interface CleanupRequest {
  days: number;  // Retention period
}

interface CleanupResponse {
  success: boolean;
  sessions_cleaned: number;
  files_deleted: number;
  bytes_freed: number;
  duration_seconds: number;
  errors: string[];
}
```

### Cleanup Service Implementation

```python
# Storage cleanup service

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

class StorageCleanupService:
    def __init__(
        self,
        session_repo: SessionRepository,
        storage_path: Path,
    ):
        self._sessions = session_repo
        self._storage_path = storage_path

    async def preview(self, days: int) -> CleanupPreviewResponse:
        """Preview cleanup without deleting."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        sessions = await self._sessions.get_cleanable_before(cutoff)

        total_size = 0
        files_count = 0

        for session in sessions:
            session_path = self._storage_path / session.id
            if session_path.exists():
                for file in session_path.rglob('*'):
                    if file.is_file():
                        total_size += file.stat().st_size
                        files_count += 1

        disk = shutil.disk_usage(self._storage_path)
        new_used = disk.used - total_size
        new_percent = (new_used / disk.total) * 100

        return CleanupPreviewResponse(
            sessions_count=len(sessions),
            files_count=files_count,
            total_size_bytes=total_size,
            estimated_new_usage_percent=new_percent,
        )

    async def cleanup(
        self,
        days: int,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> CleanupResponse:
        """Perform cleanup of old sessions."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        start_time = time.time()

        sessions = await self._sessions.get_cleanable_before(cutoff)
        total = len(sessions)

        cleaned = 0
        files_deleted = 0
        bytes_freed = 0
        errors = []

        for i, session in enumerate(sessions):
            try:
                result = await self._clean_session(session)
                files_deleted += result['files']
                bytes_freed += result['bytes']
                cleaned += 1

            except Exception as e:
                errors.append(f"Session {session.id}: {e}")
                logger.error(f"Failed to clean session {session.id}: {e}")

            if progress_callback:
                progress_callback(i + 1, total)

        duration = time.time() - start_time

        logger.info(
            f"Cleanup completed: {cleaned} sessions, "
            f"{bytes_freed / 1024 / 1024:.1f} MB freed in {duration:.1f}s"
        )

        return CleanupResponse(
            success=len(errors) == 0,
            sessions_cleaned=cleaned,
            files_deleted=files_deleted,
            bytes_freed=bytes_freed,
            duration_seconds=int(duration),
            errors=errors,
        )

    async def _clean_session(self, session: Session) -> dict:
        """Clean a single session's files."""
        session_path = self._storage_path / session.id

        files = 0
        bytes_freed = 0

        if session_path.exists():
            # Count before deletion
            for file in session_path.rglob('*'):
                if file.is_file():
                    files += 1
                    bytes_freed += file.stat().st_size

            # Delete directory
            shutil.rmtree(session_path)

        # Update session record
        session.files_cleaned = True
        session.cleaned_at = datetime.utcnow()
        await self._sessions.update(session)

        return {'files': files, 'bytes': bytes_freed}


# Scheduled task

from apscheduler.schedulers.asyncio import AsyncIOScheduler

def setup_scheduled_cleanup(app: FastAPI):
    scheduler = AsyncIOScheduler()

    async def daily_cleanup():
        settings = await settings_repo.get_all()
        days = settings.get('cleanup_days', 30)

        cleanup_service = StorageCleanupService(session_repo, storage_path)
        await cleanup_service.cleanup(days)

    # Run at 2:00 AM daily
    scheduler.add_job(
        daily_cleanup,
        'cron',
        hour=2,
        minute=0,
    )

    scheduler.start()
```

### Emergency Cleanup Trigger

```python
# Storage monitor with emergency cleanup

class StorageMonitor:
    WARNING_THRESHOLD = 80  # percent
    CRITICAL_THRESHOLD = 95  # percent

    async def check_and_cleanup(self):
        """Check storage and trigger emergency cleanup if needed."""
        disk = shutil.disk_usage(storage_path)
        usage_percent = (disk.used / disk.total) * 100

        if usage_percent >= self.CRITICAL_THRESHOLD:
            logger.warning(f"Critical storage: {usage_percent:.1f}%")

            # Emergency cleanup - 7 days
            await cleanup_service.cleanup(days=7)

            # Check again
            disk = shutil.disk_usage(storage_path)
            usage_percent = (disk.used / disk.total) * 100

            if usage_percent >= self.CRITICAL_THRESHOLD:
                # More aggressive - 3 days
                logger.warning("Still critical, aggressive cleanup")
                await cleanup_service.cleanup(days=3)
```

---

## Related Use Cases

- **UC-102**: View System Status (shows storage usage)
- **UC-104**: Update Settings (configure retention period)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
