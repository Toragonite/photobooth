# UC-007: Retry Failed Print

## Summary

After automatic retries have been exhausted (3 attempts), the user is presented with options to manually retry the print job or abort. This is the user-initiated retry after UC-203 (Auto-Retry) has failed.

---

## Actors

| Actor | Type | Description |
|-------|------|-------------|
| **User** | Primary | Person deciding whether to retry |
| **System** | Secondary | Processes retry request |

---

## Preconditions

| ID | Condition |
|----|-----------|
| PRE-1 | Print job exists with status: FAILED |
| PRE-2 | Job.needs_user_retry = true |
| PRE-3 | User is on Error page |
| PRE-4 | Job.retry_count >= 3 |

---

## Trigger

User taps the [Retry] button on the Error page.

---

## Main Flow

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Step                                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ User arrives on Error page after FAILED status                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ System displays:                                               │
│     │ - Error icon and message                                       │
│     │ - Troubleshooting suggestions                                  │
│     │ - [Retry] and [Home] buttons                                   │
│     │ - Composite image preview                                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ User attempts to resolve issue:                                │
│     │ - Checks printer power                                         │
│     │ - Adds paper if needed                                         │
│     │ - Checks USB connection                                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4   │ User taps [Retry] button                                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5   │ Frontend sends POST /api/print/{job_id}/retry                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6   │ Backend validates job can be retried:                          │
│     │ - Status is FAILED                                             │
│     │ - Composite file exists                                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7   │ Backend resets job for retry:                                  │
│     │ - retry_count = 0 (reset)                                      │
│     │ - error_code = null                                            │
│     │ - error_message = null                                         │
│     │ - status: FAILED → SENDING                                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8   │ Backend resubmits to CUPS (same as UC-005 step 10)             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 9   │ Backend returns updated PrintJobDTO                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ 10  │ Frontend navigates to Printing page                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ 11  │ Resume UC-006: Monitor Print Status                            │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Alternative Flows

### AF-1: User Chooses Abort Instead

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 4a  │ User taps [Home] instead of [Retry]                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4b  │ System shows confirmation: "Abandon print job?"               │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4c  │ User confirms                                                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4d  │ Frontend sends POST /api/print/{job_id}/abort                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4e  │ Backend updates: status → ABORTED                             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4f  │ Navigate to Home page                                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4g  │ Session ended, can start new                                  │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-2: Printer Now Ready

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 6a  │ Backend checks printer status before retry                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6b  │ Printer is ready: Proceed with retry                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6c  │ (If not ready, warn user but still attempt)                   │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Exception Flows

### EX-1: Composite File Missing

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Backend checks: composite_path does not exist                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Return error: "Print file not found. Please take new photos." │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Frontend displays: Cannot retry, file corrupted/deleted       │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ [Start New Session] button only option                        │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-2: Job Not in FAILED State

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Job status is not FAILED (race condition)                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Return current job status                                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Frontend routes based on actual status:                       │
│     │ - COMPLETED → Complete page                                   │
│     │ - PRINTING → Printing page                                    │
│     │ - Other → Refresh error page                                  │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-3: Retry Fails Immediately

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ CUPS rejects job immediately on retry                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Job enters ERROR state                                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Auto-retry (UC-203) takes over with 3 new attempts            │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ User sees retry progress on Printing page                     │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Postconditions

### Retry Initiated

| ID | Condition |
|----|-----------|
| POST-1 | Job status: SENDING or PRINTING |
| POST-2 | retry_count reset to 0 |
| POST-3 | User on Printing page |
| POST-4 | Monitoring resumed |

### Aborted

| ID | Condition |
|----|-----------|
| POST-A1 | Job status: ABORTED |
| POST-A2 | User on Home page |
| POST-A3 | Can start new session |

---

## Business Rules

| ID | Rule |
|----|------|
| RET-BR-1 | User retry resets retry_count to 0 |
| RET-BR-2 | No limit on user-initiated retries |
| RET-BR-3 | Abort requires confirmation |
| RET-BR-4 | Cannot retry COMPLETED or ABORTED jobs |

---

## UI/UX Requirements

### Error Page Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  [🏠]                                                           │
│                                                                 │
│                           ❌                                    │
│                                                                 │
│                    Print Failed                                 │
│                    인쇄에 실패했습니다                            │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              [Composite Image Preview]                  │    │
│  │                     (smaller)                           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  ⚠️ Error: Printer offline                              │    │
│  │     오류: 프린터 오프라인                                  │    │
│  │                                                         │    │
│  │  Please check:                                          │    │
│  │  확인해 주세요:                                          │    │
│  │                                                         │    │
│  │  • Printer is turned on / 프린터 전원 확인              │    │
│  │  • Paper is loaded / 용지 확인                          │    │
│  │  • USB cable is connected / USB 케이블 연결 확인        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│                                                                 │
│  ┌────────────────┐                    ┌────────────────────┐   │
│  │  🏠 Home       │                    │  🔄 Retry          │   │
│  │     처음으로    │                    │     다시 시도       │   │
│  └────────────────┘                    └────────────────────┘   │
│                                                                 │
│          After checking the printer, tap Retry                  │
│          프린터 확인 후 다시 시도를 눌러주세요                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Error-Specific Messages

| Error Code | English | Korean |
|------------|---------|--------|
| PRINTER_OFFLINE | Printer is offline | 프린터 오프라인 |
| PAPER_EMPTY | Out of paper | 용지 없음 |
| INK_EMPTY | Out of ink | 잉크 없음 |
| CUPS_UNAVAILABLE | Print service error | 인쇄 서비스 오류 |

---

## Technical Notes

### API Endpoint

```typescript
// POST /api/print/{job_id}/retry

// Response
interface RetryResponse {
  success: boolean;
  job: PrintJobDTO;
  error?: string;
}
```

### Backend Implementation

```python
@router.post("/print/{job_id}/retry")
async def retry_print_job(job_id: str) -> RetryResponse:
    repo = get_print_job_repository()
    printer = get_printer_service()

    job = repo.find_by_id(JobId.from_string(job_id))
    if not job:
        raise HTTPException(404, "Job not found")

    if job.status != PrintStatus.FAILED:
        return RetryResponse(
            success=False,
            job=PrintJobDTO.from_entity(job),
            error=f"Cannot retry job in {job.status} state"
        )

    # Check composite exists
    if not job.composite_path or not job.composite_path.exists():
        raise HTTPException(400, "Composite file not found")

    # Reset for retry
    job.user_retry()  # Sets retry_count=0, status=SENDING
    repo.update(job)

    # Attempt print
    result = printer.print_file(job.composite_path, job.copies)

    if result.success:
        job.cups_job_id = result.cups_job_id
        job.transition_to(PrintStatus.PRINTING)
    else:
        job.error_code = result.error_code
        job.error_message = result.error_message
        job.transition_to(PrintStatus.ERROR)

    repo.update(job)

    return RetryResponse(
        success=True,
        job=PrintJobDTO.from_entity(job)
    )
```

---

## Related Use Cases

- **UC-006**: Monitor Print Status (continues after retry)
- **UC-008**: Abort Print Job (alternative action)
- **UC-203**: Auto-Retry Print (resumes after user retry)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
