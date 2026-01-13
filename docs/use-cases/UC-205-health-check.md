# UC-205: Health Check

## Summary

System performs periodic health checks on all components and services, detecting issues before they cause failures. Reports health status through API for dashboard display and triggers alerts for critical issues.

---

## Actors

| Actor | Type | Description |
|-------|------|-------------|
| **System** | Primary | Background health monitor |
| **Admin** | Observer | Views health status |

---

## Preconditions

| ID | Condition |
|----|-----------|
| PRE-1 | Backend service is running |
| PRE-2 | Health check endpoints accessible |

---

## Trigger

- **Periodic**: Every 30 seconds
- **On-demand**: API request from dashboard
- **Startup**: Full check on service start

---

## Main Flow

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Step                                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ Health check timer triggers (every 30 seconds)                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ Execute component health checks in parallel:                  │
│     │ a. Database connectivity                                      │
│     │ b. CUPS service status                                        │
│     │ c. Printer connectivity                                       │
│     │ d. Storage availability                                       │
│     │ e. Wi-Fi AP status                                            │
│     │ f. System resources (CPU, memory, temp)                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ Aggregate results into health status:                         │
│     │ - Each component: healthy/warning/critical/unknown            │
│     │ - Overall status: worst of all components                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4   │ Compare with previous health status                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5   │ If status changed: Log event                                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6   │ If critical issue detected: Attempt auto-recovery             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7   │ Cache health status for API queries                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8   │ Schedule next check                                           │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Health Check Components

### Database Health

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Check                                                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ Execute simple query: SELECT 1                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ Check response time < 100ms                                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ Verify write capability: INSERT/DELETE test row               │
├─────┼────────────────────────────────────────────────────────────────┤
│     │ Result:                                                        │
│     │ - healthy: Query succeeds < 100ms                             │
│     │ - warning: Query succeeds but slow (100-500ms)                │
│     │ - critical: Query fails or > 500ms                            │
└─────┴────────────────────────────────────────────────────────────────┘
```

### CUPS Service Health

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Check                                                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ Check systemctl status cups                                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ Verify CUPS socket is accessible                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ Query printer list via lpstat                                 │
├─────┼────────────────────────────────────────────────────────────────┤
│     │ Result:                                                        │
│     │ - healthy: Service running, socket accessible                 │
│     │ - warning: Service running but slow response                  │
│     │ - critical: Service stopped or unresponsive                   │
└─────┴────────────────────────────────────────────────────────────────┘
```

### Printer Health

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Check                                                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ Query printer status from CUPS                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ Check printer state reasons                                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ Verify USB connection (lsusb for Canon device)                │
├─────┼────────────────────────────────────────────────────────────────┤
│     │ Result:                                                        │
│     │ - healthy: Printer idle, no issues                            │
│     │ - warning: Printer busy or paper/ink low                      │
│     │ - critical: Printer offline or not connected                  │
└─────┴────────────────────────────────────────────────────────────────┘
```

### Storage Health

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Check                                                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ Check disk usage percentage                                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ Verify write capability: Create/delete test file              │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ Check for filesystem errors (read-only mount)                 │
├─────┼────────────────────────────────────────────────────────────────┤
│     │ Result:                                                        │
│     │ - healthy: Usage < 80%, writable                              │
│     │ - warning: Usage 80-95%                                       │
│     │ - critical: Usage > 95% or read-only                          │
└─────┴────────────────────────────────────────────────────────────────┘
```

