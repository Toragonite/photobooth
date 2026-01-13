# UC-104: Update Settings

## Summary

Admin updates system configuration settings through the dashboard. Settings include display options, print defaults, system behavior, and operational parameters.

---

## Actors

| Actor | Type | Description |
|-------|------|-------------|
| **Admin** | Primary | Operator configuring system |
| **System** | Secondary | Applies and persists settings |

---

## Preconditions

| ID | Condition |
|----|-----------|
| PRE-1 | Admin is authenticated |
| PRE-2 | Admin is on settings page |
| PRE-3 | Database is writable |

---

## Trigger

Admin navigates to Settings section and modifies a value.

---

## Main Flow

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Step                                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ Admin navigates to Settings on dashboard                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ Frontend requests: GET /api/admin/settings                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ Backend returns current settings                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4   │ Frontend displays settings form organized by category:        │
│     │ - Display Settings                                            │
│     │ - Print Settings                                              │
│     │ - System Settings                                             │
│     │ - Security Settings                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5   │ Admin modifies one or more settings                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6   │ Admin taps [Save] button                                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7   │ Frontend validates settings locally                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8   │ Frontend sends: PUT /api/admin/settings                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 9   │ Backend validates settings                                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 10  │ Backend persists settings to database                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 11  │ Backend applies changes that take effect immediately          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 12  │ Return success response                                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 13  │ Frontend shows success toast: "Settings saved"                │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Alternative Flows

### AF-1: Reset to Defaults

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 5a  │ Admin taps [Reset to Defaults]                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5b  │ Confirmation dialog: "Reset all settings to factory defaults?"│
├─────┼────────────────────────────────────────────────────────────────┤
│ 5c  │ Admin confirms                                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5d  │ Form resets to default values (not yet saved)                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5e  │ Admin must still tap [Save] to apply                          │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-2: Discard Changes

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 5a  │ Admin modifies settings but wants to cancel                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5b  │ Admin taps [Discard] or navigates away                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5c  │ If changes exist: Confirm "Discard unsaved changes?"          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5d  │ Changes are not saved                                         │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-3: Change Admin PIN

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 5a  │ Admin opens Security section                                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5b  │ Admin taps "Change PIN"                                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5c  │ Dialog requests:                                              │
│     │ - Current PIN                                                 │
│     │ - New PIN                                                     │
│     │ - Confirm new PIN                                             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5d  │ System validates current PIN matches                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5e  │ System validates new PIN meets requirements (4 digits)        │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5f  │ PIN updated, admin logged out for re-authentication           │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Exception Flows

### EX-1: Validation Error

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Backend validation fails (invalid value)                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Return 400 with validation errors                             │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Frontend highlights invalid fields                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Display error messages next to fields                         │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-2: Save Fails

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Database write fails                                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Return 500 error                                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Frontend shows error toast: "Failed to save. Please retry."   │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Settings in form preserved for retry                          │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Postconditions

| ID | Condition |
|----|-----------|
| POST-1 | Settings persisted to database |
| POST-2 | Applicable settings immediately active |
| POST-3 | Admin sees confirmation |

---

## Settings Catalog

### Display Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| default_language | enum | ko | Default UI language |
| countdown_default | number | 5 | Default countdown seconds |
| countdown_options | array | [3,5,8,10] | Available countdown options |
| show_logo | boolean | true | Show event logo on composite |
| date_format | string | YYYY.MM.DD | Date stamp format |
| timezone | string | Africa/Kigali | Timezone for timestamps |

### Print Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| max_copies | number | 3 | Maximum copies per print |
| default_copies | number | 1 | Default copy count |
| print_quality | enum | high | Quality setting |
| auto_retry_count | number | 3 | Auto-retry attempts |
| retry_delays | array | [3,5,8] | Delay between retries (sec) |

### System Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| storage_warning_percent | number | 80 | Storage warning threshold |
| storage_critical_percent | number | 95 | Storage critical threshold |
| log_level | enum | error | Logging level (debug/info/error) |
| cleanup_days | number | 30 | Days before old sessions cleaned |

