# UC-201: Process Print Queue

## Summary

Background system process that monitors the print queue and submits pending jobs to CUPS for printing. Runs continuously as a daemon, processing jobs in FIFO order while respecting printer availability.

---

## Actors

| Actor | Type | Description |
|-------|------|-------------|
| **System** | Primary | Background job processor |
| **CUPS** | Secondary | Print spooler service |
| **Printer** | External | Canon Selphy CP1500 |

---

## Preconditions

| ID | Condition |
|----|-----------|
| PRE-1 | Backend service is running |
| PRE-2 | SQLite database is accessible |
| PRE-3 | CUPS service is running |
| PRE-4 | Print queue table exists |

---

## Trigger

- System startup (automatic)
- New print job inserted into queue
- Periodic check interval (every 2 seconds)

---

## Main Flow

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Step                                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ Queue processor starts on system boot                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ Enter main processing loop                                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ Query database for next pending job:                          │
│     │ - Status = PENDING                                            │
│     │ - Order by created_at ASC (FIFO)                              │
│     │ - Limit 1                                                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4   │ If no pending job: Sleep for 2 seconds, goto step 3           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5   │ Check printer availability:                                   │
│     │ - Query CUPS for printer status                               │
│     │ - Verify printer is idle or has capacity                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6   │ If printer not ready: Sleep for 2 seconds, goto step 3        │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7   │ Update job status: PENDING → PROCESSING                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8   │ Submit job to CUPS:                                           │
│     │ - Load composite image from path                              │
│     │ - Set print options (4x6, quality, copies)                    │
│     │ - Call lp command or CUPS API                                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 9   │ Store CUPS job ID in database                                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 10  │ Update job status: PROCESSING → PRINTING                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 11  │ Trigger UC-202: Monitor Print Job                             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 12  │ Continue to step 3 for next job                               │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Alternative Flows

### AF-1: Multiple Copies

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 8a  │ Job has copies > 1                                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8b  │ Pass copies parameter to CUPS: -n {copies}                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8c  │ CUPS handles multiple copies as single job                    │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-2: Printer Busy with Previous Job

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 5a  │ Printer status is "processing"                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5b  │ Check CUPS queue depth                                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5c  │ If queue < max_queue_depth (default: 2):                      │
│     │ - Allow submission (printer can buffer)                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5d  │ If queue >= max_queue_depth:                                  │
│     │ - Wait for current job to complete                            │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-3: Job Already Has CUPS ID (Retry Scenario)

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 7a  │ Job has existing cups_job_id from previous attempt            │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7b  │ Check if CUPS job still exists and is active                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7c  │ If active: Skip submission, just monitor existing job         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7d  │ If not found: Clear old CUPS ID, submit as new job            │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Exception Flows

### EX-1: Composite Image Not Found

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Composite file path does not exist                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Log error with job ID and path                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Update job:                                                   │
│     │ - status = FAILED                                             │
│     │ - error_code = FILE_NOT_FOUND                                 │
│     │ - error_message = "Composite image not found"                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ This is NOT retryable - mark as permanent failure             │
├─────┼────────────────────────────────────────────────────────────────┤
│ E5  │ Continue processing next job                                  │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-2: CUPS Submission Fails

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ lp command or CUPS API returns error                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Parse error to determine cause:                               │
│     │ - "printer not found" → PRINTER_NOT_FOUND                     │
│     │ - "service unavailable" → CUPS_UNAVAILABLE                    │
│     │ - "job rejected" → CUPS_REJECTED                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Update job with error details                                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Trigger UC-203: Auto-Retry Print if retryable                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ E5  │ Continue processing next job                                  │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-3: Database Connection Lost

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ SQLite query fails with connection error                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Log critical error                                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Attempt reconnection with backoff:                            │
│     │ - Wait 1s, retry                                              │
│     │ - Wait 2s, retry                                              │
│     │ - Wait 4s, retry                                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ If reconnection fails after 3 attempts:                       │
│     │ - Log fatal error                                             │
│     │ - Exit process (systemd will restart)                         │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-4: CUPS Service Not Running

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Cannot connect to CUPS socket                                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Log error: "CUPS service unavailable"                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Attempt to restart CUPS via systemctl                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Wait 5 seconds for CUPS to start                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ E5  │ If still unavailable: Continue loop, will retry next cycle    │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Postconditions

