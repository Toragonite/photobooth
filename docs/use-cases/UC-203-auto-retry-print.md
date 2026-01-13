# UC-203: Auto-Retry Print

## Summary

The system automatically retries failed print jobs that have retryable errors, without requiring user intervention. This runs as a background process on the backend.

---

## Actors

| Actor | Type | Description |
|-------|------|-------------|
| **System** | Primary | Backend automatic process |
| **Job Monitor** | Secondary | Background thread monitoring jobs |
| **CUPS** | Secondary | Print service |

---

## Preconditions

| ID | Condition |
|----|-----------|
| PRE-1 | Print job exists in ERROR status |
| PRE-2 | retry_count < MAX_RETRIES (3) |
| PRE-3 | error_code is retryable |
| PRE-4 | Job not manually aborted |

---

## Trigger

Automatic: Detected by background job monitor when a job enters ERROR state with a retryable error.

---

## Main Flow

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Step                                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ Job Monitor detects job in ERROR status                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ Monitor checks retry eligibility:                              │
│     │ - error_code in RETRYABLE_ERRORS                               │
│     │ - retry_count < 3                                              │
│     │ - status == ERROR (not FAILED or ABORTED)                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ If eligible, calculate retry delay:                            │
│     │ - Retry 1: 3 seconds                                           │
│     │ - Retry 2: 5 seconds                                           │
│     │ - Retry 3: 8 seconds                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4   │ System waits for delay period                                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5   │ System logs retry attempt:                                     │
│     │ - "Retrying job {job_id}, attempt {retry_count + 1}/3"         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6   │ System re-checks printer status:                               │
│     │ - PrinterService.is_ready()                                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7   │ If printer ready:                                              │
│     │ - Update job status: ERROR → SENDING                           │
│     │ - Clear error_code, error_message                              │
│     │ - Increment retry_count                                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8   │ System resubmits print job to CUPS:                            │
│     │ - PrinterService.print_file(composite_path, copies)            │
├─────┼────────────────────────────────────────────────────────────────┤
│ 9   │ If CUPS accepts job:                                           │
│     │ - Update job with new cups_job_id                              │
│     │ - Update status: SENDING → PRINTING                            │
│     │ - Continue normal monitoring (UC-202)                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 10  │ If CUPS rejects job:                                           │
│     │ - Update job status: SENDING → ERROR                           │
│     │ - Set error_code, error_message                                │
│     │ - Loop back to step 1 (will retry again if eligible)           │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Retry Decision Tree

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Job enters ERROR state                                                     │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────┐                                                    │
│  │ Is error_code       │                                                    │
│  │ retryable?          │                                                    │
│  └──────────┬──────────┘                                                    │
│             │                                                               │
│     ┌───────┴───────┐                                                       │
│     │ NO            │ YES                                                   │
│     ▼               ▼                                                       │
│  ┌────────┐   ┌─────────────────────┐                                       │
│  │ FAILED │   │ Is retry_count < 3? │                                       │
│  │(final) │   └──────────┬──────────┘                                       │
│  └────────┘              │                                                  │
│                  ┌───────┴───────┐                                          │
│                  │ NO            │ YES                                      │
│                  ▼               ▼                                          │
│             ┌────────┐    ┌─────────────┐                                   │
│             │ FAILED │    │ Wait delay  │                                   │
│             │(final) │    │ then RETRY  │                                   │
│             └────────┘    └─────────────┘                                   │
│                                                                             │
│  RETRYABLE ERRORS:                                                          │
│  ✓ PRINTER_OFFLINE                                                          │
│  ✓ PRINTER_BUSY                                                             │
│  ✓ PAPER_EMPTY                                                              │
│  ✓ INK_EMPTY                                                                │
│  ✓ CUPS_UNAVAILABLE                                                         │
│  ✓ CUPS_REJECTED                                                            │
│                                                                             │
│  NON-RETRYABLE ERRORS:                                                      │
│  ✗ PROCESSING_ERROR                                                         │
│  ✗ INVALID_IMAGE                                                            │
│  ✗ STORAGE_FULL                                                             │
│  ✗ TIMEOUT                                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Alternative Flows

### AF-1: Printer Becomes Ready Before Delay

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 4a  │ While waiting, PrinterService.is_ready() becomes true         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4b  │ System may skip remaining delay (implementation choice)       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4c  │ Proceed to step 6                                             │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-2: User Aborts During Retry Wait

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 4a  │ User initiates abort (UC-008) while system waiting            │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4b  │ System checks abort flag before retrying                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4c  │ If aborted: Cancel retry, job status → ABORTED                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4d  │ No further retries attempted                                  │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-3: Backend Restart During Retry

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 4a  │ Backend restarts while job in ERROR state awaiting retry      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4b  │ On startup, Job Monitor queries all ERROR jobs from DB        │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4c  │ For each eligible job, schedule immediate retry               │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4d  │ Resume normal retry flow from step 6                          │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Exception Flows

