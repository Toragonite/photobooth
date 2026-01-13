# UC-202: Monitor Print Job

## Summary

System continuously monitors active print jobs in CUPS to track their progress and detect completion or failure. Updates job status in database and notifies frontend clients via polling endpoints.

---

## Actors

| Actor | Type | Description |
|-------|------|-------------|
| **System** | Primary | Background job monitor |
| **CUPS** | Secondary | Print spooler with job status |
| **Frontend** | Observer | Polls for status updates |

---

## Preconditions

| ID | Condition |
|----|-----------|
| PRE-1 | Print job has been submitted to CUPS |
| PRE-2 | Job has valid cups_job_id |
| PRE-3 | Job status is PRINTING |
| PRE-4 | CUPS service is accessible |

---

## Trigger

- Job submitted to CUPS (from UC-201)
- Periodic monitoring interval (every 1 second)

---

## Main Flow

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Step                                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ Job monitor receives job to track (from UC-201)               │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ Add job to active monitoring set                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ Query CUPS for job status:                                    │
│     │ lpstat -l -o {printer_name}                                   │
│     │ OR CUPS API: IPP Get-Job-Attributes                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4   │ Parse CUPS response for job state:                            │
│     │ - pending: Job queued in CUPS                                 │
│     │ - processing: Printer actively printing                       │
│     │ - completed: Print finished successfully                      │
│     │ - canceled: Job was canceled                                  │
│     │ - aborted: Job failed/aborted                                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5   │ If state unchanged: Wait 1 second, goto step 3                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6   │ If state = completed:                                         │
│     │ - Update job status → COMPLETED                               │
│     │ - Set completed_at timestamp                                  │
│     │ - Remove from active monitoring                               │
│     │ - Log success                                                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7   │ If state = processing:                                        │
│     │ - Update progress percentage (if available)                   │
│     │ - Continue monitoring                                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8   │ Frontend polls GET /api/print/{job_id}/status                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 9   │ Return current job status from database                       │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Alternative Flows

### AF-1: Job Not Found in CUPS

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 3a  │ CUPS returns no job with given ID                             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3b  │ Check if job was recently completed:                          │
│     │ - Query CUPS completed job history                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3c  │ If found in history as completed:                             │
│     │ - Mark job as COMPLETED                                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3d  │ If not found anywhere:                                        │
│     │ - Wait and retry (job may not have reached CUPS yet)          │
│     │ - After 10 retries: Mark as UNKNOWN status                    │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-2: Multiple Copies Progress

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 7a  │ Job has copies > 1                                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7b  │ CUPS reports page progress (e.g., "page 2 of 3")              │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7c  │ Calculate percentage: (current_page / total_copies) * 100     │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7d  │ Update job.progress field                                     │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-3: Startup Recovery

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 0a  │ System starts up after restart/crash                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 0b  │ Query database for jobs with status = PRINTING                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 0c  │ For each job:                                                 │
│     │ - Check CUPS for job status                                   │
│     │ - If completed in CUPS: Mark COMPLETED                        │
│     │ - If still active: Resume monitoring                          │
│     │ - If not found: Mark for retry                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 0d  │ Continue normal monitoring loop                               │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Exception Flows

