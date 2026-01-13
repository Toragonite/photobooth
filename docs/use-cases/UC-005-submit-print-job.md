# UC-005: Submit Print Job

## Summary

User confirms the composite preview and submits a print job with selected options (copies, date stamp, logo). System processes the images, creates the composite, and initiates printing.

---

## Actors

| Actor | Type | Description |
|-------|------|-------------|
| **User** | Primary | Person requesting the print |
| **Frontend** | Secondary | Collects data, sends request |
| **Backend** | Secondary | Processes images, manages print queue |
| **Printer** | Secondary | Physical printing device |

---

## Preconditions

| ID | Condition |
|----|-----------|
| PRE-1 | Active session exists with exactly 4 captured photos |
| PRE-2 | User is on Preview page |
| PRE-3 | System is operational |
| PRE-4 | No active print job for this session |

---

## Trigger

User taps the "Print" / "인쇄" button on the Preview page.

---

## Main Flow

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Step                                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ User configures print options:                                 │
│     │ - Copies: 1-4 (default: 2)                                     │
│     │ - Add date stamp: yes/no                                       │
│     │ - Add logo: yes/no                                             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ User taps "Print" button                                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ Frontend disables Print button, shows "Submitting..."          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4   │ Frontend sends POST /api/print with:                           │
│     │ - session_id                                                   │
│     │ - images[4] (base64 JPEG)                                      │
│     │ - copies                                                       │
│     │ - add_date                                                     │
│     │ - add_logo                                                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5   │ Backend validates request:                                     │
│     │ - Exactly 4 images                                             │
│     │ - Valid base64 encoding                                        │
│     │ - Copies in range 1-4                                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6   │ Backend creates PrintJob entity:                               │
│     │ - Generate job_id (UUID short form)                            │
│     │ - Set status: PROCESSING                                       │
│     │ - Record created_at                                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7   │ Backend calls ImageProcessor.create_composite():               │
│     │ - Decode 4 base64 images                                       │
│     │ - Create 1200x1800 canvas                                      │
│     │ - Resize/crop each photo to fit quadrant                       │
│     │ - Arrange in 2x2 grid with padding                             │
│     │ - Add date stamp if requested                                  │
│     │ - Add logo if requested                                        │
│     │ - Save as JPEG (quality: 95)                                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8   │ Backend calls StorageService.save():                           │
│     │ - Save composite to /data/output/YYYY/MM/DD/                   │
│     │ - Archive originals as ZIP                                     │
│     │ - Update job with file paths                                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 9   │ Backend updates job status: SENDING                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ 10  │ Backend calls PrinterService.print_file():                     │
│     │ - Connect to CUPS                                              │
│     │ - Submit print job with options                                │
│     │ - Receive cups_job_id                                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 11  │ Backend updates job:                                           │
│     │ - status: PRINTING                                             │
│     │ - cups_job_id: received ID                                     │
│     │ - Save to repository                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 12  │ Backend starts background job monitor thread                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 13  │ Backend returns response:                                      │
│     │ - job_id                                                       │
│     │ - status: PRINTING                                             │
│     │ - preview_image (base64 composite)                             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 14  │ Frontend receives response                                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ 15  │ Frontend stores job_id in session/localStorage                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 16  │ Frontend navigates to Printing page (/printing)                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 17  │ Continue to UC-006: Monitor Print Status                       │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Alternative Flows

### AF-1: Printer Offline at Submission

```
Trigger: PrinterService reports printer offline

┌─────┬────────────────────────────────────────────────────────────────┐
│ 10a │ PrinterService.is_ready() returns false                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ 10b │ Backend still creates composite (steps 7-8 complete)           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 10c │ Backend sets job status: ERROR                                 │
│     │ - error_code: PRINTER_OFFLINE                                  │
│     │ - retry_count: 0                                               │
├─────┼────────────────────────────────────────────────────────────────┤
│ 10d │ Backend queues job for auto-retry (see UC-203)                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 10e │ Backend returns response with status: ERROR, retry scheduled   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 10f │ Frontend navigates to Printing page (will show retry status)   │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-2: Duplicate Submission Prevention

```
Trigger: User double-taps Print button

┌─────┬────────────────────────────────────────────────────────────────┐
│ 2a  │ First tap disables button immediately                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2b  │ Subsequent taps are ignored (button disabled)                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2c  │ Backend also checks: no active job for this session_id        │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2d  │ If duplicate detected, return existing job_id                 │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Exception Flows

