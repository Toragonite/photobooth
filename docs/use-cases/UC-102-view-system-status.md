# UC-102: View System Status

## Summary

Admin views comprehensive system health information on the admin dashboard. This includes printer status, storage usage, system resources, service health, and recent activity. Designed for phone access without needing direct Pi inspection.

---

## Actors

| Actor | Type | Description |
|-------|------|-------------|
| **Admin** | Primary | Operator monitoring system health |
| **System** | Secondary | Provides status information |

---

## Preconditions

| ID | Condition |
|----|-----------|
| PRE-1 | Admin is authenticated (valid JWT token) |
| PRE-2 | Admin is on dashboard page |
| PRE-3 | Backend services are running |

---

## Trigger

Admin navigates to System Status section on dashboard OR dashboard auto-refreshes.

---

## Main Flow

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Step                                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ Admin accesses dashboard (already authenticated)              │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ Frontend requests system status:                              │
│     │ GET /api/admin/status                                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ Backend collects status from multiple sources:                │
│     │ - CUPS printer status                                         │
│     │ - Disk/storage usage                                          │
│     │ - Memory usage                                                │
│     │ - CPU temperature                                             │
│     │ - Service health checks                                       │
│     │ - Database statistics                                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4   │ Backend returns SystemStatusDTO                               │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5   │ Frontend displays status dashboard:                           │
│     │ - Overall health indicator (green/yellow/red)                 │
│     │ - Printer status card                                         │
│     │ - Storage usage card                                          │
│     │ - System resources card                                       │
│     │ - Recent activity summary                                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6   │ Dashboard auto-refreshes every 10 seconds                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7   │ Admin reviews status and takes action if needed               │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Alternative Flows

### AF-1: Manual Refresh

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 6a  │ Admin taps [Refresh] button                                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6b  │ Frontend immediately requests fresh status                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6c  │ UI shows loading indicator during fetch                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6d  │ Display updated status                                        │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-2: View Detailed Logs

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 7a  │ Admin taps [View Logs] on a status card                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7b  │ Navigate to filtered log view:                                │
│     │ - Printer card → Print job logs                               │
│     │ - System card → System event logs                             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7c  │ Display recent log entries with timestamps                    │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-3: Quick Actions from Status Card

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 7a  │ Printer offline: [Test Connection] button appears             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7b  │ Storage high: [Clean Old Sessions] button appears             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7c  │ Admin taps action button                                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7d  │ System executes action and updates status                     │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Exception Flows

### EX-1: Status Fetch Fails

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ GET /api/admin/status times out or returns error              │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Frontend shows warning banner:                                │
│     │ "Unable to fetch status. Backend may be unresponsive."        │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Previous status data retained with "stale" indicator          │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ [Retry] button available                                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ E5  │ Auto-refresh continues attempting                             │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-2: Partial Status Available

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Some subsystems fail to report (e.g., CUPS unreachable)       │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Backend returns partial status with error flags               │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Frontend shows available data                                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Unavailable sections show "Status Unknown" with reason        │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-3: Token Expired During View

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Auto-refresh request returns 401 Unauthorized                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Frontend displays session expired message                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Redirect to admin login page                                  │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Postconditions

| ID | Condition |
|----|-----------|
| POST-1 | Admin has current system status view |
| POST-2 | Any critical issues are visible |
| POST-3 | Quick actions available for common issues |

---

## Business Rules

| ID | Rule |
|----|------|
| SYS-BR-1 | Status auto-refreshes every 10 seconds |
| SYS-BR-2 | Overall health is RED if any critical component fails |
| SYS-BR-3 | Overall health is YELLOW if warnings exist |
| SYS-BR-4 | Storage warning at 80%, critical at 95% |
| SYS-BR-5 | Temperature warning at 70°C, critical at 80°C |
| SYS-BR-6 | Memory warning at 80%, critical at 90% |

---

## Status Indicators

### Health Levels

| Level | Color | Criteria |
|-------|-------|----------|
| **Healthy** | 🟢 Green | All systems operational |
| **Warning** | 🟡 Yellow | Non-critical issues present |
| **Critical** | 🔴 Red | Critical component failure |
| **Unknown** | ⚪ Gray | Unable to determine status |

### Printer Status Mapping