### EX-1: CUPS Reports Job Aborted

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ CUPS job state = aborted                                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Parse abort reason from CUPS:                                 │
│     │ - "job-canceled-by-user"                                      │
│     │ - "job-canceled-at-device"                                    │
│     │ - "aborted-by-system"                                         │
│     │ - "job-completed-with-errors"                                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Map to error code:                                            │
│     │ - Device cancel → PRINTER_ERROR                               │
│     │ - System abort → CUPS_ERROR                                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ If retryable: Set status → RETRY_PENDING                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ E5  │ If not retryable or max retries: Set status → FAILED          │
├─────┼────────────────────────────────────────────────────────────────┤
│ E6  │ Remove from active monitoring                                 │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-2: CUPS Connection Lost

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Cannot connect to CUPS socket/API                             │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Log warning                                                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Retry with exponential backoff:                               │
│     │ - 1s, 2s, 4s, 8s (max)                                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Continue monitoring attempts - do not mark jobs failed        │
├─────┼────────────────────────────────────────────────────────────────┤
│ E5  │ Jobs remain in PRINTING status during outage                  │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-3: Printer Hardware Error

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ CUPS reports printer error:                                   │
│     │ - "media-empty" (paper out)                                   │
│     │ - "marker-supply-empty" (ink out)                             │
│     │ - "offline" (printer disconnected)                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Job remains in CUPS queue (held)                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Update our job record:                                        │
│     │ - status remains PRINTING                                     │
│     │ - Add warning flag for UI display                             │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Continue monitoring - job will resume when error cleared      │
├─────┼────────────────────────────────────────────────────────────────┤
│ E5  │ Frontend shows: "Waiting for printer - check paper/ink"       │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-4: Monitoring Timeout

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Job has been in PRINTING status > 10 minutes                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Log warning: "Job {id} monitoring timeout"                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Check CUPS one more time for final status                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ If still no resolution:                                       │
│     │ - Mark job as FAILED                                          │
│     │ - error_code = TIMEOUT                                        │
│     │ - Allow user retry                                            │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Postconditions

| ID | Condition |
|----|-----------|
| POST-1 | Job status accurately reflects CUPS state |
| POST-2 | Completed jobs have completed_at timestamp |
| POST-3 | Failed jobs have error details |
| POST-4 | Frontend can retrieve current status |

---

## Business Rules

| ID | Rule |
|----|------|
| MON-BR-1 | Polling interval: 1 second for active jobs |
| MON-BR-2 | Timeout: 10 minutes maximum monitoring time |
| MON-BR-3 | Hardware errors do not auto-fail jobs |
| MON-BR-4 | CUPS connection loss does not fail jobs |
| MON-BR-5 | Progress reported as percentage 0-100 |

---

## CUPS Status Mapping

| CUPS State | Our Status | Action |
|------------|------------|--------|
| pending | PRINTING | Continue monitoring |
| pending-held | PRINTING | Continue + warn UI |
| processing | PRINTING | Update progress |
| processing-stopped | PRINTING | Continue + warn UI |
| completed | COMPLETED | Success |
| canceled | FAILED | Check if user-initiated |
| aborted | FAILED/RETRY | Check reason |

---

## Technical Notes

### Job Monitor Implementation

