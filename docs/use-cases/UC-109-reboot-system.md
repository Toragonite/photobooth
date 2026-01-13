# UC-109: Reboot System

## Summary

Admin initiates a full system reboot of the Raspberry Pi from the dashboard. This is a last-resort action when individual service restarts don't resolve issues.

---

## Actors

| Actor | Type | Description |
|-------|------|-------------|
| **Admin** | Primary | Operator initiating reboot |
| **System** | Secondary | Executes reboot command |

---

## Preconditions

| ID | Condition |
|----|-----------|
| PRE-1 | Admin is authenticated |
| PRE-2 | No active print jobs in progress |

---

## Trigger

Admin taps [Reboot System] button on System Management page.

---

## Main Flow

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Step                                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ Admin navigates to System Management section                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ Admin taps [Reboot System] button                             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ System checks for active print jobs                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4   │ System shows critical warning dialog:                         │
│     │ ⚠️ "Reboot Raspberry Pi?"                                      │
│     │                                                               │
│     │ "This will:"                                                  │
│     │ "• Stop all services"                                         │
│     │ "• Disconnect all users"                                      │
│     │ "• Take 30-60 seconds to restart"                             │
│     │                                                               │
│     │ "Any active sessions will be lost."                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5   │ Admin confirms reboot                                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6   │ Frontend sends: POST /api/admin/system/reboot                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7   │ Backend schedules reboot (10 second delay):                   │
│     │ - Log reboot request                                          │
│     │ - Gracefully stop services                                    │
│     │ - Execute: sudo reboot                                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8   │ Return "reboot scheduled" response                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ 9   │ Frontend shows countdown:                                     │
│     │ "System rebooting in 10... 9... 8..."                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 10  │ Connection lost (system rebooting)                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ 11  │ Frontend shows "Waiting for system..."                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ 12  │ Frontend polls for backend availability                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 13  │ When backend responds: "System is back online"                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 14  │ Admin must re-authenticate (session expired)                  │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Alternative Flows

### AF-1: Active Print Jobs

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 3a  │ System detects active print jobs                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3b  │ Show additional warning:                                      │
│     │ "⚠️ There are 2 active print jobs!"                           │
│     │ "Rebooting now will cancel them."                             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3c  │ Offer options:                                                │
│     │ - "Wait for prints to complete" (recommended)                 │
│     │ - "Reboot anyway" (destructive)                               │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3d  │ If wait selected: Show print status, enable reboot when done  │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-2: Cancel Reboot

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 9a  │ During countdown, admin taps [Cancel]                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 9b  │ Frontend sends: POST /api/admin/system/reboot/cancel          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 9c  │ Backend cancels scheduled reboot                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ 9d  │ Show confirmation: "Reboot cancelled"                         │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-3: Emergency Reboot (Unresponsive)

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 1a  │ System is partially unresponsive                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2a  │ Admin holds [Reboot] button for 5 seconds                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3a  │ Emergency reboot triggered with minimal delay (2 seconds)     │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4a  │ Skip graceful shutdown, force reboot                          │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Exception Flows

### EX-1: Reboot Command Fails

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ sudo reboot command fails (permission, etc.)                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Log error                                                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Return error: "Reboot failed. Check system configuration."    │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Suggest physical power cycle if persistent                    │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-2: System Doesn't Come Back

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Frontend polling doesn't get response after 3 minutes         │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Show message:                                                 │
│     │ "System is taking longer than expected to restart."           │
│     │                                                               │
│     │ "Possible causes:"                                            │
│     │ "• System is still booting"                                   │
│     │ "• SD card issue"                                             │
│     │ "• Power problem"                                             │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ "Try reconnecting to Wi-Fi 'photobooth'"                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ [Keep Waiting] [Stop Checking] buttons                        │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Postconditions

| ID | Condition |
|----|-----------|
| POST-1 | System rebooted and services restarted |
| POST-2 | All sessions reset (clean state) |
| POST-3 | Admin must re-authenticate |
| POST-4 | Reboot logged for audit |

---

## Business Rules

| ID | Rule |
|----|------|
| RBT-BR-1 | Reboot requires explicit confirmation |
| RBT-BR-2 | Active print warning required |
| RBT-BR-3 | 10 second delay allows cancellation |
| RBT-BR-4 | Reboot command logged with admin ID |
| RBT-BR-5 | Expected reboot time: 30-60 seconds |

---

## UI/UX Requirements

### Reboot Button Location