| CUPS Status | Display | Health |
|-------------|---------|--------|
| idle | Ready | 🟢 |
| processing | Printing | 🟢 |
| stopped | Paused | 🟡 |
| offline | Offline | 🔴 |
| not-found | Not Connected | 🔴 |

---

## UI/UX Requirements

### Dashboard Layout (Mobile-Optimized)

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back                 System Status              [🔄 Refresh] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │          🟢 System Healthy                              │    │
│  │             Last updated: 12:34:56                      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─── Printer ──────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │  🖨️ Canon Selphy CP1500                                  │   │
│  │                                                          │   │
│  │  Status:    🟢 Ready (idle)                              │   │
│  │  Queue:     0 jobs                                       │   │
│  │  Today:     15 prints completed                          │   │
│  │                                                          │   │
│  │  [Test Print]                              [View Queue →] │   │
│  └──────────────────────────────────────────────────────────┘   │
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
│  │                                     [Clean Old Data →]   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─── System Resources ─────────────────────────────────────┐   │
│  │                                                          │   │
│  │  🌡️ CPU Temperature                                      │   │
│  │  48°C  ████████░░░░░░░░░░░░░  Normal                     │   │
│  │                                                          │   │
│  │  🧠 Memory (8GB)                                         │   │
│  │  2.1 GB / 8 GB  ██████░░░░░░░░░░░░░░  26%                │   │
│  │                                                          │   │
│  │  ⏱️ Uptime: 3 days, 14 hours                             │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─── Services ─────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │  ✅ Backend API         Running                          │   │
│  │  ✅ CUPS Service        Running                          │   │
│  │  ✅ Database            Connected (SQLite)               │   │
│  │  ✅ Wi-Fi AP            Active (3 clients)               │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─── Today's Activity ─────────────────────────────────────┐   │
│  │                                                          │   │
│  │  📸 Sessions Started:    23                              │   │
│  │  ✅ Sessions Completed:  21                              │   │
│  │  🖨️ Print Jobs:          21 (2 failed, 19 success)       │   │
│  │  📊 Success Rate:        90.5%                           │   │
│  │                                                          │   │
│  │                                      [View Details →]    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Warning State Example

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │          🟡 Warning: Issues Detected                    │    │
│  │                                                         │    │
│  │  ⚠️ Storage usage above 80%                             │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─── Storage ──────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │  💾 SD Card (256GB)                          ⚠️ Warning  │   │
│  │                                                          │   │
│  │  Used:     210 GB / 256 GB                               │   │
│  │  █████████████████████████████░░░░  82.0%                │   │
│  │                                                          │   │
│  │  ⚠️ Storage running low. Consider cleaning old data.     │   │
│  │                                                          │   │
│  │  [Clean Sessions Older Than 30 Days]                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Critical State Example

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │          🔴 Critical: Printer Offline                   │    │
│  │                                                         │    │
│  │  The printer is not responding.                         │    │
│  │  Please check the connection.                           │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─── Printer ──────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │  🖨️ Canon Selphy CP1500                      🔴 Critical │   │
│  │                                                          │   │
│  │  Status:    🔴 Offline                                   │   │
│  │                                                          │   │
│  │  Please check:                                           │   │
│  │  • Printer is powered on                                 │   │
│  │  • USB cable is connected                                │   │
│  │  • Paper/ink are loaded                                  │   │
│  │                                                          │   │
│  │  [Test Connection]              [Restart Print Service]  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technical Notes

### API Response

```typescript
// GET /api/admin/status

interface SystemStatusDTO {
  timestamp: string;  // ISO 8601
  overall_health: 'healthy' | 'warning' | 'critical' | 'unknown';
  warnings: string[];
  errors: string[];

  printer: PrinterStatusDTO;
  storage: StorageStatusDTO;
  system: SystemResourcesDTO;
  services: ServiceStatusDTO[];
  activity: ActivitySummaryDTO;
}

interface PrinterStatusDTO {
  name: string;
  model: string;
  status: 'idle' | 'processing' | 'stopped' | 'offline' | 'not-found';
  health: 'healthy' | 'warning' | 'critical' | 'unknown';
  queue_count: number;
  today_completed: number;
  today_failed: number;
  error_message?: string;
}

interface StorageStatusDTO {
  total_bytes: number;
  used_bytes: number;
  free_bytes: number;
  percent_used: number;
  health: 'healthy' | 'warning' | 'critical';
  session_count: number;
  photo_storage_bytes: number;
  system_storage_bytes: number;
}

interface SystemResourcesDTO {
  cpu_temp_celsius: number;
  memory_total_bytes: number;
  memory_used_bytes: number;
  memory_percent: number;
  uptime_seconds: number;
  health: 'healthy' | 'warning' | 'critical';
}

interface ServiceStatusDTO {
  name: string;
  status: 'running' | 'stopped' | 'error';
  details?: string;
}

interface ActivitySummaryDTO {
  date: string;  // YYYY-MM-DD
  sessions_started: number;
  sessions_completed: number;
  sessions_abandoned: number;
  prints_total: number;
  prints_success: number;
  prints_failed: number;
  success_rate: number;
}
```

