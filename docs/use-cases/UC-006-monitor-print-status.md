# UC-006: Monitor Print Status

## Summary

After submitting a print job, the system continuously monitors and displays the print progress to the user. The frontend polls the backend for status updates until the job reaches a terminal state.

---

## Actors

| Actor | Type | Description |
|-------|------|-------------|
| **User** | Primary | Person waiting for print to complete |
| **Frontend** | Secondary | Polls backend for status |
| **Backend** | Secondary | Monitors CUPS job status |
| **CUPS** | Secondary | Manages actual print job |

---

## Preconditions

| ID | Condition |
|----|-----------|
| PRE-1 | Print job exists (UC-005 completed) |
| PRE-2 | User is on Printing page |
| PRE-3 | Job ID is known (stored in session) |
| PRE-4 | Job is in non-terminal state |

---

## Trigger

Automatic: Page load on Printing page after print submission.

---

## Main Flow

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Step                                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ User arrives on Printing page with job_id                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ Frontend displays initial state:                               │
│     │ - Composite image preview                                      │
│     │ - Progress bar at last known progress                          │
│     │ - Status message                                               │
│     │ - Home button HIDDEN                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ Frontend starts polling loop:                                  │
│     │ - GET /api/print/{job_id}                                      │
│     │ - Interval: 1 second                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4   │ Backend receives status request                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5   │ Backend queries PrintJob from repository                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6   │ Backend queries CUPS for latest job state (if cups_job_id set) │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7   │ Backend returns PrintJobDTO:                                   │
│     │ - status: current state                                        │
│     │ - progress: 0-100                                              │
│     │ - message: human-readable status                               │
│     │ - can_go_home: boolean                                         │
│     │ - needs_user_retry: boolean                                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8   │ Frontend updates UI:                                           │
│     │ - Progress bar animation                                       │
│     │ - Status message update                                        │
│     │ - Status icon change                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 9   │ Frontend checks terminal conditions:                           │
│     │ - If status == COMPLETED: Go to step 10                        │
│     │ - If status == FAILED: Go to step 11                           │
│     │ - If status == ABORTED: Go to step 12                          │
│     │ - Otherwise: Continue polling (back to step 3)                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 10  │ COMPLETED: Stop polling, navigate to Complete page             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 11  │ FAILED: Stop polling, navigate to Error page                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 12  │ ABORTED: Stop polling, navigate to Home page                   │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Status Progression

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  NORMAL PROGRESSION                                                         │
│                                                                             │
│  PROCESSING ──► SENDING ──► PRINTING ──► COMPLETED                         │
│      25%          50%          75%          100%                            │
│                                                                             │
│  Messages:                                                                  │
│  - "Processing images..." / "이미지 처리 중..."                             │
│  - "Sending to printer..." / "프린터로 전송 중..."                          │
│  - "Printing..." / "인쇄 중..."                                            │
│  - "Complete!" / "완료!"                                                   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ERROR WITH AUTO-RETRY                                                      │
│                                                                             │
│  PRINTING ──► ERROR ──► SENDING ──► PRINTING ──► ...                       │
│                  │                                                          │
│                  └── "Retrying... (1/3)" / "재시도 중... (1/3)"             │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FAILED (after max retries)                                                 │
│                                                                             │
│  ERROR ──► ERROR ──► ERROR ──► FAILED                                      │
│   1/3       2/3       3/3        │                                          │
│                                  └── needs_user_retry = true                │
│                                      Navigate to Error page                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Alternative Flows

### AF-1: Job Already Complete on Load

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 3a  │ First poll returns status: COMPLETED                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3b  │ Frontend skips polling loop                                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3c  │ Navigate directly to Complete page                            │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-2: Recovery After Page Refresh

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 1a  │ User refreshes Printing page                                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1b  │ Frontend retrieves job_id from sessionStorage                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1c  │ If found: Resume polling with existing job_id                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1d  │ If not found: Navigate to Home (session lost)                 │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-3: Auto-Retry In Progress

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 8a  │ Status returns ERROR with retry_count < 3                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8b  │ Frontend shows retry indicator:                               │
│     │ - "Retrying... (2/3)"                                         │
│     │ - Progress bar shows retry attempt                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8c  │ Continue polling (backend handles retry)                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8d  │ When status changes to SENDING/PRINTING: Clear retry message  │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Exception Flows

