# UC-108: Download Photos

## Summary

Admin downloads photos from completed sessions for backup or sharing. Supports downloading individual sessions or bulk export of multiple sessions.

---

## Actors

| Actor | Type | Description |
|-------|------|-------------|
| **Admin** | Primary | Operator downloading photos |
| **System** | Secondary | Packages and serves files |

---

## Preconditions

| ID | Condition |
|----|-----------|
| PRE-1 | Admin is authenticated |
| PRE-2 | Sessions with photos exist |
| PRE-3 | Photo files are on disk |

---

## Trigger

Admin selects session(s) and taps download button.

---

## Main Flow (Single Session)

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Step                                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ Admin navigates to Print History or Photo Gallery             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ Admin views session details                                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ Admin taps [Download] button                                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4   │ System shows download options:                                │
│     │ - Composite only (1 file)                                     │
│     │ - All photos (4 files + composite)                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5   │ Admin selects option                                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6   │ Frontend requests: GET /api/admin/session/{id}/download       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7   │ Backend creates ZIP archive (if multiple files)               │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8   │ Return file for download                                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 9   │ Browser prompts save location                                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 10  │ File downloads to admin's device                              │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Alternative Flows

### AF-1: Bulk Download (Multiple Sessions)

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 1a  │ Admin is on session list view                                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2a  │ Admin selects multiple sessions (checkboxes)                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3a  │ Bulk action bar appears: "5 sessions selected"                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4a  │ Admin taps [Download Selected]                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5a  │ System shows progress: "Preparing download..."                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6a  │ Backend creates ZIP with all sessions' files                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7a  │ Large downloads may take time, show progress                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8a  │ Return ZIP file for download                                  │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-2: Download by Date Range

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 1a  │ Admin taps [Export] button                                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2a  │ Export dialog appears:                                        │
│     │ - Date range selector                                         │
│     │ - Include options (composite only / all files)                │
│     │ - Estimated size                                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3a  │ Admin selects date range: "Last 7 days"                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4a  │ System shows: "45 sessions, ~2.3 GB"                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5a  │ Admin confirms export                                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6a  │ Backend generates export in background                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7a  │ When ready: Download link available                           │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-3: Download to USB Drive

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 1a  │ Admin connects USB drive to Raspberry Pi                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2a  │ System detects USB drive                                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3a  │ Export dialog shows "USB Drive" as destination option         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4a  │ Admin selects sessions and "Export to USB"                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5a  │ System copies files directly to USB drive                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6a  │ No network transfer needed (faster for large exports)         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7a  │ Notification: "Export complete. Safe to remove USB."          │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Exception Flows

### EX-1: Files Already Cleaned

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Session files were deleted by cleanup process                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Display message: "Photos no longer available"                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Session record shows "Files cleaned on [date]"                │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-2: Partial Files Missing

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Some photos exist but others are missing                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Show warning: "3 of 4 photos available"                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Offer to download available files anyway                      │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-3: Download Timeout (Large Export)

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Export takes too long, connection times out                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Backend continues preparing in background                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Show: "Export is being prepared. Check back shortly."         │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Provide download link when ready                              │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Postconditions

| ID | Condition |
|----|-----------|
| POST-1 | Admin has downloaded photos |
| POST-2 | Download logged for audit |
| POST-3 | Original files unchanged |

---

## Business Rules

| ID | Rule |
|----|------|
| DL-BR-1 | Only admins can download photos |
| DL-BR-2 | Bulk download max: 100 sessions |
| DL-BR-3 | Large exports (>500MB) prepared async |
| DL-BR-4 | Export links expire after 1 hour |
| DL-BR-5 | Downloads logged with admin ID |

---

## File Naming Convention

```
Single session:
  photobooth_2024-01-13_143200_abc123.zip
  └── session_abc123/
      ├── composite.jpg
      ├── photo_1.jpg
      ├── photo_2.jpg
      ├── photo_3.jpg
      └── photo_4.jpg

Bulk export:
  photobooth_export_2024-01-13.zip
  ├── session_abc123/
  │   ├── composite.jpg
  │   └── ...
  ├── session_def456/
  │   ├── composite.jpg
  │   └── ...
  └── manifest.json
```

