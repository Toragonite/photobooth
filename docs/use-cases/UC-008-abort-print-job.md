# UC-008: Abort Print Job

## Summary

User cancels a print job that is pending, processing, or waiting for retry. The job is removed from the queue and the session ends without printing.

---

## Actors

| Actor | Type | Description |
|-------|------|-------------|
| **User** | Primary | Person canceling the print |
| **System** | Secondary | Handles cancellation |
| **CUPS** | External | May need to cancel queued job |

---

## Preconditions

| ID | Condition |
|----|-----------|
| PRE-1 | Active print job exists |
| PRE-2 | Job status is cancellable (not COMPLETED) |
| PRE-3 | User is on print status or retry screen |

---

## Trigger

User taps [Cancel] or [Abort] button during print flow.

---

## Main Flow

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Step                                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ User viewing print status (job in progress or failed)         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ User taps [Cancel Print] button                               │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ System displays confirmation dialog:                          │
│     │ "Cancel printing? Your photos will not be printed."           │
│     │ "인쇄를 취소하시겠습니까? 사진이 인쇄되지 않습니다."             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4   │ User confirms cancellation                                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5   │ Frontend sends: POST /api/print/{job_id}/cancel               │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6   │ Backend processes cancellation:                               │
│     │ - If job in CUPS queue: Send cancel to CUPS                   │
│     │ - Update job status → CANCELLED                               │
│     │ - Set cancelled_at timestamp                                  │
│     │ - Update session status                                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7   │ Return success response                                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8   │ Frontend displays cancellation confirmation:                  │
│     │ "Print cancelled. Starting new session..."                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 9   │ After 3 seconds: Navigate to Home screen                      │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Alternative Flows

### AF-1: User Declines Confirmation

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 4a  │ User taps [Keep Printing] / [No]                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4b  │ Dialog closes                                                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4c  │ Return to print status screen                                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4d  │ Continue monitoring print job                                 │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-2: Cancel from Failed/Retry Screen

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 1a  │ Job is in FAILED or RETRY_PENDING status                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2a  │ Screen shows [Retry] and [Give Up] buttons                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2b  │ User taps [Give Up] / [Cancel]                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3a  │ Simplified confirmation (no job to stop):                     │
│     │ "End session without printing?"                               │
├─────┼────────────────────────────────────────────────────────────────┤
│     │ Continue from step 4                                          │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-3: Cancel During Active Printing

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 6a  │ Job is currently printing (CUPS processing)                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6b  │ Send cancel command to CUPS:                                  │
│     │ cancel {printer}-{job_id}                                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6c  │ Note: Selphy may complete current page before stopping        │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6d  │ Update job status regardless of CUPS response                 │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Exception Flows

### EX-1: Job Already Completed

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Backend finds job status is already COMPLETED                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Return error: "Cannot cancel - print already completed"       │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Frontend shows success screen instead:                        │
│     │ "Good news! Your print completed successfully."               │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Navigate to completion screen                                 │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-2: CUPS Cancel Fails

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ CUPS cancel command fails (job not found, permission, etc.)   │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Log warning but continue with our cancellation                │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Update job status → CANCELLED in our database                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Job monitor will handle any orphaned CUPS job                 │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-3: Network Error

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ POST /api/print/{job_id}/cancel request fails                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Frontend shows error:                                         │
│     │ "Could not cancel. Please try again."                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ [Try Again] button retries the request                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ After 3 failed attempts: Allow forced navigation to Home      │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Postconditions

| ID | Condition |
|----|-----------|
| POST-1 | Job status is CANCELLED |
| POST-2 | CUPS job cancelled (if was queued) |
| POST-3 | Session marked as ABANDONED |
| POST-4 | User returned to Home screen |
| POST-5 | Photos retained on disk (not deleted) |

---

## Business Rules

| ID | Rule |
|----|------|
| ABT-BR-1 | Cancellation always requires confirmation |
| ABT-BR-2 | Photos are never deleted on cancel (admin can clean later) |
| ABT-BR-3 | Session status → ABANDONED on cancel |
| ABT-BR-4 | Cancellation logged for analytics |
| ABT-BR-5 | Active CUPS jobs should be cancelled when possible |

---

## UI/UX Requirements

### Cancel Button Placement

```
Print Status Screen:
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                       Printing...                               │
│                        인쇄 중...                                │
│                                                                 │
│                    ████████████░░░░  75%                        │
│                                                                 │
│                                                                 │
│                                                                 │
│                    ┌─────────────────┐                          │
│                    │  Cancel Print   │  ← Secondary style       │
│                    │    인쇄 취소     │     (not prominent)      │
│                    └─────────────────┘                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Failed/Retry Screen:
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                    ⚠️ Print Failed                              │
│                      인쇄 실패                                   │
│                                                                 │
│              Printer is offline. Please check                   │
│              the printer and try again.                         │
│                                                                 │
│  ┌────────────────────┐          ┌────────────────────┐         │
│  │     Give Up        │          │       Retry        │         │
│  │      포기하기       │          │      다시 시도      │         │
│  └────────────────────┘          └────────────────────┘         │
│      Secondary                        Primary                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Confirmation Dialog

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│     ┌─────────────────────────────────────────────────────┐     │
│     │                                                     │     │
│     │              Cancel Print?                          │     │
│     │              인쇄를 취소하시겠습니까?                 │     │
│     │                                                     │     │
│     │   Your photos will not be printed.                  │     │
│     │   사진이 인쇄되지 않습니다.                          │     │
│     │                                                     │     │
│     │   ┌──────────────┐     ┌──────────────────┐         │     │
│     │   │   Go Back    │     │  Yes, Cancel     │         │     │
│     │   │    돌아가기   │     │   네, 취소합니다  │         │     │
│     │   └──────────────┘     └──────────────────┘         │     │
│     │                                                     │     │
│     └─────────────────────────────────────────────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Cancellation Confirmation

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                                                                 │
│                          ✓                                      │
│                                                                 │
│                   Print Cancelled                               │
│                     인쇄가 취소되었습니다                        │
│                                                                 │
│                                                                 │
│              Starting new session in 3...                       │
│                                                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technical Notes

### API Endpoint

```typescript
// POST /api/print/{job_id}/cancel