### Security Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| admin_pin | string | 1998 | Admin access PIN |
| max_failed_attempts | number | 5 | Lockout after N failures |
| lockout_minutes | number | 5 | Lockout duration |
| token_expiry_minutes | number | 30 | JWT token lifetime |

---

## UI/UX Requirements

### Settings Page Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back                    Settings                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─── Display ──────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │  Default Language          ┌──────────────┐              │   │
│  │                            │ Korean    ▼  │              │   │
│  │                            └──────────────┘              │   │
│  │                                                          │   │
│  │  Default Countdown         ┌──────────────┐              │   │
│  │                            │ 5 seconds ▼  │              │   │
│  │                            └──────────────┘              │   │
│  │                                                          │   │
│  │  Show Logo on Print        ┌─────┐                       │   │
│  │                            │ ✓   │  Enabled              │   │
│  │                            └─────┘                       │   │
│  │                                                          │   │
│  │  Date Format               ┌──────────────┐              │   │
│  │                            │ YYYY.MM.DD ▼ │              │   │
│  │                            └──────────────┘              │   │
│  │                                                          │   │
│  │  Timezone                  ┌──────────────────┐          │   │
│  │                            │ Africa/Kigali ▼  │          │   │
│  │                            └──────────────────┘          │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─── Print ────────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │  Maximum Copies            ┌──────────────┐              │   │
│  │                            │ 3         ▼  │              │   │
│  │                            └──────────────┘              │   │
│  │                                                          │   │
│  │  Auto-Retry Attempts       ┌──────────────┐              │   │
│  │                            │ 3            │              │   │
│  │                            └──────────────┘              │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─── Security ─────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │  Admin PIN                 ┌──────────────────┐          │   │
│  │                            │ [Change PIN]     │          │   │
│  │                            └──────────────────┘          │   │
│  │                                                          │   │
│  │  Session Timeout           ┌──────────────┐              │   │
│  │                            │ 30 min    ▼  │              │   │
│  │                            └──────────────┘              │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────┐                      ┌──────────────────┐     │
│  │   Discard    │                      │       Save       │     │
│  └──────────────┘                      └──────────────────┘     │
│                                                                 │
│                   [Reset to Defaults]                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Change PIN Dialog

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│     ┌─────────────────────────────────────────────────────┐     │
│     │                                                     │     │
│     │              Change Admin PIN                       │     │
│     │                                                     │     │
│     │   Current PIN                                       │     │
│     │   ┌────┬────┬────┬────┐                             │     │
│     │   │ •  │ •  │ •  │ •  │                             │     │
│     │   └────┴────┴────┴────┘                             │     │
│     │                                                     │     │
│     │   New PIN                                           │     │
│     │   ┌────┬────┬────┬────┐                             │     │
│     │   │    │    │    │    │                             │     │
│     │   └────┴────┴────┴────┘                             │     │
│     │                                                     │     │
│     │   Confirm New PIN                                   │     │
│     │   ┌────┬────┬────┬────┐                             │     │
│     │   │    │    │    │    │                             │     │
│     │   └────┴────┴────┴────┘                             │     │
│     │                                                     │     │
│     │   ┌──────────────┐     ┌──────────────────┐         │     │
│     │   │    Cancel    │     │   Change PIN     │         │     │
│     │   └──────────────┘     └──────────────────┘         │     │
│     │                                                     │     │
│     └─────────────────────────────────────────────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technical Notes

### API Endpoints

```typescript
// GET /api/admin/settings
interface SettingsResponse {
  display: DisplaySettings;
  print: PrintSettings;
  system: SystemSettings;
  security: SecuritySettingsPublic; // PIN hash not exposed
}

// PUT /api/admin/settings
interface UpdateSettingsRequest {
  display?: Partial<DisplaySettings>;
  print?: Partial<PrintSettings>;
  system?: Partial<SystemSettings>;
  // security handled separately
}

// POST /api/admin/change-pin
interface ChangePinRequest {
  current_pin: string;
  new_pin: string;
}
```