| ID | Condition |
|----|-----------|
| POST-1 | Pending jobs are submitted to CUPS |
| POST-2 | Job status reflects current state |
| POST-3 | CUPS job ID stored for tracking |
| POST-4 | Failed jobs have error details |

---

## Business Rules

| ID | Rule |
|----|------|
| PQ-BR-1 | Jobs processed in FIFO order (oldest first) |
| PQ-BR-2 | Only one job submitted to CUPS at a time (unless queue allows) |
| PQ-BR-3 | Polling interval: 2 seconds when idle |
| PQ-BR-4 | Max CUPS queue depth: 2 jobs |
| PQ-BR-5 | Processor must survive and recover from any error |

---

## Technical Notes

### Queue Processor Implementation

```python
# Background queue processor daemon

import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PrintQueueProcessor:
    """
    Background daemon that processes the print queue.
    Designed for resilience - must never crash permanently.
    """

    POLL_INTERVAL = 2.0  # seconds
    MAX_CUPS_QUEUE = 2
    DB_RETRY_DELAYS = [1, 2, 4]  # seconds

    def __init__(
        self,
        job_repository: PrintJobRepository,
        printer_service: PrinterService,
        job_monitor: JobMonitor,
    ):
        self._jobs = job_repository
        self._printer = printer_service
        self._monitor = job_monitor
        self._running = False

    async def start(self):
        """Start the queue processor daemon."""
        self._running = True
        logger.info("Print queue processor started")

        while self._running:
            try:
                await self._process_next_job()
            except Exception as e:
                logger.error(f"Queue processor error: {e}", exc_info=True)
                # Never crash - just log and continue
                await asyncio.sleep(self.POLL_INTERVAL)

    async def stop(self):
        """Gracefully stop the processor."""
        self._running = False
        logger.info("Print queue processor stopping")

    async def _process_next_job(self):
        """Process the next pending job in queue."""

        # Get next pending job
        job = await self._get_next_pending_job()
        if not job:
            await asyncio.sleep(self.POLL_INTERVAL)
            return

        logger.info(f"Processing job {job.id}")

        # Check printer readiness
        if not await self._is_printer_ready():
            logger.debug("Printer not ready, waiting...")
            await asyncio.sleep(self.POLL_INTERVAL)
            return

        # Validate composite file exists
        if not job.composite_path.exists():
            await self._fail_job(
                job,
                ErrorCode.FILE_NOT_FOUND,
                f"Composite image not found: {job.composite_path}",
                retryable=False,
            )
            return

        # Update status to PROCESSING
        job.status = PrintStatus.PROCESSING
        job.started_at = datetime.utcnow()
        await self._jobs.update(job)

        # Submit to CUPS
        try:
            cups_job_id = await self._submit_to_cups(job)
            job.cups_job_id = cups_job_id
            job.status = PrintStatus.PRINTING
            await self._jobs.update(job)

            logger.info(f"Job {job.id} submitted to CUPS as {cups_job_id}")

            # Start monitoring this job
            await self._monitor.track_job(job)

        except PrinterOfflineError:
            await self._fail_job(
                job,
                ErrorCode.PRINTER_OFFLINE,
                "Printer is offline",
                retryable=True,
            )
        except CupsUnavailableError:
            await self._fail_job(
                job,
                ErrorCode.CUPS_UNAVAILABLE,
                "CUPS service unavailable",
                retryable=True,
            )
        except CupsRejectedError as e:
            await self._fail_job(
                job,
                ErrorCode.CUPS_REJECTED,
                f"CUPS rejected job: {e}",
                retryable=True,
            )
        except Exception as e:
            await self._fail_job(
                job,
                ErrorCode.UNKNOWN,
                f"Unexpected error: {e}",
                retryable=False,
            )

    async def _get_next_pending_job(self) -> PrintJob | None:
        """Get next job with database retry logic."""
        for delay in self.DB_RETRY_DELAYS:
            try:
                return await self._jobs.get_next_pending()
            except DatabaseError as e:
                logger.warning(f"Database error, retrying in {delay}s: {e}")
                await asyncio.sleep(delay)

        # All retries failed
        logger.critical("Database connection failed after all retries")
        raise DatabaseConnectionError("Cannot connect to database")

    async def _is_printer_ready(self) -> bool:
        """Check if printer can accept new jobs."""
        try:
            info = await self._printer.get_status()

            if info.status == 'offline':
                return False

            if info.status == 'processing':
                # Check queue depth
                queue_count = await self._printer.get_queue_count()
                return queue_count < self.MAX_CUPS_QUEUE

            return info.status == 'idle'

        except Exception as e:
            logger.warning(f"Cannot check printer status: {e}")
            return False

    async def _submit_to_cups(self, job: PrintJob) -> int:
        """Submit job to CUPS and return CUPS job ID."""
        options = PrintOptions(
            media='4x6',
            quality='high',
            copies=job.copies,
        )

        result = await self._printer.print_file(
            file_path=job.composite_path,
            options=options,
        )

        if not result.success:
            raise CupsRejectedError(result.error_message)

        return result.cups_job_id

    async def _fail_job(
        self,
        job: PrintJob,
        error_code: ErrorCode,
        message: str,
        retryable: bool,
    ):
        """Mark job as failed and optionally queue for retry."""
        logger.error(f"Job {job.id} failed: {message}")

        job.error_code = error_code
        job.error_message = message

        if retryable and job.retry_count < PrintJob.MAX_RETRIES:
            # Will be picked up by auto-retry processor
            job.status = PrintStatus.RETRY_PENDING
        else:
            job.status = PrintStatus.FAILED

        await self._jobs.update(job)
```