### EX-1: CUPS Connection Lost

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ PrinterService connection to CUPS fails                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ System attempts reconnection (3 attempts, 1s apart)           │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ If reconnection fails:                                        │
│     │ - Keep job in ERROR state                                     │
│     │ - error_code: CUPS_UNAVAILABLE                                │
│     │ - Will retry again on next cycle                              │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-2: Composite File Missing

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ job.composite_path file does not exist                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ System cannot retry without file                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Set error_code: STORAGE_ERROR (non-retryable)                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Job status: ERROR → FAILED                                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ E5  │ Log critical error for admin attention                        │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Postconditions

### Retry Successful

| ID | Condition |
|----|-----------|
| POST-1 | Job status: PRINTING |
| POST-2 | New cups_job_id assigned |
| POST-3 | retry_count incremented |
| POST-4 | Normal monitoring resumed |

### Retry Failed (Still Retryable)

| ID | Condition |
|----|-----------|
| POST-F1 | Job status: ERROR |
| POST-F2 | error_code set to new error |
| POST-F3 | retry_count incremented |
| POST-F4 | Will retry again if < 3 |

### Max Retries Reached

| ID | Condition |
|----|-----------|
| POST-M1 | Job status: FAILED |
| POST-M2 | needs_user_retry = true |
| POST-M3 | User must manually retry or abort |

---

## Business Rules

| ID | Rule |
|----|------|
| ART-BR-1 | Maximum auto-retries: 3 |
| ART-BR-2 | Retry delays: 3s, 5s, 8s (increasing) |
| ART-BR-3 | Only retryable errors trigger auto-retry |
| ART-BR-4 | User abort cancels pending retries |
| ART-BR-5 | Backend restart recovers pending retries |
| ART-BR-6 | Each retry increments retry_count |

---

## Data Requirements

### Retry Configuration

```python
RETRY_CONFIG = {
    'max_retries': 3,
    'delays': [3, 5, 8],  # Seconds between retries
    'retryable_errors': [
        'PRINTER_OFFLINE',
        'PRINTER_BUSY',
        'PAPER_EMPTY',
        'INK_EMPTY',
        'CUPS_UNAVAILABLE',
        'CUPS_REJECTED',
    ],
}
```

### Job State for Retry

```python
@dataclass
class PrintJob:
    # ... other fields ...
    status: PrintStatus          # ERROR while waiting retry
    error_code: ErrorCode        # Current error
    error_message: str           # Error details
    retry_count: int             # 0, 1, 2, or 3
    last_error_at: datetime      # When error occurred
    next_retry_at: datetime      # When to retry (calculated)
```

---

## Technical Notes

### Job Monitor Implementation

```python
# infrastructure/services/job_monitor.py

class JobMonitor:
    """Background service that monitors and retries failed print jobs"""

    def __init__(
        self,
        print_job_repo: PrintJobRepository,
        printer_service: PrinterService,
        config: RetryConfig,
    ):
        self._repo = print_job_repo
        self._printer = printer_service
        self._config = config
        self._running = False
        self._thread: Optional[Thread] = None

    def start(self):
        """Start the monitor in a background thread"""
        self._running = True
        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Job monitor started")

    def stop(self):
        """Stop the monitor"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Job monitor stopped")

    def _run(self):
        """Main monitor loop"""
        while self._running:
            try:
                self._check_jobs()
            except Exception as e:
                logger.error(f"Job monitor error: {e}")

            time.sleep(1)  # Check every second

    def _check_jobs(self):
        """Check for jobs needing retry"""
        # Get all jobs in ERROR state
        error_jobs = self._repo.find_by_status(PrintStatus.ERROR)

        for job in error_jobs:
            if self._should_retry(job):
                self._retry_job(job)

    def _should_retry(self, job: PrintJob) -> bool:
        """Determine if job should be retried"""
        # Check if error is retryable
        if job.error_code not in self._config.retryable_errors:
            # Move to FAILED (non-retryable)
            job.transition_to(PrintStatus.FAILED)
            self._repo.update(job)
            return False

        # Check retry count
        if job.retry_count >= self._config.max_retries:
            job.transition_to(PrintStatus.FAILED)
            self._repo.update(job)
            return False

        # Check if enough time has passed
        delay = self._get_delay(job.retry_count)
        time_since_error = (datetime.now() - job.last_error_at).total_seconds()

        return time_since_error >= delay

    def _get_delay(self, retry_count: int) -> int:
        """Get delay in seconds for given retry number"""
        delays = self._config.delays
        index = min(retry_count, len(delays) - 1)
        return delays[index]

    def _retry_job(self, job: PrintJob):
        """Execute a retry attempt"""
        logger.info(f"Retrying job {job.id}, attempt {job.retry_count + 1}/3")

        # Check printer status
        if not self._printer.is_ready():
            logger.warning(f"Printer not ready for retry of job {job.id}")
            return  # Will try again on next cycle

        # Update job state
        job.retry_count += 1
        job.error_code = None
        job.error_message = None
        job.transition_to(PrintStatus.SENDING)
        self._repo.update(job)

        # Attempt print
        try:
            result = self._printer.print_file(
                file_path=job.composite_path,
                copies=job.copies,
            )

            if result.success:
                job.cups_job_id = result.cups_job_id
                job.transition_to(PrintStatus.PRINTING)
                logger.info(f"Retry successful for job {job.id}")
            else:
                job.error_code = result.error_code
                job.error_message = result.error_message
                job.last_error_at = datetime.now()
                job.transition_to(PrintStatus.ERROR)
                logger.warning(f"Retry failed for job {job.id}: {result.error_message}")

        except Exception as e:
            job.error_code = ErrorCode.CUPS_UNAVAILABLE
            job.error_message = str(e)
            job.last_error_at = datetime.now()
            job.transition_to(PrintStatus.ERROR)
            logger.error(f"Retry exception for job {job.id}: {e}")

        self._repo.update(job)
```