### EX-1: Network Error During Poll

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Fetch request fails (network error)                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Frontend shows connection warning:                            │
│     │ - "Connection lost. Reconnecting..." (top banner)             │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Frontend continues polling with exponential backoff:          │
│     │ - 1s → 2s → 4s → 8s (max)                                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ On successful reconnection:                                   │
│     │ - Hide warning banner                                         │
│     │ - Resume normal 1s polling                                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ E5  │ After 30 failed attempts:                                     │
│     │ - Show permanent error                                        │
│     │ - Offer [Go Home] button                                      │
│     │ - Note: Print may still complete on backend                   │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-2: Job Not Found (404)

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Backend returns 404 for job_id                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Frontend stops polling                                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Show error: "Job not found. It may have expired."             │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Offer [Start New Session] button                              │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-3: Backend Restart During Print

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Backend restarts while job in PRINTING state                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Job recovered from SQLite with status PRINTING                │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Backend reconnects to CUPS, queries job status                │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ If CUPS job complete: Update status to COMPLETED              │
├─────┼────────────────────────────────────────────────────────────────┤
│ E5  │ If CUPS job missing: Mark as ERROR, allow retry               │
├─────┼────────────────────────────────────────────────────────────────┤
│ E6  │ Frontend continues polling, receives recovered state          │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Postconditions

### Job Completed

| ID | Condition |
|----|-----------|
| POST-1 | Polling stopped |
| POST-2 | User on Complete page |
| POST-3 | Session marked as PRINTED |
| POST-4 | Print output collected |

### Job Failed

| ID | Condition |
|----|-----------|
| POST-F1 | Polling stopped |
| POST-F2 | User on Error page |
| POST-F3 | Retry options available |

---

## Business Rules

| ID | Rule |
|----|------|
| MON-BR-1 | Poll interval: 1 second (fixed) |
| MON-BR-2 | Network retry: Exponential backoff up to 8 seconds |
| MON-BR-3 | Max poll failures before showing permanent error: 30 |
| MON-BR-4 | Home button hidden until can_go_home = true |
| MON-BR-5 | Page refresh recovers state from sessionStorage |

---

## Data Requirements

### Poll Response

```typescript
interface PrintJobStatusResponse {
  job_id: string;
  status: 'processing' | 'sending' | 'printing' | 'completed' | 'error' | 'failed' | 'aborted';
  progress: number;           // 0-100
  message: string;            // English message
  message_ko: string;         // Korean message
  can_go_home: boolean;       // True when terminal
  needs_user_retry: boolean;  // True when FAILED
  retry_count: number;        // 0-3
  cups_job_id?: number;       // CUPS reference if available
  error_code?: string;        // Error identifier if error
}
```

---

## UI/UX Requirements

### Printing Page Layout

```
┌─────────────────────────────────────────────────────────────────┐
│                         (No Home button)                        │
│                                                                 │
│                     Printing... / 인쇄 중...                     │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │              [Composite Image Preview]                  │    │
│  │                     (centered)                          │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│                          🖨️                                     │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │██████████████████████████████░░░░░░░░░░░░░░│ 65%        │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│                 Sending to printer...                           │
│                 프린터로 전송 중...                              │
│                                                                 │
│                                                                 │
│         ⚠️ Please wait. Do not close this page.                 │
│            잠시만 기다려주세요. 페이지를 닫지 마세요.             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Auto-Retry State

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                     Printing... / 인쇄 중...                     │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              [Composite Image Preview]                  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│                          🔄                                     │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │██████████████████░░░░░░░░░░░░░░░░░░░░░░░░░│ 40%         │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│                 Retrying... (2/3)                               │
│                 재시도 중... (2/3)                               │
│                                                                 │
│       ⚠️ Printer connection issue. Retrying automatically.      │
│          프린터 연결 문제. 자동으로 재시도 중입니다.              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Status Icons

| Status | Icon | Color |
|--------|------|-------|
| PROCESSING | ⚙️ | Blue (#00A1DE) |
| SENDING | 📤 | Purple |
| PRINTING | 🖨️ | Orange |
| COMPLETED | ✅ | Green (#20603D) |
| ERROR/Retrying | 🔄 | Yellow (#FAD201) |
| FAILED | ❌ | Red |

---

## Technical Notes

### usePrintStatus Hook

```typescript
// hooks/usePrintStatus.ts