### Backend Implementation

```python
# System status service

import psutil
import subprocess
from pathlib import Path
from datetime import date

class SystemStatusService:
    def __init__(
        self,
        printer_service: PrinterService,
        session_repo: SessionRepository,
        print_job_repo: PrintJobRepository,
        storage_path: Path,
    ):
        self._printer = printer_service
        self._sessions = session_repo
        self._jobs = print_job_repo
        self._storage_path = storage_path

    def get_status(self) -> SystemStatusDTO:
        printer = self._get_printer_status()
        storage = self._get_storage_status()
        system = self._get_system_resources()
        services = self._get_service_status()
        activity = self._get_activity_summary()

        # Determine overall health
        healths = [printer.health, storage.health, system.health]
        if 'critical' in healths:
            overall = 'critical'
        elif 'warning' in healths:
            overall = 'warning'
        elif 'unknown' in healths:
            overall = 'unknown'
        else:
            overall = 'healthy'

        # Collect warnings and errors
        warnings = []
        errors = []

        if storage.percent_used >= 80:
            warnings.append(f"Storage usage at {storage.percent_used:.1f}%")
        if system.cpu_temp_celsius >= 70:
            warnings.append(f"CPU temperature at {system.cpu_temp_celsius}°C")
        if printer.status == 'offline':
            errors.append("Printer is offline")
        elif printer.status == 'not-found':
            errors.append("Printer not connected")

        return SystemStatusDTO(
            timestamp=datetime.utcnow().isoformat(),
            overall_health=overall,
            warnings=warnings,
            errors=errors,
            printer=printer,
            storage=storage,
            system=system,
            services=services,
            activity=activity,
        )

    def _get_printer_status(self) -> PrinterStatusDTO:
        try:
            info = self._printer.get_printer_info()
            today_stats = self._jobs.get_today_stats()

            # Map CUPS status to health
            if info.status in ('idle', 'processing'):
                health = 'healthy'
            elif info.status == 'stopped':
                health = 'warning'
            else:
                health = 'critical'

            return PrinterStatusDTO(
                name=info.name,
                model=info.model,
                status=info.status,
                health=health,
                queue_count=info.queue_count,
                today_completed=today_stats.completed,
                today_failed=today_stats.failed,
            )
        except Exception as e:
            return PrinterStatusDTO(
                name="Unknown",
                model="Unknown",
                status="not-found",
                health="critical",
                queue_count=0,
                today_completed=0,
                today_failed=0,
                error_message=str(e),
            )

    def _get_storage_status(self) -> StorageStatusDTO:
        disk = psutil.disk_usage(str(self._storage_path))
        session_count = self._sessions.count_all()

        # Calculate photo storage
        photo_size = sum(
            f.stat().st_size
            for f in self._storage_path.rglob('*')
            if f.is_file()
        )

        # Determine health
        if disk.percent >= 95:
            health = 'critical'
        elif disk.percent >= 80:
            health = 'warning'
        else:
            health = 'healthy'

        return StorageStatusDTO(
            total_bytes=disk.total,
            used_bytes=disk.used,
            free_bytes=disk.free,
            percent_used=disk.percent,
            health=health,
            session_count=session_count,
            photo_storage_bytes=photo_size,
            system_storage_bytes=disk.used - photo_size,
        )

    def _get_system_resources(self) -> SystemResourcesDTO:
        # CPU temperature (Raspberry Pi specific)
        try:
            temp = psutil.sensors_temperatures()
            cpu_temp = temp.get('cpu_thermal', [{}])[0].current
        except:
            # Fallback for Pi
            try:
                result = subprocess.run(
                    ['vcgencmd', 'measure_temp'],
                    capture_output=True, text=True
                )
                cpu_temp = float(result.stdout.replace("temp=", "").replace("'C", ""))
            except:
                cpu_temp = 0

        mem = psutil.virtual_memory()
        boot_time = psutil.boot_time()
        uptime = time.time() - boot_time

        # Determine health
        if cpu_temp >= 80 or mem.percent >= 90:
            health = 'critical'
        elif cpu_temp >= 70 or mem.percent >= 80:
            health = 'warning'
        else:
            health = 'healthy'

        return SystemResourcesDTO(
            cpu_temp_celsius=cpu_temp,
            memory_total_bytes=mem.total,
            memory_used_bytes=mem.used,
            memory_percent=mem.percent,
            uptime_seconds=int(uptime),
            health=health,
        )

    def _get_service_status(self) -> list[ServiceStatusDTO]:
        services = []

        # Check backend (always running if we're here)
        services.append(ServiceStatusDTO(
            name="Backend API",
            status="running",
        ))

        # Check CUPS
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', 'cups'],
                capture_output=True, text=True
            )
            cups_status = 'running' if result.returncode == 0 else 'stopped'
        except:
            cups_status = 'error'

        services.append(ServiceStatusDTO(
            name="CUPS Service",
            status=cups_status,
        ))

        # Check database
        try:
            self._sessions.health_check()
            db_status = 'running'
            db_details = 'Connected (SQLite)'
        except Exception as e:
            db_status = 'error'
            db_details = str(e)

        services.append(ServiceStatusDTO(
            name="Database",
            status=db_status,
            details=db_details,
        ))

        # Check Wi-Fi AP
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', 'hostapd'],
                capture_output=True, text=True
            )
            wifi_status = 'running' if result.returncode == 0 else 'stopped'

            # Count connected clients
            if wifi_status == 'running':
                result = subprocess.run(
                    ['iw', 'dev', 'wlan0', 'station', 'dump'],
                    capture_output=True, text=True
                )
                client_count = result.stdout.count('Station')
                wifi_details = f"Active ({client_count} clients)"
            else:
                wifi_details = None
        except:
            wifi_status = 'error'
            wifi_details = None

        services.append(ServiceStatusDTO(
            name="Wi-Fi AP",
            status=wifi_status,
            details=wifi_details,
        ))

        return services

    def _get_activity_summary(self) -> ActivitySummaryDTO:
        today = date.today()
        sessions = self._sessions.get_stats_for_date(today)
        jobs = self._jobs.get_stats_for_date(today)

        total = jobs.completed + jobs.failed
        success_rate = (jobs.completed / total * 100) if total > 0 else 100.0

        return ActivitySummaryDTO(
            date=today.isoformat(),
            sessions_started=sessions.started,
            sessions_completed=sessions.completed,
            sessions_abandoned=sessions.abandoned,
            prints_total=total,
            prints_success=jobs.completed,
            prints_failed=jobs.failed,
            success_rate=success_rate,
        )
```

### Frontend Hook

```typescript
// useSystemStatus hook

interface UseSystemStatusReturn {
  status: SystemStatusDTO | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

const useSystemStatus = (
  autoRefreshInterval: number = 10000
): UseSystemStatusReturn => {
  const [status, setStatus] = useState<SystemStatusDTO | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const { token } = useAdminAuth();

  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch('/api/admin/status', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.status === 401) {
        throw new Error('Session expired');
      }

      if (!response.ok) {
        throw new Error(`Failed to fetch status: ${response.status}`);
      }

      const data = await response.json();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  // Initial fetch
  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // Auto-refresh
  useEffect(() => {
    const interval = setInterval(fetchStatus, autoRefreshInterval);
    return () => clearInterval(interval);
  }, [fetchStatus, autoRefreshInterval]);

  return {
    status,
    isLoading,
    error,
    refetch: fetchStatus,
  };
};
```

---

## Related Use Cases

- **UC-101**: Admin Login (prerequisite)
- **UC-103**: Manage Settings (accessible from dashboard)
- **UC-104**: View Print History (linked from activity)
- **UC-105**: Clean Storage (action from storage card)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