---

## UI/UX Requirements

### Session Detail Download

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Session: abc-123-def-456                                       │
│  Date: 2024-01-13 14:32                                         │
│  Status: ✅ Completed                                            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │            [Composite Image Preview]                     │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Photos: 4 files (12.3 MB total)                                │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Download Options                        │ │
│  │                                                            │ │
│  │  ○ Composite only (3.2 MB)                                │ │
│  │  ● All photos + composite (12.3 MB)                       │ │
│  │                                                            │ │
│  │  ┌────────────────────────────────────────────────────┐    │ │
│  │  │              ⬇️ Download                           │    │ │
│  │  └────────────────────────────────────────────────────┘    │ │
│  │                                                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Bulk Selection

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ☑ Session abc-123  │  2024-01-13 14:32  │  ✅ Completed         │
│  ☑ Session def-456  │  2024-01-13 14:28  │  ✅ Completed         │
│  ☐ Session ghi-789  │  2024-01-13 14:15  │  ✅ Completed         │
│  ☑ Session jkl-012  │  2024-01-13 14:02  │  ✅ Completed         │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  3 sessions selected (36.9 MB)                             │ │
│  │                                                            │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │ │
│  │  │ Select All   │  │ Clear        │  │ ⬇️ Download      │  │ │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘  │ │
│  │                                                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Export Dialog

```
┌─────────────────────────────────────────────────────────────────┐
│     ┌─────────────────────────────────────────────────────┐     │
│     │                                                     │     │
│     │              Export Photos                          │     │
│     │                                                     │     │
│     │   Date Range:                                       │     │
│     │   ┌─────────────────┐  ┌─────────────────┐          │     │
│     │   │ Today        ▼  │  │ Last 7 Days  ▼  │          │     │
│     │   └─────────────────┘  └─────────────────┘          │     │
│     │                                                     │     │
│     │   Include:                                          │     │
│     │   ○ Composites only                                │     │
│     │   ● All photos                                     │     │
│     │                                                     │     │
│     │   ─────────────────────────────────────────────    │     │
│     │   Sessions: 45                                      │     │
│     │   Estimated size: 2.3 GB                           │     │
│     │   ─────────────────────────────────────────────    │     │
│     │                                                     │     │
│     │   ┌──────────────┐     ┌──────────────────┐         │     │
│     │   │    Cancel    │     │   Start Export   │         │     │
│     │   └──────────────┘     └──────────────────┘         │     │
│     │                                                     │     │
│     └─────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

### Export Progress

```
┌─────────────────────────────────────────────────────────────────┐
│     ┌─────────────────────────────────────────────────────┐     │
│     │                                                     │     │
│     │              Preparing Export...                    │     │
│     │                                                     │     │
│     │  ████████████████░░░░░░░░░░░░░░░░  45%              │     │
│     │                                                     │     │
│     │  Processing session 20 of 45                        │     │
│     │  Files added: 82                                    │     │
│     │  Size so far: 1.1 GB                               │     │
│     │                                                     │     │
│     │  ┌──────────────────────────────────────────────┐   │     │
│     │  │              Cancel                          │   │     │
│     │  └──────────────────────────────────────────────┘   │     │
│     │                                                     │     │
│     └─────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technical Notes

### API Endpoints

```typescript
// GET /api/admin/session/{session_id}/download
// Returns single session ZIP or single file

interface DownloadSessionRequest {
  session_id: string;
  type: 'composite' | 'all';  // Query param
}

// Response: File download (application/zip or image/jpeg)

// POST /api/admin/export
// Create bulk export job

interface BulkExportRequest {
  session_ids?: string[];    // Specific sessions
  from_date?: string;        // Or date range
  to_date?: string;
  include: 'composite' | 'all';
}

interface BulkExportResponse {
  export_id: string;
  status: 'preparing' | 'ready' | 'failed';
  download_url?: string;     // When ready
  estimated_size_bytes: number;
  session_count: number;
}

// GET /api/admin/export/{export_id}/status
// Check export status

// GET /api/admin/export/{export_id}/download
// Download completed export
```

### Backend Implementation