### Startup Integration

```python
# Application startup

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    queue_processor = PrintQueueProcessor(
        job_repository=job_repo,
        printer_service=printer_service,
        job_monitor=job_monitor,
    )

    # Start as background task
    processor_task = asyncio.create_task(queue_processor.start())

    yield

    # Shutdown
    await queue_processor.stop()
    processor_task.cancel()
```

### Database Query

```sql
-- Get next pending job (FIFO)
SELECT *
FROM print_jobs
WHERE status = 'PENDING'
ORDER BY created_at ASC
LIMIT 1;

-- Get retry-pending jobs
SELECT *
FROM print_jobs
WHERE status = 'RETRY_PENDING'
  AND next_retry_at <= datetime('now')
ORDER BY next_retry_at ASC
LIMIT 1;
```

---

## State Diagram

```
                    ┌─────────────────┐
                    │     PENDING     │
                    └────────┬────────┘
                             │
                    Queue processor picks up
                             │
                             ▼
                    ┌─────────────────┐
                    │   PROCESSING    │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
        Submit fails    Submit OK     File not found
              │              │              │
              ▼              ▼              ▼
     ┌────────────────┐ ┌─────────┐  ┌──────────┐
     │ RETRY_PENDING  │ │PRINTING │  │  FAILED  │
     └────────────────┘ └─────────┘  └──────────┘
              │              │
         (UC-203)       (UC-202)
```

---

## Related Use Cases

- **UC-005**: Submit Print Job (creates jobs for this processor)
- **UC-202**: Monitor Print Job (tracks CUPS job status)
- **UC-203**: Auto-Retry Print (handles failed jobs)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
