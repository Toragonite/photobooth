# UC-105: Restart Service

## Summary

Admin restarts individual services (CUPS, backend, Wi-Fi AP) or the entire system to resolve issues. This provides remote control without physical access to the Raspberry Pi.

---

## Actors

| Actor | Type | Description |
|-------|------|-------------|
| **Admin** | Primary | Operator restarting services |
| **System** | Secondary | Executes restart commands |

---

## Preconditions

| ID | Condition |
|----|-----------|
| PRE-1 | Admin is authenticated |
| PRE-2 | Admin is on system management page |
| PRE-3 | Target service exists |

---

## Trigger

Admin taps restart button for a specific service.

---

## Main Flow

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Step                                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ Admin navigates to System Management section                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ Admin sees list of services with status:                      │
│     │ - CUPS (Print Service)                                        │
│     │ - Backend API                                                 │
│     │ - Wi-Fi AP (hostapd)                                          │
│     │ - Full System Reboot                                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ Admin taps [Restart] for CUPS service                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4   │ System shows confirmation:                                    │
│     │ "Restart Print Service? Active prints may be interrupted."    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5   │ Admin confirms                                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6   │ Frontend sends: POST /api/admin/service/cups/restart          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7   │ Backend executes: systemctl restart cups                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8   │ Backend waits for service to restart (max 30 seconds)         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 9   │ Backend verifies service is running                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 10  │ Return success response                                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 11  │ Frontend shows success: "Print Service restarted"             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 12  │ Service status updates to "Running"                           │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Alternative Flows

### AF-1: Restart Backend API

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 3a  │ Admin taps [Restart] for Backend API                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4a  │ Extra warning: "You will be disconnected temporarily"         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5a  │ Admin confirms                                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6a  │ Backend schedules self-restart (5 second delay)               │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7a  │ Return "restart scheduled" response                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8a  │ Frontend shows countdown: "Restarting in 5..."                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 9a  │ Connection lost                                               │
├─────┼────────────────────────────────────────────────────────────────┤
│ 10a │ Frontend polls for backend availability                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 11a │ Backend responds → "Reconnected successfully"                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 12a │ Note: Admin session (JWT) may still be valid                  │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-2: Restart Wi-Fi AP

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 3a  │ Admin taps [Restart] for Wi-Fi AP                             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4a  │ Critical warning:                                             │
│     │ "⚠️ All connected devices will be disconnected."              │
│     │ "You must reconnect to continue."                             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5a  │ Admin confirms                                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6a  │ Backend restarts hostapd service                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7a  │ Admin's device disconnects from Wi-Fi                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8a  │ Admin must manually reconnect to "photobooth" network         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 9a  │ After reconnecting, refresh dashboard                         │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Exception Flows

### EX-1: Service Fails to Restart

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ systemctl restart returns error                               │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Backend reads service logs for error details                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Return error with diagnostic info:                            │
│     │ - Exit code                                                   │
│     │ - Last 10 log lines                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Frontend shows error:                                         │
│     │ "Service failed to restart. Check logs for details."          │
├─────┼────────────────────────────────────────────────────────────────┤
│ E5  │ [View Logs] button available                                  │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-2: Service Restart Timeout

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Service doesn't respond within 30 seconds                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Backend returns timeout error                                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Frontend shows:                                               │
│     │ "Restart timed out. Service may still be starting."           │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ [Check Status] button to manually verify                      │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-3: Permission Denied

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Backend lacks permission to restart service                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ This indicates misconfiguration (should not happen)           │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Return 500 error with instruction to check sudo config        │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Log error for debugging                                       │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Postconditions

| ID | Condition |
|----|-----------|
| POST-1 | Target service restarted and running |
| POST-2 | Admin session maintained (if possible) |
| POST-3 | Service status updated on dashboard |

---

## Business Rules

| ID | Rule |
|----|------|
| RST-BR-1 | All restarts require confirmation |
| RST-BR-2 | Wi-Fi restart has extra warning |
| RST-BR-3 | Backend restart uses delayed self-restart |
| RST-BR-4 | Restart timeout: 30 seconds |
| RST-BR-5 | Restart commands logged for audit |

---

## Services and Commands

| Service | Display Name | Command | Warning Level |
|---------|--------------|---------|---------------|
| cups | Print Service | systemctl restart cups | Normal |
| photobooth-backend | Backend API | systemctl restart photobooth-backend | High |
| hostapd | Wi-Fi AP | systemctl restart hostapd | Critical |
| dnsmasq | DHCP Server | systemctl restart dnsmasq | Critical |

---

## UI/UX Requirements

### Service Management Page

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back               System Management                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─── Services ─────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  🖨️ Print Service (CUPS)                           │  │   │
│  │  │  Status: ✅ Running                                 │  │   │
│  │  │                               [Restart]            │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │                                                          │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  ⚙️ Backend API                                     │  │   │
│  │  │  Status: ✅ Running (uptime: 3d 14h)               │  │   │
│  │  │                               [Restart]            │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │                                                          │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  📶 Wi-Fi Access Point                              │  │   │
│  │  │  Status: ✅ Running (3 clients)                    │  │   │
│  │  │                               [Restart]  ⚠️        │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
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
│  │  │                         [Reboot System]  ⚠️      │    │   │
│  │  └──────────────────────────────────────────────────┘    │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Restart Confirmation Dialog