```python
# Background job monitor

import asyncio
import subprocess
from datetime import datetime, timedelta
from typing import Set

class JobMonitor:
    """
    Monitors active print jobs in CUPS.
    Updates job status based on CUPS feedback.
    """

    POLL_INTERVAL = 1.0  # seconds
    TIMEOUT_MINUTES = 10
    CUPS_RETRY_DELAYS = [1, 2, 4, 8]  # seconds

    def __init__(self, job_repository: PrintJobRepository):
        self._jobs = job_repository
        self._active_jobs: Set[str] = set()
        self._running = False

    async def start(self):
        """Start the monitoring daemon."""
        self._running = True

        # Recover any jobs that were printing when we restarted
        await self._recover_printing_jobs()

        # Main monitoring loop
        while self._running:
            await self._monitor_cycle()
            await asyncio.sleep(self.POLL_INTERVAL)

    async def stop(self):
        """Stop the monitor gracefully."""
        self._running = False

    async def track_job(self, job: PrintJob):
        """Add a job to active monitoring."""
        self._active_jobs.add(job.id)

    async def _recover_printing_jobs(self):
        """Recover jobs that were printing before restart."""
        jobs = await self._jobs.get_by_status(PrintStatus.PRINTING)

        for job in jobs:
            if job.cups_job_id:
                # Check current CUPS status
                cups_status = await self._get_cups_status(job.cups_job_id)

                if cups_status == 'completed':
                    await self._complete_job(job)
                elif cups_status in ('canceled', 'aborted'):
                    await self._fail_job(job, "Job failed during system restart")
                elif cups_status:
                    # Still active, resume monitoring
                    self._active_jobs.add(job.id)
                else:
                    # Not found in CUPS, mark for retry
                    job.status = PrintStatus.RETRY_PENDING
                    await self._jobs.update(job)

    async def _monitor_cycle(self):
        """Single monitoring cycle for all active jobs."""
        jobs_to_remove = []

        for job_id in list(self._active_jobs):
            try:
                job = await self._jobs.get_by_id(job_id)
                if not job or not job.cups_job_id:
                    jobs_to_remove.append(job_id)
                    continue

                # Check for timeout
                if self._is_timed_out(job):
                    await self._timeout_job(job)
                    jobs_to_remove.append(job_id)
                    continue

                # Get CUPS status
                cups_status = await self._get_cups_status(job.cups_job_id)

                if cups_status == 'completed':
                    await self._complete_job(job)
                    jobs_to_remove.append(job_id)

                elif cups_status in ('canceled', 'aborted'):
                    await self._fail_job(job, f"CUPS job {cups_status}")
                    jobs_to_remove.append(job_id)

                elif cups_status == 'processing':
                    # Update progress if available
                    progress = await self._get_job_progress(job.cups_job_id)
                    if progress != job.progress:
                        job.progress = progress
                        await self._jobs.update(job)

                # pending, pending-held, processing-stopped: continue monitoring

            except Exception as e:
                # Log but don't remove - will retry next cycle
                logger.error(f"Error monitoring job {job_id}: {e}")

        # Remove finished jobs from active set
        for job_id in jobs_to_remove:
            self._active_jobs.discard(job_id)

    async def _get_cups_status(self, cups_job_id: int) -> str | None:
        """Query CUPS for job status with retry."""
        for delay in self.CUPS_RETRY_DELAYS:
            try:
                # Use lpstat to check job
                result = subprocess.run(
                    ['lpstat', '-l', '-o'],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                # Parse output for our job
                # Format: "printer-123 username 1024 Mon Jan 13 12:00:00 2024"
                for line in result.stdout.split('\n'):
                    if f'-{cups_job_id} ' in line:
                        # Job is still in queue (pending or processing)
                        if 'processing' in line.lower():
                            return 'processing'
                        return 'pending'

                # Job not in active queue - check history
                result = subprocess.run(
                    ['lpstat', '-W', 'completed', '-o'],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                if f'-{cups_job_id} ' in result.stdout:
                    return 'completed'

                # Check for aborted/canceled
                result = subprocess.run(
                    ['lpstat', '-W', 'not-completed', '-o'],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                if f'-{cups_job_id} ' in result.stdout:
                    if 'canceled' in result.stdout.lower():
                        return 'canceled'
                    return 'aborted'

                # Job not found anywhere
                return None

            except subprocess.TimeoutExpired:
                logger.warning(f"CUPS timeout, retrying in {delay}s")
                await asyncio.sleep(delay)
            except Exception as e:
                logger.warning(f"CUPS error: {e}, retrying in {delay}s")
                await asyncio.sleep(delay)

        return None

    async def _get_job_progress(self, cups_job_id: int) -> int:
        """Get print progress percentage."""
        # Selphy doesn't report detailed progress
        # Return 50 for processing, 0 for pending
        status = await self._get_cups_status(cups_job_id)
        if status == 'processing':
            return 50
        return 0

    def _is_timed_out(self, job: PrintJob) -> bool:
        """Check if job has exceeded timeout."""
        if not job.started_at:
            return False
        timeout = timedelta(minutes=self.TIMEOUT_MINUTES)
        return datetime.utcnow() - job.started_at > timeout

    async def _complete_job(self, job: PrintJob):
        """Mark job as completed."""
        job.status = PrintStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.progress = 100
        await self._jobs.update(job)
        logger.info(f"Job {job.id} completed successfully")

    async def _fail_job(self, job: PrintJob, reason: str):
        """Mark job as failed."""
        job.error_message = reason

        if job.retry_count < PrintJob.MAX_RETRIES:
            job.status = PrintStatus.RETRY_PENDING
        else:
            job.status = PrintStatus.FAILED

        await self._jobs.update(job)
        logger.warning(f"Job {job.id} failed: {reason}")

    async def _timeout_job(self, job: PrintJob):
        """Handle job timeout."""
        job.status = PrintStatus.FAILED
        job.error_code = ErrorCode.TIMEOUT
        job.error_message = f"Job timed out after {self.TIMEOUT_MINUTES} minutes"
        await self._jobs.update(job)
        logger.error(f"Job {job.id} timed out")
```