```
System Management Page:
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ┌─── System ───────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │  ⏱️ System Uptime: 3 days, 14 hours, 22 minutes          │   │
│  │                                                          │   │
│  │  ┌──────────────────────────────────────────────────┐    │   │
│  │  │  🔄 Full System Reboot                           │    │   │
│  │  │                                                  │    │   │
│  │  │  Restarts the entire Raspberry Pi.               │    │   │
│  │  │  All active sessions will be lost.               │    │   │
│  │  │                                                  │    │   │
│  │  │  ⚠️ Use only if individual service               │    │   │
│  │  │     restarts don't resolve the issue.           │    │   │
│  │  │                                                  │    │   │
│  │  │                    ┌─────────────────────────┐   │    │   │
│  │  │                    │  🔄 Reboot System       │   │    │   │
│  │  │                    └─────────────────────────┘   │    │   │
│  │  │                         Red/destructive         │    │   │
│  │  │                                                  │    │   │
│  │  └──────────────────────────────────────────────────┘    │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Critical Warning Dialog

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│     ┌─────────────────────────────────────────────────────┐     │
│     │                                                     │     │
│     │     ⚠️ Reboot Raspberry Pi?                         │     │
│     │                                                     │     │
│     │     This will:                                      │     │
│     │     • Stop all services                             │     │
│     │     • Disconnect all users                          │     │
│     │     • Take 30-60 seconds to restart                 │     │
│     │                                                     │     │
│     │     Any active sessions will be lost.               │     │
│     │                                                     │     │
│     │     Are you sure you want to reboot?                │     │
│     │                                                     │     │
│     │   ┌──────────────┐     ┌──────────────────┐         │     │
│     │   │    Cancel    │     │  Yes, Reboot     │         │     │
│     │   └──────────────┘     └──────────────────┘         │     │
│     │                            (destructive red)        │     │
│     │                                                     │     │
│     └─────────────────────────────────────────────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Active Print Warning

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│     ┌─────────────────────────────────────────────────────┐     │
│     │                                                     │     │
│     │     ⚠️ Active Print Jobs!                           │     │
│     │                                                     │     │
│     │     There are 2 print jobs currently in progress.   │     │
│     │                                                     │     │
│     │     • Job abc-123: Printing (75%)                   │     │
│     │     • Job def-456: Queued                           │     │
│     │                                                     │     │
│     │     Rebooting now will cancel these jobs.           │     │
│     │                                                     │     │
│     │   ┌──────────────────┐  ┌─────────────────────┐     │     │
│     │   │ Wait for prints  │  │  Reboot anyway      │     │     │
│     │   │  (recommended)   │  │     ⚠️              │     │     │
│     │   └──────────────────┘  └─────────────────────┘     │     │
│     │                                                     │     │
│     └─────────────────────────────────────────────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Reboot Countdown

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│     ┌─────────────────────────────────────────────────────┐     │
│     │                                                     │     │
│     │              System Rebooting                       │     │
│     │                                                     │     │
│     │                    10                               │     │
│     │                                                     │     │
│     │              seconds remaining                      │     │
│     │                                                     │     │
│     │                                                     │     │
│     │              ┌──────────────────┐                   │     │
│     │              │      Cancel      │                   │     │
│     │              └──────────────────┘                   │     │
│     │                                                     │     │
│     └─────────────────────────────────────────────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Waiting for System

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│     ┌─────────────────────────────────────────────────────┐     │
│     │                                                     │     │
│     │              Waiting for System                     │     │
│     │                                                     │     │
│     │                   ◐ ◓ ◑ ◒                           │     │
│     │                                                     │     │
│     │     The system is rebooting...                      │     │
│     │                                                     │     │
│     │     This usually takes 30-60 seconds.               │     │
│     │                                                     │     │
│     │     Elapsed: 25 seconds                             │     │
│     │                                                     │     │
│     └─────────────────────────────────────────────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### System Back Online

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│     ┌─────────────────────────────────────────────────────┐     │
│     │                                                     │     │
│     │              ✓ System Online                        │     │
│     │                                                     │     │
│     │     The system has successfully rebooted.           │     │
│     │                                                     │     │
│     │     Reboot completed in 42 seconds.                 │     │
│     │                                                     │     │
│     │     Please log in again to continue.                │     │
│     │                                                     │     │
│     │              ┌──────────────────┐                   │     │
│     │              │   Go to Login    │                   │     │
│     │              └──────────────────┘                   │     │
│     │                                                     │     │
│     └─────────────────────────────────────────────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technical Notes

### API Endpoints

```typescript
// POST /api/admin/system/reboot
interface RebootRequest {
  force?: boolean;  // Skip graceful shutdown
}