### Settings Repository

```python
# Settings repository with SQLite

class SettingsRepository:
    DEFAULTS = {
        'default_language': 'ko',
        'countdown_default': 5,
        'countdown_options': '[3,5,8,10]',
        'show_logo': True,
        'date_format': 'YYYY.MM.DD',
        'timezone': 'Africa/Kigali',
        'max_copies': 3,
        'default_copies': 1,
        'print_quality': 'high',
        'auto_retry_count': 3,
        'retry_delays': '[3,5,8]',
        'storage_warning_percent': 80,
        'storage_critical_percent': 95,
        'log_level': 'error',
        'cleanup_days': 30,
        'admin_pin_hash': None,  # Set on first access
        'max_failed_attempts': 5,
        'lockout_minutes': 5,
        'token_expiry_minutes': 30,
    }

    async def get_all(self) -> dict:
        """Get all settings with defaults."""
        result = dict(self.DEFAULTS)

        rows = await self._db.fetchall("SELECT key, value FROM settings")
        for row in rows:
            key = row['key']
            if key in result:
                result[key] = self._deserialize(key, row['value'])

        return result

    async def update(self, settings: dict) -> None:
        """Update multiple settings."""
        for key, value in settings.items():
            if key not in self.DEFAULTS:
                raise ValueError(f"Unknown setting: {key}")

            serialized = self._serialize(key, value)

            await self._db.execute("""
                INSERT INTO settings (key, value, updated_at)
                VALUES (?, ?, datetime('now'))
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
            """, [key, serialized])

    def _serialize(self, key: str, value: Any) -> str:
        """Serialize value for storage."""
        if isinstance(value, (list, dict)):
            return json.dumps(value)
        if isinstance(value, bool):
            return '1' if value else '0'
        return str(value)

    def _deserialize(self, key: str, value: str) -> Any:
        """Deserialize value from storage."""
        default = self.DEFAULTS.get(key)

        if isinstance(default, bool):
            return value == '1'
        if isinstance(default, int):
            return int(value)
        if isinstance(default, list):
            return json.loads(value)

        return value
```

### Settings Validation

```python
# Settings validation

from pydantic import BaseModel, validator

class DisplaySettings(BaseModel):
    default_language: str
    countdown_default: int
    countdown_options: list[int]
    show_logo: bool
    date_format: str
    timezone: str

    @validator('default_language')
    def valid_language(cls, v):
        if v not in ('ko', 'en'):
            raise ValueError('Language must be ko or en')
        return v

    @validator('countdown_default')
    def valid_countdown(cls, v, values):
        if 'countdown_options' in values and v not in values['countdown_options']:
            raise ValueError('Default must be in options')
        return v

    @validator('countdown_options')
    def valid_options(cls, v):
        for opt in v:
            if opt < 1 or opt > 30:
                raise ValueError('Countdown must be 1-30 seconds')
        return v

class PrintSettings(BaseModel):
    max_copies: int
    default_copies: int
    print_quality: str
    auto_retry_count: int
    retry_delays: list[int]

    @validator('max_copies')
    def valid_max_copies(cls, v):
        if v < 1 or v > 10:
            raise ValueError('Max copies must be 1-10')
        return v

    @validator('auto_retry_count')
    def valid_retry_count(cls, v):
        if v < 0 or v > 10:
            raise ValueError('Retry count must be 0-10')
        return v
```

---

## Business Rules

| ID | Rule |
|----|------|
| SET-BR-1 | Settings changes require admin auth |
| SET-BR-2 | PIN change requires current PIN verification |
| SET-BR-3 | Some settings require service restart |
| SET-BR-4 | Invalid settings rejected with clear errors |
| SET-BR-5 | Settings persist across restarts |

---

## Related Use Cases

- **UC-101**: Admin Login (prerequisite)
- **UC-102**: View System Status (settings affect status)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