### Alternative: CUPS Python Binding

```python
# Using pycups for more reliable status

import cups

class CupsJobMonitor:
    def __init__(self):
        self._conn = cups.Connection()

    def get_job_status(self, job_id: int) -> dict:
        """Get detailed job status from CUPS."""
        try:
            jobs = self._conn.getJobs(which_jobs='all')
            if job_id in jobs:
                job = jobs[job_id]
                return {
                    'state': job.get('job-state', 0),
                    'state_reasons': job.get('job-state-reasons', []),
                    'pages_completed': job.get('job-media-sheets-completed', 0),
                }
        except cups.IPPError as e:
            logger.error(f"CUPS IPP error: {e}")
        return None

    def get_printer_state(self, printer_name: str) -> dict:
        """Get printer state including errors."""
        printers = self._conn.getPrinters()
        if printer_name in printers:
            p = printers[printer_name]
            return {
                'state': p.get('printer-state', 0),
                'state_reasons': p.get('printer-state-reasons', []),
            }
        return None
```

### Frontend Polling

```typescript
// Status polling from frontend (see UC-006)

const usePrintStatus = (jobId: string) => {
  const [status, setStatus] = useState<PrintJobStatus | null>(null);

  useEffect(() => {
    const poll = async () => {
      const response = await fetch(`/api/print/${jobId}/status`);
      const data = await response.json();
      setStatus(data);

      // Stop polling if terminal state
      if (['COMPLETED', 'FAILED'].includes(data.status)) {
        return;
      }
    };

    poll();
    const interval = setInterval(poll, 1000);
    return () => clearInterval(interval);
  }, [jobId]);

  return status;
};
```

---

## Sequence Diagram

```
┌─────────┐     ┌─────────────┐     ┌──────┐     ┌──────────┐
│ UC-201  │     │ JobMonitor  │     │ CUPS │     │ Database │
└────┬────┘     └──────┬──────┘     └───┬──┘     └────┬─────┘
     │                 │                │              │
     │ track_job(job)  │                │              │
     │────────────────>│                │              │
     │                 │                │              │
     │                 │ lpstat -l      │              │
     │                 │───────────────>│              │
     │                 │                │              │
     │                 │ "processing"   │              │
     │                 │<───────────────│              │
     │                 │                │              │
     │                 │ update progress│              │
     │                 │───────────────────────────────>
     │                 │                │              │
     │                 │    ... (polling continues)   │
     │                 │                │              │
     │                 │ lpstat -W completed           │
     │                 │───────────────>│              │
     │                 │                │              │
     │                 │ "completed"    │              │
     │                 │<───────────────│              │
     │                 │                │              │
     │                 │ status=COMPLETED              │
     │                 │───────────────────────────────>
     │                 │                │              │
```

---

## Related Use Cases

- **UC-201**: Process Print Queue (submits jobs for monitoring)
- **UC-006**: Monitor Print Status (frontend polling)
- **UC-203**: Auto-Retry Print (handles failures)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