```
Normal Service:
┌─────────────────────────────────────────────────────────────────┐
│     ┌─────────────────────────────────────────────────────┐     │
│     │                                                     │     │
│     │         Restart Print Service?                      │     │
│     │                                                     │     │
│     │   Active print jobs may be interrupted.             │     │
│     │                                                     │     │
│     │   ┌──────────────┐     ┌──────────────────┐         │     │
│     │   │    Cancel    │     │     Restart      │         │     │
│     │   └──────────────┘     └──────────────────┘         │     │
│     │                                                     │     │
│     └─────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘

Critical Service (Wi-Fi):
┌─────────────────────────────────────────────────────────────────┐
│     ┌─────────────────────────────────────────────────────┐     │
│     │                                                     │     │
│     │    ⚠️ Restart Wi-Fi Access Point?                   │     │
│     │                                                     │     │
│     │   WARNING: All connected devices will be            │     │
│     │   disconnected, including this device.              │     │
│     │                                                     │     │
│     │   You must manually reconnect to the                │     │
│     │   "photobooth" network afterwards.                  │     │
│     │                                                     │     │
│     │   ┌──────────────┐     ┌──────────────────┐         │     │
│     │   │    Cancel    │     │     Restart      │         │     │
│     │   └──────────────┘     └──────────────────┘         │     │
│     │                             (destructive)           │     │
│     └─────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

### Restart In Progress

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│     ┌─────────────────────────────────────────────────────┐     │
│     │                                                     │     │
│     │              Restarting Print Service...            │     │
│     │                                                     │     │
│     │                   ◐ ◓ ◑ ◒                           │     │
│     │                                                     │     │
│     │              Please wait...                         │     │
│     │                                                     │     │
│     └─────────────────────────────────────────────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technical Notes

### API Endpoint

```typescript
// POST /api/admin/service/{service_name}/restart

interface RestartServiceRequest {
  // No body required
}

interface RestartServiceResponse {
  success: boolean;
  service: string;
  status: 'running' | 'stopped' | 'failed';
  message: string;
  restart_time_ms?: number;
}

// Supported services:
// - cups
// - photobooth-backend
// - hostapd
// - dnsmasq
```

### Backend Implementation

```python
# Service restart handler

import asyncio
import subprocess

class ServiceRestartUseCase:
    ALLOWED_SERVICES = {
        'cups': 'cups',
        'backend': 'photobooth-backend',
        'wifi': 'hostapd',
        'dhcp': 'dnsmasq',
    }

    RESTART_TIMEOUT = 30  # seconds

    async def execute(self, service_name: str) -> RestartServiceResponse:
        if service_name not in self.ALLOWED_SERVICES:
            raise ValueError(f"Unknown service: {service_name}")

        systemd_name = self.ALLOWED_SERVICES[service_name]

        # Special handling for self-restart
        if service_name == 'backend':
            return await self._restart_self()

        start_time = time.time()

        try:
            # Execute restart
            result = subprocess.run(
                ['sudo', 'systemctl', 'restart', systemd_name],
                capture_output=True,
                text=True,
                timeout=self.RESTART_TIMEOUT,
            )

            if result.returncode != 0:
                raise ServiceRestartError(
                    f"Restart failed: {result.stderr}"
                )

            # Wait for service to be active
            await self._wait_for_service(systemd_name)

            restart_time = int((time.time() - start_time) * 1000)

            logger.info(f"Service {systemd_name} restarted in {restart_time}ms")

            return RestartServiceResponse(
                success=True,
                service=service_name,
                status='running',
                message=f"{service_name} restarted successfully",
                restart_time_ms=restart_time,
            )

        except subprocess.TimeoutExpired:
            return RestartServiceResponse(
                success=False,
                service=service_name,
                status='unknown',
                message="Restart timed out",
            )

    async def _wait_for_service(self, systemd_name: str, timeout: int = 30):
        """Wait for service to report as active."""
        deadline = time.time() + timeout

        while time.time() < deadline:
            result = subprocess.run(
                ['systemctl', 'is-active', systemd_name],
                capture_output=True,
                text=True,
            )

            if result.stdout.strip() == 'active':
                return

            await asyncio.sleep(0.5)

        raise TimeoutError(f"Service {systemd_name} not active after {timeout}s")

    async def _restart_self(self) -> RestartServiceResponse:
        """Schedule backend self-restart."""
        # Schedule restart in background
        asyncio.create_task(self._delayed_restart())

        return RestartServiceResponse(
            success=True,
            service='backend',
            status='restarting',
            message="Backend restart scheduled in 5 seconds",
        )

    async def _delayed_restart(self):
        """Delayed self-restart to allow response to be sent."""
        await asyncio.sleep(5)

        # Use systemctl to restart ourselves
        subprocess.Popen(
            ['sudo', 'systemctl', 'restart', 'photobooth-backend'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
```

### Sudoers Configuration

```bash
# /etc/sudoers.d/photobooth
# Allow photobooth user to restart specific services without password

photobooth ALL=(ALL) NOPASSWD: /bin/systemctl restart cups
photobooth ALL=(ALL) NOPASSWD: /bin/systemctl restart photobooth-backend
photobooth ALL=(ALL) NOPASSWD: /bin/systemctl restart hostapd
photobooth ALL=(ALL) NOPASSWD: /bin/systemctl restart dnsmasq
photobooth ALL=(ALL) NOPASSWD: /sbin/reboot
```

---

## Related Use Cases

- **UC-101**: Admin Login (prerequisite)
- **UC-102**: View System Status (shows service health)
- **UC-109**: Reboot System (full system restart)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