### Wi-Fi AP Health

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Check                                                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ Check systemctl status hostapd                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ Verify interface is up (ip link show wlan0)                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ Check dnsmasq is running for DHCP                             │
├─────┼────────────────────────────────────────────────────────────────┤
│     │ Result:                                                        │
│     │ - healthy: AP active, DHCP running                            │
│     │ - warning: AP active but no clients                           │
│     │ - critical: AP or DHCP not running                            │
└─────┴────────────────────────────────────────────────────────────────┘
```

### System Resources Health

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Check                                                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ CPU temperature via vcgencmd                                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ Memory usage via psutil                                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ CPU usage (1 minute average)                                  │
├─────┼────────────────────────────────────────────────────────────────┤
│     │ Result:                                                        │
│     │ - healthy: Temp < 70°C, memory < 80%, CPU < 80%               │
│     │ - warning: Temp 70-80°C, memory 80-90%, CPU 80-95%            │
│     │ - critical: Temp > 80°C, memory > 90%, CPU > 95%              │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Alternative Flows

### AF-1: Auto-Recovery for CUPS

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 6a  │ CUPS service detected as stopped                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6b  │ Attempt restart: systemctl restart cups                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6c  │ Wait 5 seconds                                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6d  │ Re-check CUPS status                                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6e  │ If recovered: Log recovery event                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6f  │ If still failed: Log persistent failure, alert admin          │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-2: Startup Health Check

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 1a  │ Backend service starting                                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1b  │ Execute full health check before accepting requests           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1c  │ If critical issues: Log warning but continue                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1d  │ Attempt auto-recovery for recoverable issues                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1e  │ Begin accepting requests after initial check                  │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-3: On-Demand Health Check

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 1a  │ Admin requests: GET /api/health                               │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1b  │ Return cached health status (< 30 seconds old)                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1c  │ If cache stale: Execute fresh health check                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1d  │ Return comprehensive health report                            │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Exception Flows

### EX-1: Health Check Times Out

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Individual check exceeds timeout (5 seconds)                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Mark component as "unknown" status                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Continue with other health checks                             │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Log timeout for debugging                                     │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-2: Recovery Fails

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Auto-recovery attempt fails                                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Log failure with details                                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Set component to critical status                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Do not attempt recovery again for 5 minutes                   │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Postconditions

| ID | Condition |
|----|-----------|
| POST-1 | Health status cached and available via API |
| POST-2 | Issues logged for debugging |
| POST-3 | Auto-recovery attempted for recoverable issues |
| POST-4 | Admin dashboard shows current health |

---

## Business Rules

| ID | Rule |
|----|------|
| HLT-BR-1 | Health check interval: 30 seconds |
| HLT-BR-2 | Individual check timeout: 5 seconds |
| HLT-BR-3 | Auto-recovery cooldown: 5 minutes |
| HLT-BR-4 | Overall status = worst component status |
| HLT-BR-5 | Cache validity: 30 seconds |

---

## Health Status Values

| Status | Code | Description |
|--------|------|-------------|
| healthy | 0 | Component operating normally |
| warning | 1 | Degraded but functional |
| critical | 2 | Component failed or unavailable |
| unknown | 3 | Cannot determine status |

---

## Technical Notes

### API Endpoints

```typescript
// GET /api/health
// Simple health check for load balancers

interface SimpleHealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
}

// GET /api/health/detailed
// Full health report for dashboard

interface DetailedHealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  components: {
    database: ComponentHealth;
    cups: ComponentHealth;
    printer: ComponentHealth;
    storage: ComponentHealth;
    wifi: ComponentHealth;
    system: ComponentHealth;
  };
  uptime_seconds: number;
}

interface ComponentHealth {
  status: 'healthy' | 'warning' | 'critical' | 'unknown';
  message?: string;
  last_check: string;
  details?: Record<string, any>;
}
```

### Health Check Service Implementation

```python
# Health check service

import asyncio
import psutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum

class HealthStatus(IntEnum):
    HEALTHY = 0
    WARNING = 1
    CRITICAL = 2
    UNKNOWN = 3

@dataclass
class ComponentHealth:
    status: HealthStatus
    message: str = ""
    details: dict = None
    last_check: datetime = None