### EX-1: Invalid Image Data

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Backend validates base64 images                               │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ One or more images fail validation:                           │
│     │ - Invalid base64 encoding                                     │
│     │ - Not a valid JPEG/PNG                                        │
│     │ - Corrupted image data                                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Backend returns HTTP 400:                                     │
│     │ - error_code: INVALID_IMAGE                                   │
│     │ - message: "Photo X is invalid"                               │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Frontend shows error, offers to retake photos                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ E5  │ No retry (not a transient error)                              │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-2: Image Processing Failure

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ ImageProcessor throws exception during composite creation     │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Backend logs full error details                               │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Backend returns HTTP 500:                                     │
│     │ - error_code: PROCESSING_ERROR                                │
│     │ - message: "Failed to create composite"                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Frontend shows error page                                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ E5  │ No auto-retry (likely a bug, needs investigation)             │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-3: Storage Full

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ StorageService.save() fails due to disk full                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Backend attempts emergency cleanup of old files               │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ If cleanup frees space, retry save                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ If still fails, return HTTP 507:                              │
│     │ - error_code: STORAGE_FULL                                    │
│     │ - message: "Storage full, contact admin"                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ E5  │ Log critical alert for admin                                  │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-4: CUPS Connection Failure

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ PrinterService cannot connect to CUPS daemon                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Backend saves composite (image is safe)                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Backend creates job with status: ERROR                        │
│     │ - error_code: CUPS_UNAVAILABLE                                │
│     │ - retry_count: 0                                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Backend schedules auto-retry in 3 seconds                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ E5  │ Return job with retry information                             │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-5: Network Timeout

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Frontend fetch() times out (> 30 seconds)                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Frontend shows "Connection timeout" error                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Offer "Retry" button                                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Note: Job may have been created on backend                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ E5  │ On retry, backend detects existing job, returns it            │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Postconditions

### Success

| ID | Condition |
|----|-----------|
| POST-1 | PrintJob exists in database with status PRINTING |
| POST-2 | Composite image saved to storage |
| POST-3 | Original photos archived |
| POST-4 | Print job submitted to CUPS |
| POST-5 | Background monitor thread running |
| POST-6 | User on Printing page |

### Failure

| ID | Condition |
|----|-----------|
| POST-F1 | PrintJob exists with status ERROR (if past step 6) |
| POST-F2 | Composite saved if processing succeeded |
| POST-F3 | Error logged with full details |
| POST-F4 | User informed of specific error |

---

## Business Rules

| ID | Rule |
|----|------|
| BR-1 | Exactly 4 images required, no more, no less |
| BR-2 | Copies must be 1-4 (validated) |
| BR-3 | Each image max size: 5MB after base64 decode |
| BR-4 | Composite output: 1200x1800 pixels @ 300 DPI |
| BR-5 | JPEG quality: 95 for print, 85 for storage |
| BR-6 | One job per session (prevent duplicates) |
| BR-7 | Job ID format: 8 character alphanumeric |

---

## Data Requirements

### Request Schema

```typescript
interface SubmitPrintRequest {
  session_id: string;              // UUID
  images: string[];                // Exactly 4 base64 JPEGs
  copies: number;                  // 1-4
  add_date: boolean;
  add_logo: boolean;
}
```

### Response Schema

```typescript
interface SubmitPrintResponse {
  job_id: string;                  // e.g., "abc12345"
  status: PrintStatus;             // "processing" | "sending" | "printing" | "error"
  message: string;                 // Human-readable status
  message_ko: string;              // Korean translation
  preview_image: string;           // Base64 composite (for display)
  created_at: string;              // ISO timestamp
  error_code?: string;             // If status is error
  retry_scheduled?: boolean;       // If auto-retry planned
}
```

### PrintJob Entity

```python
@dataclass
class PrintJob:
    job_id: JobId
    session_id: SessionId
    status: PrintStatus
    cups_job_id: Optional[int]
    copies: int
    add_date: bool
    add_logo: bool
    composite_path: Optional[Path]
    originals_path: Optional[Path]
    error_code: Optional[str]
    error_message: Optional[str]
    retry_count: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
```

---

## UI/UX Requirements

### Preview Page (Before Submit)

```
┌─────────────────────────────────────────────────────────────────┐
│  [🏠]                    Preview / 미리보기                       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │              [4-Cut Composite Preview]                  │    │
│  │                                                         │    │
│  │                   2024.01.13                            │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│     Copies / 매수:  [ - ]  [2]  [ + ]                           │
│                                                                 │
│     [✓] Add date / 날짜 추가                                     │
│     [ ] Add logo / 로고 추가                                     │
│                                                                 │
│                                                                 │
│  ┌────────────────┐                    ┌────────────────────┐   │
│  │  🔄 Retake     │                    │  🖨️ Print          │   │
│  │     다시 촬영   │                    │     인쇄 (2장)      │   │
│  └────────────────┘                    └────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### During Submission (Loading State)

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                    Submitting...                                │
│                    제출 중...                                    │
│                                                                 │
│                       [Spinner]                                 │
│                                                                 │
│               Please wait / 잠시만 기다려주세요                   │
│                                                                 │
│           (All buttons disabled, no navigation)                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technical Notes

### Frontend Implementation

```typescript
// hooks/usePrintJob.ts