interface RebootResponse {
  success: boolean;
  message: string;
  scheduled_at: string;
  delay_seconds: number;
}

// POST /api/admin/system/reboot/cancel
interface CancelRebootResponse {
  success: boolean;
  message: string;
}

// GET /api/health
// Used to check if system is back online
interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  uptime_seconds: number;
}
```

### Backend Implementation

```python
# System reboot handler

import asyncio
import subprocess
from datetime import datetime

class SystemRebootService:
    REBOOT_DELAY = 10  # seconds
    _reboot_task: asyncio.Task | None = None
    _reboot_scheduled_at: datetime | None = None

    async def schedule_reboot(self, force: bool = False) -> dict:
        """Schedule system reboot."""
        # Check for active prints
        if not force:
            active_jobs = await self._get_active_print_jobs()
            if active_jobs:
                raise ActivePrintJobsError(
                    f"{len(active_jobs)} active print jobs"
                )

        # Cancel existing scheduled reboot
        if self._reboot_task and not self._reboot_task.done():
            self._reboot_task.cancel()

        # Log reboot request
        logger.warning("System reboot scheduled", extra={
            'force': force,
            'delay': self.REBOOT_DELAY,
        })

        # Schedule reboot
        self._reboot_scheduled_at = datetime.utcnow()
        self._reboot_task = asyncio.create_task(
            self._execute_reboot(force)
        )

        return {
            'success': True,
            'message': f"Reboot scheduled in {self.REBOOT_DELAY} seconds",
            'scheduled_at': self._reboot_scheduled_at.isoformat(),
            'delay_seconds': self.REBOOT_DELAY,
        }

    async def cancel_reboot(self) -> dict:
        """Cancel scheduled reboot."""
        if self._reboot_task and not self._reboot_task.done():
            self._reboot_task.cancel()
            logger.info("System reboot cancelled")
            return {
                'success': True,
                'message': "Reboot cancelled",
            }
        return {
            'success': False,
            'message': "No reboot scheduled",
        }

    async def _execute_reboot(self, force: bool):
        """Execute the reboot after delay."""
        try:
            # Wait for delay (allows cancellation)
            await asyncio.sleep(self.REBOOT_DELAY)

            logger.warning("Executing system reboot NOW")

            # Graceful shutdown of services (unless force)
            if not force:
                await self._graceful_shutdown()

            # Execute reboot
            subprocess.Popen(
                ['sudo', 'reboot'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        except asyncio.CancelledError:
            logger.info("Reboot was cancelled")
            raise

    async def _graceful_shutdown(self):
        """Gracefully stop services before reboot."""
        # Stop accepting new requests
        # Wait for in-progress operations to complete (max 5s)
        await asyncio.sleep(2)

    async def _get_active_print_jobs(self) -> list:
        """Get list of active print jobs."""
        jobs = await self._job_repo.get_by_status(PrintStatus.PRINTING)
        jobs += await self._job_repo.get_by_status(PrintStatus.PROCESSING)
        return jobs
```

### Frontend Reconnection Logic

```typescript
// Reboot handling component

const RebootHandler: React.FC = () => {
  const [stage, setStage] = useState<
    'idle' | 'countdown' | 'waiting' | 'online' | 'timeout'
  >('idle');
  const [countdown, setCountdown] = useState(10);
  const [elapsed, setElapsed] = useState(0);

  const initiateReboot = async () => {
    const response = await fetch('/api/admin/system/reboot', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });

    if (response.ok) {
      setStage('countdown');
      startCountdown();
    }
  };

  const startCountdown = () => {
    const interval = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(interval);
          setStage('waiting');
          startWaiting();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const startWaiting = () => {
    const startTime = Date.now();
    const maxWait = 180000; // 3 minutes

    const checkHealth = async () => {
      try {
        const response = await fetch('/api/health', {
          signal: AbortSignal.timeout(5000),
        });

        if (response.ok) {
          setStage('online');
          return;
        }
      } catch {
        // Expected while system is down
      }

      const elapsed = Date.now() - startTime;
      setElapsed(Math.floor(elapsed / 1000));

      if (elapsed < maxWait) {
        setTimeout(checkHealth, 3000);
      } else {
        setStage('timeout');
      }
    };

    setTimeout(checkHealth, 5000);
  };

  const cancelReboot = async () => {
    await fetch('/api/admin/system/reboot/cancel', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    setStage('idle');
    setCountdown(10);
  };

  // Render based on stage...
};
```

---

## Related Use Cases

- **UC-105**: Restart Service (try before reboot)
- **UC-102**: View System Status (check health after reboot)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