interface CancelPrintRequest {
  // No body required
}

interface CancelPrintResponse {
  success: boolean;
  job_id: string;
  previous_status: string;
  cups_cancelled: boolean;
  error?: string;
}

// Error responses:
// 404 - Job not found
// 409 - Job already completed
// 500 - Internal error
```

### Backend Implementation

```python
# Cancel print job use case

from datetime import datetime

class CancelPrintJobUseCase:
    def __init__(
        self,
        job_repository: PrintJobRepository,
        session_repository: SessionRepository,
        printer_service: PrinterService,
    ):
        self._jobs = job_repository
        self._sessions = session_repository
        self._printer = printer_service

    async def execute(self, job_id: str) -> CancelPrintResponse:
        # Get job
        job = await self._jobs.get_by_id(job_id)
        if not job:
            raise JobNotFoundError(job_id)

        previous_status = job.status

        # Check if already completed
        if job.status == PrintStatus.COMPLETED:
            raise JobAlreadyCompletedError(job_id)

        # Already cancelled - idempotent
        if job.status == PrintStatus.CANCELLED:
            return CancelPrintResponse(
                success=True,
                job_id=job_id,
                previous_status=previous_status.value,
                cups_cancelled=False,
            )

        # Try to cancel in CUPS if job is active
        cups_cancelled = False
        if job.cups_job_id and job.status in (
            PrintStatus.PRINTING,
            PrintStatus.PROCESSING,
            PrintStatus.PENDING,
        ):
            try:
                await self._printer.cancel_job(job.cups_job_id)
                cups_cancelled = True
            except Exception as e:
                # Log but don't fail - we'll mark cancelled anyway
                logger.warning(f"CUPS cancel failed for job {job.cups_job_id}: {e}")

        # Update job status
        job.status = PrintStatus.CANCELLED
        job.cancelled_at = datetime.utcnow()
        job.error_message = "Cancelled by user"
        await self._jobs.update(job)

        # Update session
        session = await self._sessions.get_by_id(job.session_id)
        if session:
            session.status = SessionStatus.ABANDONED
            await self._sessions.update(session)

        # Log for analytics
        logger.info(
            f"Job {job_id} cancelled",
            extra={
                'job_id': job_id,
                'previous_status': previous_status.value,
                'cups_job_id': job.cups_job_id,
                'cups_cancelled': cups_cancelled,
            }
        )

        return CancelPrintResponse(
            success=True,
            job_id=job_id,
            previous_status=previous_status.value,
            cups_cancelled=cups_cancelled,
        )
```

### CUPS Cancel Command

```python
# Printer service - cancel job

import subprocess

class PrinterService:
    async def cancel_job(self, cups_job_id: int) -> bool:
        """Cancel a job in CUPS queue."""
        try:
            result = subprocess.run(
                ['cancel', str(cups_job_id)],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                logger.warning(f"cancel command failed: {result.stderr}")
                return False

            return True

        except subprocess.TimeoutExpired:
            logger.error(f"cancel command timed out for job {cups_job_id}")
            return False
```

### Frontend Component

```typescript
// Cancel button component

interface CancelPrintButtonProps {
  jobId: string;
  onCancelled: () => void;
}

const CancelPrintButton: React.FC<CancelPrintButtonProps> = ({
  jobId,
  onCancelled,
}) => {
  const [showConfirm, setShowConfirm] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
  const { t } = useTranslation();

  const handleCancel = async () => {
    setIsCancelling(true);

    try {
      const response = await fetch(`/api/print/${jobId}/cancel`, {
        method: 'POST',
      });

      if (response.status === 409) {
        // Job already completed
        toast.success(t('print.alreadyCompleted'));
        onCancelled();
        return;
      }

      if (!response.ok) {
        throw new Error('Cancel failed');
      }

      onCancelled();

    } catch (error) {
      toast.error(t('print.cancelFailed'));
    } finally {
      setIsCancelling(false);
      setShowConfirm(false);
    }
  };

  return (
    <>
      <Button
        variant="secondary"
        onClick={() => setShowConfirm(true)}
        disabled={isCancelling}
      >
        {t('print.cancel')}
      </Button>

      <ConfirmDialog
        open={showConfirm}
        title={t('print.cancelTitle')}
        message={t('print.cancelMessage')}
        confirmText={t('print.yesCancel')}
        cancelText={t('print.goBack')}
        onConfirm={handleCancel}
        onCancel={() => setShowConfirm(false)}
        isLoading={isCancelling}
        destructive
      />
    </>
  );
};
```

---

## Related Use Cases

- **UC-006**: Monitor Print Status (cancel available during)
- **UC-007**: Retry Failed Print (alternative to cancel)
- **UC-010**: Return to Home (after cancellation)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