const usePrintJob = () => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<PrintError | null>(null);

  const submit = async (request: SubmitPrintRequest): Promise<PrintJob> => {
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await apiService.submitPrintJob(request);

      // Store job_id for recovery
      sessionStorage.setItem('active_job_id', response.job_id);

      return response;
    } catch (err) {
      const printError = mapToPrintError(err);
      setError(printError);
      throw printError;
    } finally {
      setIsSubmitting(false);
    }
  };

  return { submit, isSubmitting, error };
};
```

### Backend Use Case Implementation

```python
# application/use_cases/print/submit_print_job.py

class SubmitPrintJobUseCase:
    def __init__(
        self,
        print_job_repo: PrintJobRepository,
        image_processor: ImageProcessor,
        storage_service: StorageService,
        printer_service: PrinterService,
    ):
        self._print_job_repo = print_job_repo
        self._image_processor = image_processor
        self._storage_service = storage_service
        self._printer_service = printer_service

    def execute(self, request: SubmitPrintRequest) -> PrintJobDTO:
        # 1. Validate
        self._validate(request)

        # 2. Check for existing job (idempotency)
        existing = self._print_job_repo.find_by_session(request.session_id)
        if existing and existing.status not in [PrintStatus.ERROR, PrintStatus.ABORTED]:
            return PrintJobDTO.from_entity(existing)

        # 3. Create job entity
        job = PrintJob.create(
            session_id=request.session_id,
            copies=request.copies,
            add_date=request.add_date,
            add_logo=request.add_logo,
        )
        self._print_job_repo.save(job)

        try:
            # 4. Create composite
            composite = self._image_processor.create_composite(
                images=request.images,
                add_date=request.add_date,
                add_logo=request.add_logo,
            )

            # 5. Save files
            paths = self._storage_service.save_print_job(
                job_id=job.job_id,
                composite=composite,
                originals=request.images,
            )
            job.set_paths(paths.composite, paths.originals)
            job.transition_to(PrintStatus.SENDING)
            self._print_job_repo.update(job)

            # 6. Submit to printer
            result = self._printer_service.print_file(
                file_path=paths.composite,
                copies=request.copies,
            )

            if result.success:
                job.set_cups_job_id(result.cups_job_id)
                job.transition_to(PrintStatus.PRINTING)
            else:
                job.mark_error(result.error_code, result.error_message)

            self._print_job_repo.update(job)

            # 7. Start monitor (if printing)
            if job.status == PrintStatus.PRINTING:
                self._start_monitor(job.job_id)

            return PrintJobDTO.from_entity(job, preview_image=composite)

        except Exception as e:
            job.mark_error("PROCESSING_ERROR", str(e))
            self._print_job_repo.update(job)
            raise
```

---

## Sequence Diagram

```
┌──────┐          ┌──────────┐          ┌──────────┐          ┌─────────┐
│ User │          │ Frontend │          │ Backend  │          │  CUPS   │
└──┬───┘          └────┬─────┘          └────┬─────┘          └────┬────┘
   │                   │                     │                     │
   │ Tap Print         │                     │                     │
   │──────────────────►│                     │                     │
   │                   │                     │                     │
   │                   │ POST /api/print     │                     │
   │                   │────────────────────►│                     │
   │                   │                     │                     │
   │                   │                     │ Create PrintJob     │
   │                   │                     │◄───────────────────►│
   │                   │                     │                     │
   │                   │                     │ Create Composite    │
   │                   │                     │◄───────────────────►│
   │                   │                     │                     │
   │                   │                     │ Save Files          │
   │                   │                     │◄───────────────────►│
   │                   │                     │                     │
   │                   │                     │ printFile()         │
   │                   │                     │────────────────────►│
   │                   │                     │                     │
   │                   │                     │ cups_job_id         │
   │                   │                     │◄────────────────────│
   │                   │                     │                     │
   │                   │ { job_id, status }  │                     │
   │                   │◄────────────────────│                     │
   │                   │                     │                     │
   │                   │ Navigate to         │                     │
   │ See Printing page │ /printing           │                     │
   │◄──────────────────│                     │                     │
   │                   │                     │                     │
```

---

## Open Questions

| # | Question | Status |
|---|----------|--------|
| 1 | Timeout for submission request? | **Decision: 30 seconds** |
| 2 | Max payload size? | **Decision: 10MB total** |
| 3 | Should we compress images before sending? | **Decision: Yes, quality 0.9** |

---

## Related Use Cases

- **UC-004**: Preview Composite (precedes this)
- **UC-006**: Monitor Print Status (follows this)
- **UC-007**: Retry Failed Print (if this fails)
- **UC-203**: Auto-Retry Print (system auto-retry)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
