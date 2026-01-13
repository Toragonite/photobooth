# UC-001: Start Photo Session

## Summary

User initiates a new photo booth session from the home screen, which creates a new session and navigates to the camera capture interface.

---

## Actors

| Actor | Type | Description |
|-------|------|-------------|
| **User** | Primary | Person using the photo booth |
| **System** | Secondary | Backend system that manages sessions |

---

## Preconditions

| ID | Condition |
|----|-----------|
| PRE-1 | System is operational (all services healthy) |
| PRE-2 | User is on the Home page |
| PRE-3 | No active session exists for this client (or previous session is abandoned) |

---

## Trigger

User taps the "Start" / "시작" button on the Home page.

---

## Main Flow

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Step                                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ User taps "Start" button on Home page                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ Frontend generates a unique session ID (UUID)                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ Frontend initializes session state:                            │
│     │ - session_id: generated UUID                                   │
│     │ - photos: [] (empty array, max 4)                              │
│     │ - current_index: 0                                             │
│     │ - created_at: current timestamp                                │
│     │ - settings: { countdown, sound_enabled }                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4   │ Frontend stores session in SessionContext                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5   │ Frontend navigates to Camera page (/camera)                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6   │ Camera page initializes camera hardware (see UC-002)           │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Alternative Flows

### AF-1: Resume Abandoned Session

```
Trigger: User had a previous session with photos but didn't complete

┌─────┬────────────────────────────────────────────────────────────────┐
│ 1a  │ System detects existing session in localStorage               │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1b  │ System checks session age (< 10 minutes old)                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1c  │ System shows modal: "Resume previous session?"                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1d  │ User chooses "Resume" → Navigate to Camera with existing      │
│     │ photos restored                                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1e  │ User chooses "Start New" → Clear old session, continue main   │
│     │ flow from step 2                                              │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-2: Language Not Set

```
Trigger: First-time user, no language preference stored

┌─────┬────────────────────────────────────────────────────────────────┐
│ 1a  │ System detects no language preference                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1b  │ Home page prominently displays language selection             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1c  │ User must select language before Start button is enabled      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1d  │ After selection, continue main flow                           │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Exception Flows

### EX-1: System Unhealthy

```
Trigger: Backend health check fails

┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Home page displays "System Unavailable" message               │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Start button is disabled                                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ System retries health check every 5 seconds                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ When healthy, enable Start button automatically               │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-2: Printer Offline

```
Trigger: Printer status is offline

┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Home page displays warning: "Printer offline"                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Start button remains ENABLED (user can still capture photos)  │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Warning icon shown next to Start button                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ User proceeds; printer error handled at print time            │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Postconditions

| ID | Condition |
|----|-----------|
| POST-1 | New session exists with unique ID |
| POST-2 | Session has empty photos array |
| POST-3 | User is on Camera page |
| POST-4 | Camera initialization has started |

---

## Business Rules

| ID | Rule |
|----|------|
| BR-1 | Session ID must be unique (UUID v4) |
| BR-2 | Old sessions (> 10 min) are not resumable |
| BR-3 | Only one active session per browser tab |
| BR-4 | Session is stored in memory + sessionStorage for recovery |

---

## Data Requirements

### Session Object

```typescript
interface PhotoSession {
  session_id: string;          // UUID v4
  photos: CapturedPhoto[];     // Max 4 items
  current_index: number;       // 0-3
  created_at: string;          // ISO timestamp
  settings: {
    countdown_seconds: number; // 3, 5, 8, or 10
    sound_enabled: boolean;
  };
  language: 'ko' | 'en';
}

interface CapturedPhoto {
  index: number;               // 0-3
  data_url: string;            // base64 JPEG
  captured_at: string;         // ISO timestamp
}
```

---

## UI/UX Requirements

### Home Page Layout

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                         PHOTOBOOTH                              │
│                                                                 │
│                    [Optional Logo Area]                         │
│                                                                 │
│                                                                 │
│                  ┌─────────────────────┐                        │
│                  │                     │                        │
│                  │   📸 START / 시작   │  ← Large touch target  │
│                  │                     │    (min 88x88px)       │
│                  └─────────────────────┘                        │
│                                                                 │
│                                                                 │
│          [🇰🇷 한국어]              [🇺🇸 English]                  │
│                                                                 │
│                                                                 │
│  ┌──────┐                                    [Printer Status]  │
│  │ ⚙️   │                                    🟢 Ready          │
│  └──────┘                                                       │
│   Admin                                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Interaction Notes

- Start button: Primary color (#00A1DE), large text
- Language buttons: Equal size, one highlighted based on current selection
- Admin button: Small, corner position, subtle
- Printer status: Small indicator, bottom right
- Touch feedback: Button scales down slightly on press

---

## Technical Notes

### Frontend Implementation

```typescript
// pages/HomePage.tsx

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { createSession } = useSession();
  const { isHealthy, printerStatus } = useSystemStatus();

  const handleStart = () => {
    const session = createSession();
    navigate('/camera', { state: { session_id: session.session_id } });
  };

  return (
    <div className="home-page">
      <h1>{t('app.title')}</h1>

      <Button
        onClick={handleStart}
        disabled={!isHealthy}
        size="large"
        variant="primary"
      >
        {t('home.start')}
      </Button>

      <LanguageToggle />

      <PrinterStatusIndicator status={printerStatus} />

      <AdminButton />
    </div>
  );
};
```

### Session Storage Strategy

```typescript
// On session create
sessionStorage.setItem('photobooth_session', JSON.stringify(session));

// On page load (recovery)
const stored = sessionStorage.getItem('photobooth_session');
if (stored) {
  const session = JSON.parse(stored);
  const age = Date.now() - new Date(session.created_at).getTime();
  if (age < 10 * 60 * 1000) { // 10 minutes
    // Offer to resume
  }
}
```

---

## Open Questions

| # | Question | Status |
|---|----------|--------|
| 1 | Should we show a loading animation while camera initializes? | **Decision: Yes, brief spinner** |
| 2 | What happens if user opens multiple tabs? | **Decision: Only one session per tab, independent** |
| 3 | Should session ID be displayed anywhere for debugging? | **Decision: Only in admin mode** |

---

## Related Use Cases

- **UC-002**: Capture Photo (next step)
- **UC-009**: Change Language (can be done on this page)
- **UC-102**: View System Status (admin checks health)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