### Startup Recovery

```python
# In main.py or startup script

async def recover_pending_jobs():
    """Recover jobs that were in progress when system restarted"""
    repo = get_print_job_repository()
    printer = get_printer_service()

    # Find jobs that need attention
    active_jobs = repo.find_active()

    for job in active_jobs:
        if job.status == PrintStatus.PRINTING:
            # Check if CUPS job still exists
            if job.cups_job_id:
                try:
                    cups_status = printer.get_job_status(job.cups_job_id)
                    if cups_status.state == JobState.COMPLETED:
                        job.transition_to(PrintStatus.COMPLETED)
                        job.completed_at = datetime.now()
                    elif cups_status.state in (JobState.CANCELED, JobState.ABORTED):
                        job.error_code = ErrorCode.CUPS_REJECTED
                        job.transition_to(PrintStatus.ERROR)
                except:
                    # Job not found in CUPS, mark for retry
                    job.error_code = ErrorCode.CUPS_UNAVAILABLE
                    job.transition_to(PrintStatus.ERROR)

            repo.update(job)

    logger.info(f"Recovered {len(active_jobs)} active jobs")
```

---

## Sequence Diagram

```
┌───────────────┐    ┌──────────────┐    ┌─────────────┐    ┌───────┐
│  Job Monitor  │    │  Repository  │    │  Printer    │    │ CUPS  │
│   (Thread)    │    │              │    │  Service    │    │       │
└──────┬────────┘    └──────┬───────┘    └──────┬──────┘    └───┬───┘
       │                    │                   │               │
       │ find ERROR jobs    │                   │               │
       │───────────────────►│                   │               │
       │                    │                   │               │
       │ [job1: ERROR]      │                   │               │
       │◄───────────────────│                   │               │
       │                    │                   │               │
       │ (wait delay: 3s)   │                   │               │
       │                    │                   │               │
       │ is_ready()?        │                   │               │
       │───────────────────────────────────────►│               │
       │                    │                   │               │
       │ true               │                   │               │
       │◄───────────────────────────────────────│               │
       │                    │                   │               │
       │ update(SENDING)    │                   │               │
       │───────────────────►│                   │               │
       │                    │                   │               │
       │ print_file()       │                   │               │
       │───────────────────────────────────────►│               │
       │                    │                   │               │
       │                    │                   │ printFile()   │
       │                    │                   │──────────────►│
       │                    │                   │               │
       │                    │                   │ cups_job_id   │
       │                    │                   │◄──────────────│
       │                    │                   │               │
       │ success, job_id    │                   │               │
       │◄───────────────────────────────────────│               │
       │                    │                   │               │
       │ update(PRINTING)   │                   │               │
       │───────────────────►│                   │               │
       │                    │                   │               │
```

---

## Related Use Cases

- **UC-005**: Submit Print Job (initiates jobs)
- **UC-006**: Monitor Print Status (user sees retry progress)
- **UC-007**: Retry Failed Print (user manual retry after max auto)
- **UC-202**: Monitor Print Job (CUPS status monitoring)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