interface UsePrintStatusOptions {
  jobId: string;
  pollingInterval?: number;
  onComplete?: () => void;
  onFailed?: () => void;
  onAborted?: () => void;
}

interface UsePrintStatusReturn {
  status: PrintJobStatusResponse | null;
  isPolling: boolean;
  error: Error | null;
  networkRetries: number;
}

const usePrintStatus = ({
  jobId,
  pollingInterval = 1000,
  onComplete,
  onFailed,
  onAborted,
}: UsePrintStatusOptions): UsePrintStatusReturn => {
  const [status, setStatus] = useState<PrintJobStatusResponse | null>(null);
  const [isPolling, setIsPolling] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [networkRetries, setNetworkRetries] = useState(0);

  useEffect(() => {
    if (!isPolling) return;

    let timeoutId: NodeJS.Timeout;
    let currentInterval = pollingInterval;

    const poll = async () => {
      try {
        const response = await api.getPrintJobStatus(jobId);
        setStatus(response);
        setNetworkRetries(0);
        currentInterval = pollingInterval; // Reset to normal interval

        // Check terminal states
        if (response.status === 'completed') {
          setIsPolling(false);
          onComplete?.();
          return;
        }

        if (response.status === 'failed') {
          setIsPolling(false);
          onFailed?.();
          return;
        }

        if (response.status === 'aborted') {
          setIsPolling(false);
          onAborted?.();
          return;
        }

        // Continue polling
        timeoutId = setTimeout(poll, currentInterval);

      } catch (err) {
        setNetworkRetries(prev => prev + 1);

        if (networkRetries >= 30) {
          setError(new Error('Connection lost'));
          setIsPolling(false);
          return;
        }

        // Exponential backoff
        currentInterval = Math.min(currentInterval * 2, 8000);
        timeoutId = setTimeout(poll, currentInterval);
      }
    };

    // Initial poll
    poll();

    return () => clearTimeout(timeoutId);
  }, [jobId, isPolling, pollingInterval, onComplete, onFailed, onAborted]);

  return { status, isPolling, error, networkRetries };
};
```

### Progress Bar Animation

```css
/* Smooth progress bar updates */
.progress-bar {
  transition: width 0.3s ease-out;
}

.progress-bar.indeterminate {
  animation: indeterminate 1.5s ease-in-out infinite;
}

@keyframes indeterminate {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
```

---

## Sequence Diagram

```
┌──────┐       ┌──────────┐       ┌──────────┐       ┌──────────┐
│ User │       │ Frontend │       │ Backend  │       │   CUPS   │
└──┬───┘       └────┬─────┘       └────┬─────┘       └────┬─────┘
   │                │                  │                  │
   │ View progress  │                  │                  │
   │◄───────────────│                  │                  │
   │                │                  │                  │
   │                │ GET /print/{id}  │                  │
   │                │─────────────────►│                  │
   │                │                  │                  │
   │                │                  │ getJobs()        │
   │                │                  │─────────────────►│
   │                │                  │                  │
   │                │                  │ job state        │
   │                │                  │◄─────────────────│
   │                │                  │                  │
   │                │ { status, progress }                │
   │                │◄─────────────────│                  │
   │                │                  │                  │
   │ Updated UI     │                  │                  │
   │◄───────────────│                  │                  │
   │                │                  │                  │
   │                │    (repeat every 1 second)         │
   │                │                  │                  │
   │                │ GET /print/{id}  │                  │
   │                │─────────────────►│                  │
   │                │                  │                  │
   │                │ { status: completed }               │
   │                │◄─────────────────│                  │
   │                │                  │                  │
   │ Navigate to    │                  │                  │
   │ Complete page  │                  │                  │
   │◄───────────────│                  │                  │
   │                │                  │                  │
```

---

## Related Use Cases

- **UC-005**: Submit Print Job (precedes this)
- **UC-007**: Retry Failed Print (if this ends in FAILED)
- **UC-203**: Auto-Retry Print (system background retry)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