class HealthCheckService:
    CHECK_INTERVAL = 30  # seconds
    CHECK_TIMEOUT = 5    # seconds per component
    RECOVERY_COOLDOWN = 300  # seconds

    def __init__(self, db, storage_path: Path):
        self._db = db
        self._storage_path = storage_path
        self._cache: dict = {}
        self._last_recovery: dict = {}
        self._running = False

    async def start(self):
        """Start periodic health checks."""
        self._running = True

        # Initial check
        await self._run_checks()

        while self._running:
            await asyncio.sleep(self.CHECK_INTERVAL)
            await self._run_checks()

    async def stop(self):
        self._running = False

    async def get_health(self, force_refresh: bool = False) -> dict:
        """Get current health status."""
        if force_refresh or self._is_cache_stale():
            await self._run_checks()
        return self._cache

    def _is_cache_stale(self) -> bool:
        if 'timestamp' not in self._cache:
            return True
        age = time.time() - self._cache['timestamp']
        return age > self.CHECK_INTERVAL

    async def _run_checks(self):
        """Run all health checks in parallel."""
        checks = [
            ('database', self._check_database()),
            ('cups', self._check_cups()),
            ('printer', self._check_printer()),
            ('storage', self._check_storage()),
            ('wifi', self._check_wifi()),
            ('system', self._check_system()),
        ]

        results = {}
        for name, coro in checks:
            try:
                result = await asyncio.wait_for(coro, timeout=self.CHECK_TIMEOUT)
            except asyncio.TimeoutError:
                result = ComponentHealth(
                    status=HealthStatus.UNKNOWN,
                    message="Check timed out"
                )
            except Exception as e:
                result = ComponentHealth(
                    status=HealthStatus.UNKNOWN,
                    message=f"Check failed: {e}"
                )
            result.last_check = datetime.utcnow()
            results[name] = result

        # Attempt auto-recovery for critical components
        for name, health in results.items():
            if health.status == HealthStatus.CRITICAL:
                await self._attempt_recovery(name)

        # Calculate overall status
        statuses = [h.status for h in results.values()]
        if HealthStatus.CRITICAL in statuses:
            overall = 'unhealthy'
        elif HealthStatus.WARNING in statuses:
            overall = 'degraded'
        else:
            overall = 'healthy'

        self._cache = {
            'status': overall,
            'timestamp': time.time(),
            'components': {
                name: {
                    'status': h.status.name.lower(),
                    'message': h.message,
                    'last_check': h.last_check.isoformat(),
                    'details': h.details,
                }
                for name, h in results.items()
            }
        }

    async def _check_database(self) -> ComponentHealth:
        """Check database connectivity."""
        start = time.time()
        try:
            await self._db.execute("SELECT 1")
            latency = (time.time() - start) * 1000

            if latency < 100:
                return ComponentHealth(
                    status=HealthStatus.HEALTHY,
                    message=f"Response time: {latency:.0f}ms",
                    details={'latency_ms': latency}
                )
            elif latency < 500:
                return ComponentHealth(
                    status=HealthStatus.WARNING,
                    message=f"Slow response: {latency:.0f}ms",
                    details={'latency_ms': latency}
                )
            else:
                return ComponentHealth(
                    status=HealthStatus.CRITICAL,
                    message=f"Very slow: {latency:.0f}ms",
                    details={'latency_ms': latency}
                )
        except Exception as e:
            return ComponentHealth(
                status=HealthStatus.CRITICAL,
                message=f"Connection failed: {e}"
            )

    async def _check_cups(self) -> ComponentHealth:
        """Check CUPS service status."""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', 'cups'],
                capture_output=True,
                text=True,
                timeout=3,
            )

            if result.stdout.strip() == 'active':
                return ComponentHealth(
                    status=HealthStatus.HEALTHY,
                    message="CUPS service running"
                )
            else:
                return ComponentHealth(
                    status=HealthStatus.CRITICAL,
                    message=f"CUPS status: {result.stdout.strip()}"
                )
        except Exception as e:
            return ComponentHealth(
                status=HealthStatus.CRITICAL,
                message=f"Cannot check CUPS: {e}"
            )

    async def _check_printer(self) -> ComponentHealth:
        """Check printer connectivity."""
        try:
            result = subprocess.run(
                ['lpstat', '-p'],
                capture_output=True,
                text=True,
                timeout=3,
            )

            if 'idle' in result.stdout.lower():
                return ComponentHealth(
                    status=HealthStatus.HEALTHY,
                    message="Printer idle and ready"
                )
            elif 'printing' in result.stdout.lower():
                return ComponentHealth(
                    status=HealthStatus.HEALTHY,
                    message="Printer busy"
                )
            elif 'disabled' in result.stdout.lower():
                return ComponentHealth(
                    status=HealthStatus.CRITICAL,
                    message="Printer disabled"
                )
            else:
                return ComponentHealth(
                    status=HealthStatus.WARNING,
                    message=f"Printer status: {result.stdout.strip()}"
                )
        except Exception as e:
            return ComponentHealth(
                status=HealthStatus.CRITICAL,
                message=f"Cannot check printer: {e}"
            )

    async def _check_storage(self) -> ComponentHealth:
        """Check storage availability."""
        try:
            disk = psutil.disk_usage(str(self._storage_path))
            percent = disk.percent

            # Test write
            test_file = self._storage_path / '.health_check'
            test_file.write_text('test')
            test_file.unlink()

            if percent < 80:
                return ComponentHealth(
                    status=HealthStatus.HEALTHY,
                    message=f"Storage: {percent:.1f}% used",
                    details={
                        'percent_used': percent,
                        'free_bytes': disk.free,
                    }
                )
            elif percent < 95:
                return ComponentHealth(
                    status=HealthStatus.WARNING,
                    message=f"Storage low: {percent:.1f}% used",
                    details={
                        'percent_used': percent,
                        'free_bytes': disk.free,
                    }
                )
            else:
                return ComponentHealth(
                    status=HealthStatus.CRITICAL,
                    message=f"Storage critical: {percent:.1f}% used",
                    details={
                        'percent_used': percent,
                        'free_bytes': disk.free,
                    }
                )
        except PermissionError:
            return ComponentHealth(
                status=HealthStatus.CRITICAL,
                message="Storage is read-only"
            )
        except Exception as e:
            return ComponentHealth(
                status=HealthStatus.CRITICAL,
                message=f"Storage check failed: {e}"
            )

    async def _check_wifi(self) -> ComponentHealth:
        """Check Wi-Fi AP status."""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', 'hostapd'],
                capture_output=True,
                text=True,
                timeout=3,
            )

            if result.stdout.strip() != 'active':
                return ComponentHealth(
                    status=HealthStatus.CRITICAL,
                    message="Wi-Fi AP not running"
                )

            # Count connected clients
            result = subprocess.run(
                ['iw', 'dev', 'wlan0', 'station', 'dump'],
                capture_output=True,
                text=True,
                timeout=3,
            )
            clients = result.stdout.count('Station')

            return ComponentHealth(
                status=HealthStatus.HEALTHY,
                message=f"Wi-Fi AP active ({clients} clients)",
                details={'connected_clients': clients}
            )
        except Exception as e:
            return ComponentHealth(
                status=HealthStatus.WARNING,
                message=f"Cannot check Wi-Fi: {e}"
            )

    async def _check_system(self) -> ComponentHealth:
        """Check system resources."""
        try:
            # CPU temperature
            result = subprocess.run(
                ['vcgencmd', 'measure_temp'],
                capture_output=True,
                text=True,
                timeout=3,
            )
            temp = float(result.stdout.replace("temp=", "").replace("'C", ""))

            # Memory
            mem = psutil.virtual_memory()

            details = {
                'cpu_temp': temp,
                'memory_percent': mem.percent,
                'memory_available_mb': mem.available / 1024 / 1024,
            }

            if temp >= 80 or mem.percent >= 90:
                return ComponentHealth(
                    status=HealthStatus.CRITICAL,
                    message=f"Resources critical (Temp: {temp}°C, Mem: {mem.percent}%)",
                    details=details,
                )
            elif temp >= 70 or mem.percent >= 80:
                return ComponentHealth(
                    status=HealthStatus.WARNING,
                    message=f"Resources elevated (Temp: {temp}°C, Mem: {mem.percent}%)",
                    details=details,
                )
            else:
                return ComponentHealth(
                    status=HealthStatus.HEALTHY,
                    message=f"Resources normal (Temp: {temp}°C, Mem: {mem.percent}%)",
                    details=details,
                )
        except Exception as e:
            return ComponentHealth(
                status=HealthStatus.WARNING,
                message=f"Cannot check system: {e}"
            )

    async def _attempt_recovery(self, component: str):
        """Attempt auto-recovery for a failed component."""
        # Check cooldown
        last = self._last_recovery.get(component, 0)
        if time.time() - last < self.RECOVERY_COOLDOWN:
            return

        self._last_recovery[component] = time.time()

        if component == 'cups':
            logger.info("Attempting CUPS recovery...")
            subprocess.run(['sudo', 'systemctl', 'restart', 'cups'])
        elif component == 'wifi':
            logger.info("Attempting Wi-Fi recovery...")
            subprocess.run(['sudo', 'systemctl', 'restart', 'hostapd'])
```

---

## Related Use Cases

- **UC-102**: View System Status (displays health)
- **UC-105**: Restart Service (manual recovery)
- **UC-204**: Cleanup Storage (triggered by storage health)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