```python
# Photo download service

import zipfile
from pathlib import Path
from tempfile import NamedTemporaryFile
from fastapi.responses import FileResponse, StreamingResponse

class PhotoDownloadService:
    def __init__(self, session_repo: SessionRepository, storage_path: Path):
        self._sessions = session_repo
        self._storage_path = storage_path

    async def download_session(
        self,
        session_id: str,
        include_all: bool = True,
    ) -> FileResponse:
        """Download a single session's photos."""
        session = await self._sessions.get_by_id(session_id)
        if not session:
            raise SessionNotFoundError(session_id)

        session_path = self._storage_path / session_id

        if not session_path.exists():
            raise FilesNotFoundError("Session files have been cleaned")

        if include_all:
            # Create ZIP with all files
            zip_path = await self._create_session_zip(session, session_path)
            filename = f"photobooth_{session.created_at.strftime('%Y%m%d_%H%M%S')}_{session_id[:8]}.zip"

            return FileResponse(
                path=zip_path,
                filename=filename,
                media_type='application/zip',
            )
        else:
            # Just composite
            composite_path = session_path / 'composite.jpg'
            if not composite_path.exists():
                raise FilesNotFoundError("Composite file not found")

            filename = f"photobooth_{session.created_at.strftime('%Y%m%d_%H%M%S')}.jpg"

            return FileResponse(
                path=composite_path,
                filename=filename,
                media_type='image/jpeg',
            )

    async def _create_session_zip(
        self,
        session: Session,
        session_path: Path,
    ) -> Path:
        """Create ZIP archive for session."""
        with NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
            with zipfile.ZipFile(tmp.name, 'w', zipfile.ZIP_DEFLATED) as zf:
                folder_name = f"session_{session.id[:8]}"

                # Add composite
                composite = session_path / 'composite.jpg'
                if composite.exists():
                    zf.write(composite, f"{folder_name}/composite.jpg")

                # Add individual photos
                for i in range(1, 5):
                    photo = session_path / f"photo_{i}.jpg"
                    if photo.exists():
                        zf.write(photo, f"{folder_name}/photo_{i}.jpg")

            return Path(tmp.name)

    async def create_bulk_export(
        self,
        session_ids: list[str] | None,
        from_date: date | None,
        to_date: date | None,
        include_all: bool,
    ) -> str:
        """Create async bulk export job."""
        export_id = str(uuid.uuid4())

        # Determine sessions
        if session_ids:
            sessions = [await self._sessions.get_by_id(id) for id in session_ids]
        else:
            sessions = await self._sessions.get_by_date_range(from_date, to_date)

        sessions = [s for s in sessions if s and not s.files_cleaned]

        # Start background task
        asyncio.create_task(
            self._process_export(export_id, sessions, include_all)
        )

        return export_id

    async def _process_export(
        self,
        export_id: str,
        sessions: list[Session],
        include_all: bool,
    ):
        """Background task to create export ZIP."""
        export_path = self._storage_path / 'exports' / f"{export_id}.zip"
        export_path.parent.mkdir(exist_ok=True)

        try:
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                manifest = {
                    'export_id': export_id,
                    'created_at': datetime.utcnow().isoformat(),
                    'sessions': [],
                }

                for session in sessions:
                    session_path = self._storage_path / session.id
                    if not session_path.exists():
                        continue

                    folder = f"session_{session.id[:8]}"

                    # Add files
                    if include_all:
                        for file in session_path.glob('*.jpg'):
                            zf.write(file, f"{folder}/{file.name}")
                    else:
                        composite = session_path / 'composite.jpg'
                        if composite.exists():
                            zf.write(composite, f"{folder}/composite.jpg")

                    manifest['sessions'].append({
                        'id': session.id,
                        'created_at': session.created_at.isoformat(),
                    })

                # Add manifest
                zf.writestr('manifest.json', json.dumps(manifest, indent=2))

            # Update export status to ready
            await self._update_export_status(export_id, 'ready')

        except Exception as e:
            logger.error(f"Export {export_id} failed: {e}")
            await self._update_export_status(export_id, 'failed', str(e))
```

---

## Related Use Cases

- **UC-103**: View Print History (download from history)
- **UC-204**: Cleanup Storage (files may be cleaned)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
