# PhotoBooth Implementation Plan

> Detailed breakdown with concerns and risk mitigation

---

## Design Updates (from discussion)

| Item | Decision |
|------|----------|
| Logo | Skip for now, SVG support later |
| Timezone | Configurable from Admin console (not hardcoded) |
| Colors | Rwanda flag color tone |
| Sound | Default beep, custom WAV support later |

### Rwanda Flag Color Palette

```
┌─────────────────────────────────────────┐
│  Sky Blue (top)     #00A1DE            │
│  ─────────────────────────────────────  │
│  Yellow (sun)       #FAD201            │
│  ─────────────────────────────────────  │
│  Green (bottom)     #20603D            │
└─────────────────────────────────────────┘

Application mapping:
- Primary:     #00A1DE (Sky Blue) - buttons, headers
- Secondary:   #20603D (Green) - success states, accents
- Accent:      #FAD201 (Yellow) - highlights, warnings
- Background:  #F5F9FC (Light blue tint)
- Text:        #1A1A1A (Near black)
- Error:       #DC3545 (Standard red)
```

---

## Implementation Phases Overview

```
Phase 0: Project Setup & Infrastructure       [~2 days effort]
    │
    ▼
Phase 1: Backend Core Services               [~3 days effort]
    │
    ▼
Phase 2: Frontend Foundation                 [~2 days effort]
    │
    ▼
Phase 3: Camera & Capture Flow               [~3 days effort]
    │
    ▼
Phase 4: Print Flow & Status                 [~2 days effort]
    │
    ▼
Phase 5: Admin Dashboard                     [~2 days effort]
    │
    ▼
Phase 6: System Integration (Pi Setup)       [~2 days effort]
    │
    ▼
Phase 7: Testing & Hardening                 [~2 days effort]
```

---

## Phase 0: Project Setup & Infrastructure

### 0.1 Tasks

| # | Task | Description | Output |
|---|------|-------------|--------|
| 0.1 | Initialize frontend project | Vite + React + TypeScript | `frontend/` scaffold |
| 0.2 | Initialize backend project | FastAPI + Python structure | `backend/` scaffold |
| 0.3 | Docker configuration | Dockerfile, docker-compose | Working containers |
| 0.4 | Nginx configuration | SSL, reverse proxy, SPA routing | `nginx.conf` |
| 0.5 | SSL certificate generation | Self-signed cert script | `certs/` |
| 0.6 | Environment configuration | .env files, config loading | Config system |

### 0.2 Concerns & Mitigations

| Concern | Risk | Mitigation |
|---------|------|------------|
| **SSL on local network** | Safari may reject self-signed certs | Use proper CN, add cert exception instructions |
| **Docker on Pi 5** | ARM64 compatibility | Use official ARM64 images, test early |
| **Volume permissions** | Container can't write to mounted volumes | Proper UID/GID mapping in Dockerfile |
| **Build time on Pi** | Multi-stage build slow on Pi | Build on dev machine, transfer image |
| **CUPS socket sharing** | Container isolation issues | Mount `/var/run/cups` correctly |

### 0.3 Verification Checklist

- [ ] `docker compose up` starts all services
- [ ] `https://localhost` shows nginx welcome or 502
- [ ] `https://localhost/health` returns JSON
- [ ] `https://localhost:631` shows CUPS web UI
- [ ] Containers restart after `docker compose restart`

---

## Phase 1: Backend Core Services

### 1.1 Tasks

| # | Task | Description | Output |
|---|------|-------------|--------|
| 1.1 | Database setup | SQLite with SQLAlchemy/raw | `database.py`, schema |
| 1.2 | Settings service | CRUD for app settings | `settings_service.py` |
| 1.3 | Logger setup | File + console logging | `logger.py` |
| 1.4 | CUPS integration | Connection, status, print | `printer_service.py` |
| 1.5 | Image processor | 4-cut layout composition | `image_processor.py` |
| 1.6 | Job manager | State machine, retry logic | `job_manager.py` |
| 1.7 | Storage service | File save, cleanup, compression | `storage_service.py` |
| 1.8 | API routes | Print, status endpoints | `routers/` |

### 1.2 Sub-task Breakdown

#### 1.4 CUPS Integration - Detailed

```python
# printer_service.py responsibilities:

class PrinterService:
    # Connection management
    - connect() -> bool
    - reconnect() -> bool  # With retry logic
    - is_connected() -> bool

    # Printer discovery
    - get_printers() -> List[PrinterInfo]
    - get_default_printer() -> Optional[str]
    - find_selphy_printer() -> Optional[str]  # Auto-detect Canon

    # Status
    - get_printer_status(name) -> PrinterStatus
    - get_paper_status(name) -> PaperStatus  # If supported
    - is_printer_ready(name) -> bool

    # Print operations
    - print_file(path, printer, options) -> cups_job_id
    - get_job_status(cups_job_id) -> JobStatus
    - cancel_job(cups_job_id) -> bool

    # Error mapping
    - map_cups_error(code) -> UserFriendlyError
```

#### 1.5 Image Processor - Detailed

```python
# image_processor.py responsibilities:

class ImageProcessor:
    # Core composition
    - create_composite(images: List[bytes], options: CompositeOptions) -> bytes

    # Layout (4-cut specific)
    - calculate_layout(canvas_size, photo_count, padding) -> List[Rect]
    - resize_and_crop(image, target_size) -> Image  # Maintain aspect ratio

    # Overlays
    - add_date_stamp(image, date, position, font_size) -> Image
    - add_logo(image, logo_path, position, size) -> Image

    # Output
    - save_jpeg(image, path, quality) -> Path
    - compress_for_storage(path, target_quality) -> Path
    - to_base64(image) -> str

    # Validation
    - validate_image(data: bytes) -> bool
    - get_image_dimensions(data: bytes) -> Tuple[int, int]
```

#### 1.6 Job Manager - State Machine

```
                         ┌─────────────────────────────────────────┐
                         │                                         │
    ┌──────────┐         │    ┌──────────┐        ┌──────────┐    │
    │ CREATED  │────────►│───►│PROCESSING│───────►│ SENDING  │    │
    └──────────┘         │    └──────────┘        └────┬─────┘    │
                         │          │                  │          │
                         │          │ error            │          │
                         │          ▼                  ▼          │
                         │    ┌──────────┐      ┌──────────┐      │
                         │    │  ERROR   │◄─────│ PRINTING │      │
                         │    │(retry<3) │      └────┬─────┘      │
                         │    └────┬─────┘           │            │
                         │         │                 │ success    │
                         │         │ retry           ▼            │
                         │         │           ┌──────────┐       │
                         │         └──────────►│COMPLETED │       │
                         │                     └──────────┘       │
                         │                                        │
                         │  On retry >= 3:                        │
                         │    ┌──────────────┐                    │
                         │    │ FAILED       │ (user decision)    │
                         │    │ (ask_retry)  │                    │
                         │    └──────────────┘                    │
                         │                                        │
                         │  On user abort:                        │
                         │    ┌──────────────┐                    │
                         │    │  ABORTED     │                    │
                         │    └──────────────┘                    │
                         │                                        │
                         └─────────────────────────────────────────┘

State transitions in code:
- CREATED → PROCESSING: When job accepted
- PROCESSING → SENDING: When image composition complete
- PROCESSING → ERROR: When composition fails (no retry)
- SENDING → PRINTING: When CUPS accepts job
- SENDING → ERROR: When CUPS rejects (retry)
- PRINTING → COMPLETED: When CUPS reports done
- PRINTING → ERROR: When CUPS reports error (retry)
- ERROR → PROCESSING: On auto-retry (if retry_count < 3)
- ERROR → FAILED: When retry_count >= 3
- FAILED → PROCESSING: On user manual retry
- FAILED → ABORTED: On user abort
- Any → ABORTED: On user cancel (if allowed)
```

### 1.3 Concerns & Mitigations

| Concern | Risk | Mitigation |
|---------|------|------------|
| **CUPS connection drops** | Print fails mid-job | Reconnection with retry, health check |
| **Large Base64 images** | Memory spike, slow transfer | Stream processing, size validation |
| **Concurrent print jobs** | Queue confusion | Single job lock, queue system |
| **SQLite concurrent writes** | Database locks | WAL mode, connection pooling |
| **Image processing memory** | OOM on Pi | Process one image at a time, cleanup |
| **CUPS job disappears** | Status unknown | Timeout + assume complete after X seconds |
| **Printer-specific options** | Canon may need special CUPS options | Test with actual hardware, configurable |

### 1.4 Verification Checklist

- [ ] Database creates tables on first run
- [ ] Settings can be read/written via API
- [ ] Logs write to file and rotate
- [ ] CUPS connection works in container
- [ ] Can list printers via API
- [ ] Image composition creates valid JPEG
- [ ] Job state transitions work correctly
- [ ] Retry logic triggers on simulated failure
- [ ] Files save to correct location
- [ ] Old files get compressed

---

## Phase 2: Frontend Foundation

### 2.1 Tasks

| # | Task | Description | Output |
|---|------|-------------|--------|
| 2.1 | Project structure | Folders, tsconfig, vite config | Scaffold |
| 2.2 | Routing setup | React Router with all routes | `App.tsx` |
| 2.3 | i18n setup | Korean + English translations | `i18n/` |
| 2.4 | Theme/styling | Rwanda colors, CSS variables | `styles/` |
| 2.5 | API client | Fetch wrapper, error handling | `services/api.ts` |
| 2.6 | Common components | HomeButton, LanguageToggle, Loading | `components/common/` |
| 2.7 | Context providers | Language, Settings | `contexts/` |
| 2.8 | Layout component | Shared page structure | `Layout.tsx` |

### 2.2 Detailed Component Tree

```
App
├── LanguageProvider
│   └── SettingsProvider
│       └── Router
│           ├── Layout (shared)
│           │   ├── HomeButton (conditional)
│           │   └── Page Content
│           │
│           ├── / → HomePage
│           ├── /camera → CameraPage
│           ├── /preview → PreviewPage
│           ├── /printing → PrintingPage
│           ├── /complete → CompletePage
│           ├── /error → ErrorPage
│           │
│           └── /admin/*
│               ├── /admin → AdminLogin
│               └── /admin/dashboard → AdminDashboard
```

### 2.3 CSS Architecture

```css
/* styles/variables.css */

:root {
  /* Rwanda Flag Colors */
  --color-primary: #00A1DE;       /* Sky Blue */
  --color-secondary: #20603D;     /* Green */
  --color-accent: #FAD201;        /* Yellow */

  /* Derived colors */
  --color-primary-light: #E6F4FB;
  --color-primary-dark: #0077A8;
  --color-secondary-light: #E8F5E9;
  --color-secondary-dark: #1A4D31;

  /* Neutrals */
  --color-background: #F5F9FC;
  --color-surface: #FFFFFF;
  --color-text: #1A1A1A;
  --color-text-muted: #6B7280;

  /* Semantic */
  --color-success: #20603D;       /* Use secondary */
  --color-warning: #FAD201;       /* Use accent */
  --color-error: #DC3545;
  --color-info: #00A1DE;          /* Use primary */

  /* Spacing */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  --spacing-2xl: 48px;

  /* Typography */
  --font-family: 'Inter', -apple-system, sans-serif;
  --font-size-sm: 14px;
  --font-size-md: 16px;
  --font-size-lg: 20px;
  --font-size-xl: 24px;
  --font-size-2xl: 32px;
  --font-size-3xl: 48px;

  /* Border radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 16px;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
  --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);

  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-normal: 300ms ease;
}
```

### 2.4 Concerns & Mitigations

| Concern | Risk | Mitigation |
|---------|------|------------|
| **Bundle size** | Slow load on Wi-Fi | Code splitting, lazy routes |
| **Font loading** | FOUT/FOIT | System fonts fallback, font-display: swap |
| **i18n bundle** | Extra KB | Lazy load translations |
| **Safari quirks** | iOS-specific CSS bugs | Test on actual iPad, use -webkit prefixes |
| **Touch targets** | Hard to tap on touch screen | Min 44x44px touch targets |
| **Offline access** | Page fails without network | Service worker for static assets |

### 2.5 Verification Checklist

- [ ] All routes render without error
- [ ] Language toggle switches UI language
- [ ] Rwanda colors applied correctly
- [ ] API client handles network errors
- [ ] HomeButton shows/hides based on route
- [ ] Loading states display properly
- [ ] Works on iPad Safari (if available)

---

## Phase 3: Camera & Capture Flow

### 3.1 Tasks

| # | Task | Description | Output |
|---|------|-------------|--------|
| 3.1 | useCamera hook | MediaDevices API wrapper | `hooks/useCamera.ts` |
| 3.2 | CameraPreview component | Live video feed | `CameraPreview.tsx` |
| 3.3 | Countdown component | Visual countdown timer | `Countdown.tsx` |
| 3.4 | CountdownSelector | 3/5/8/10 second options | `CountdownSelector.tsx` |
| 3.5 | ThumbnailStrip | 4 photo thumbnails | `ThumbnailStrip.tsx` |
| 3.6 | CaptureButton | Trigger with feedback | `CaptureButton.tsx` |
| 3.7 | CameraPage integration | Full capture flow | `CameraPage.tsx` |
| 3.8 | Sound effects | Beep on capture | `hooks/useSound.ts` |

### 3.2 useCamera Hook - Detailed

```typescript
// hooks/useCamera.ts

interface UseCameraOptions {
  facingMode?: 'user' | 'environment';  // 'user' for selfie
  resolution?: { width: number; height: number };
  mirrored?: boolean;
}

interface UseCameraReturn {
  // State
  isInitializing: boolean;
  isReady: boolean;
  error: CameraError | null;

  // Refs
  videoRef: RefObject<HTMLVideoElement>;
  canvasRef: RefObject<HTMLCanvasElement>;  // For capture

  // Actions
  start: () => Promise<void>;
  stop: () => void;
  capture: () => Promise<string>;  // Returns base64 JPEG

  // Stream info
  stream: MediaStream | null;
  capabilities: MediaTrackCapabilities | null;
}

// Error types
type CameraError =
  | { type: 'permission_denied'; message: string }
  | { type: 'not_found'; message: string }
  | { type: 'not_supported'; message: string }
  | { type: 'unknown'; message: string };
```

### 3.3 Camera Page State Machine

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   CameraPage States                                             │
│                                                                 │
│   ┌────────────┐                                                │
│   │INITIALIZING│ ── Camera starting                             │
│   └─────┬──────┘                                                │
│         │                                                       │
│         ├── Success ──► ┌──────────┐                            │
│         │               │  READY   │ ── Waiting for user        │
│         │               │ (idle)   │                            │
│         │               └────┬─────┘                            │
│         │                    │                                  │
│         │               User taps capture                       │
│         │                    │                                  │
│         │                    ▼                                  │
│         │               ┌──────────┐                            │
│         │               │COUNTDOWN │ ── 3/5/8/10 seconds        │
│         │               │ (ticking)│                            │
│         │               └────┬─────┘                            │
│         │                    │                                  │
│         │               Countdown ends                          │
│         │                    │                                  │
│         │                    ▼                                  │
│         │               ┌──────────┐                            │
│         │               │CAPTURING │ ── Flash effect, beep      │
│         │               │          │                            │
│         │               └────┬─────┘                            │
│         │                    │                                  │
│         │                    ├── photos.length < 4              │
│         │                    │       │                          │
│         │                    │       └──► Back to READY         │
│         │                    │                                  │
│         │                    └── photos.length === 4            │
│         │                            │                          │
│         │                            ▼                          │
│         │                    ┌──────────┐                       │
│         │                    │ COMPLETE │ ── Navigate to        │
│         │                    │          │    PreviewPage        │
│         │                    └──────────┘                       │
│         │                                                       │
│         └── Error ────► ┌──────────┐                            │
│                         │  ERROR   │ ── Show permission         │
│                         │          │    instructions            │
│                         └──────────┘                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.4 Concerns & Mitigations

| Concern | Risk | Mitigation |
|---------|------|------------|
| **Camera permission** | User denies, can't proceed | Clear instructions, "how to enable" guide |
| **HTTPS required** | getUserMedia needs secure context | Self-signed cert, user accepts warning |
| **iPad camera selection** | May default to wrong camera | Force `facingMode: 'user'` for front |
| **Mirror preview** | Confusing if not mirrored | CSS transform: scaleX(-1) on video |
| **Capture quality** | Too large Base64 | Resize canvas before toDataURL |
| **Memory leaks** | Stream not stopped | Cleanup in useEffect return |
| **Countdown UX** | User misses moment | Audio + visual countdown, large numbers |
| **Retake flow** | Complex state management | Clear state machine, store photos array |
| **Lighting conditions** | Bad photos in dark room | No flash on iPad, just accept it |

### 3.5 Capture Quality Settings

```typescript
// Recommended capture settings for balance of quality vs size

const CAPTURE_CONFIG = {
  // Canvas dimensions for capture (not preview)
  width: 1280,   // Sufficient for 4-cut at 300 DPI
  height: 960,   // 4:3 aspect ratio

  // JPEG export
  quality: 0.92,  // High quality, reasonable size
  mimeType: 'image/jpeg',

  // Estimated size per photo: ~200-400KB
  // 4 photos total: ~800KB - 1.6MB to send
};
```

### 3.6 Verification Checklist

- [ ] Camera initializes on page load
- [ ] Preview shows mirrored feed
- [ ] Countdown displays and counts down
- [ ] Countdown duration is selectable
- [ ] Capture triggers flash effect
- [ ] Sound plays on capture (if enabled)
- [ ] Thumbnail shows captured photo
- [ ] Can tap thumbnail to retake
- [ ] After 4 photos, navigates to Preview
- [ ] Camera stops when leaving page
- [ ] Error shows if permission denied

---

## Phase 4: Print Flow & Status

### 4.1 Tasks

| # | Task | Description | Output |
|---|------|-------------|--------|
| 4.1 | PreviewPage | Composite preview, options | `PreviewPage.tsx` |
| 4.2 | CompositePreview | 4-cut layout preview | `CompositePreview.tsx` |
| 4.3 | CopySelector | 1-4 copy selection | `CopySelector.tsx` |
| 4.4 | OptionsToggle | Date/logo toggles | `OptionsToggle.tsx` |
| 4.5 | usePrintJob hook | Submit and poll status | `hooks/usePrintJob.ts` |
| 4.6 | PrintingPage | Progress display | `PrintingPage.tsx` |
| 4.7 | PrintProgress | Progress bar component | `PrintProgress.tsx` |
| 4.8 | CompletePage | Success display | `CompletePage.tsx` |
| 4.9 | ErrorPage | Failure with retry | `ErrorPage.tsx` |

### 4.2 usePrintJob Hook - Detailed

```typescript
// hooks/usePrintJob.ts

interface UsePrintJobOptions {
  onStatusChange?: (status: PrintStatus) => void;
  onComplete?: () => void;
  onError?: (error: PrintError) => void;
  pollingInterval?: number;  // Default 1000ms
}

interface UsePrintJobReturn {
  // State
  job: PrintJob | null;
  status: PrintStatus;
  progress: number;
  error: PrintError | null;

  // Derived state
  isSubmitting: boolean;
  isPolling: boolean;
  canGoHome: boolean;
  needsUserRetry: boolean;  // After 3 auto-retries

  // Actions
  submit: (request: PrintRequest) => Promise<void>;
  retry: () => Promise<void>;
  abort: () => Promise<void>;
  reset: () => void;
}

// Polling logic
// - Start polling after submit success
// - Poll every 1 second
// - Stop when: completed | error (after 3 retries) | aborted
// - Auto-retry: On retryable error, wait 3s, retry (up to 3 times)
```

### 4.3 Print Flow Sequence

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  PreviewPage                                                    │
│      │                                                          │
│      │ User taps "Print"                                        │
│      │                                                          │
│      ▼                                                          │
│  ┌─────────────────┐                                            │
│  │ POST /api/print │ ◄─── Send 4 Base64 images + options        │
│  └────────┬────────┘                                            │
│           │                                                     │
│           │ Response: { job_id, preview_image }                 │
│           │                                                     │
│           ▼                                                     │
│  Navigate to PrintingPage                                       │
│      │                                                          │
│      │ Start polling                                            │
│      │                                                          │
│      ▼                                                          │
│  ┌─────────────────┐                                            │
│  │ GET /api/print/ │ ◄─── Every 1 second                        │
│  │    {job_id}     │                                            │
│  └────────┬────────┘                                            │
│           │                                                     │
│           │ Response: { status, progress, message }             │
│           │                                                     │
│           ├── status: processing/sending/printing               │
│           │       │                                             │
│           │       └── Update progress bar, continue polling     │
│           │                                                     │
│           ├── status: completed                                 │
│           │       │                                             │
│           │       └── Navigate to CompletePage                  │
│           │                                                     │
│           └── status: error                                     │
│                   │                                             │
│                   ├── retry_count < 3                           │
│                   │       │                                     │
│                   │       └── Show "Retrying...", backend       │
│                   │           handles retry, continue polling   │
│                   │                                             │
│                   └── retry_count >= 3 (needs_user_retry)       │
│                           │                                     │
│                           └── Navigate to ErrorPage             │
│                               User can [Retry] or [Abort]       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.4 Concerns & Mitigations

| Concern | Risk | Mitigation |
|---------|------|------------|
| **Large payload** | Slow upload, timeout | Compress on frontend, progress indicator |
| **Polling overhead** | Many requests | 1s interval is fine, stop when terminal |
| **User closes tab** | Job continues but no feedback | Job completes anyway, it's fine |
| **User refreshes** | Loses job_id | Store in sessionStorage, recover on mount |
| **Network drop** | Polling fails | Retry fetch, show "reconnecting..." |
| **Backend restart** | Job lost | SQLite persistence, recover in-progress jobs |
| **Stuck in printing** | Never completes | Timeout after 2 min, treat as error |
| **Print completes fast** | User misses it | Show success for at least 3 seconds |

### 4.5 Verification Checklist

- [ ] Preview shows 4-cut layout correctly
- [ ] Copy selector works (1-4)
- [ ] Date/logo toggles work
- [ ] Print submission shows loading
- [ ] Navigates to printing page
- [ ] Progress bar updates
- [ ] Status messages display (bilingual)
- [ ] Home button hidden during print
- [ ] Completes and shows success
- [ ] Error shows after 3 retries
- [ ] Retry button works
- [ ] Abort button works
- [ ] Refreshing page recovers state

---

## Phase 5: Admin Dashboard

### 5.1 Tasks

| # | Task | Description | Output |
|---|------|-------------|--------|
| 5.1 | AdminLogin page | PIN entry | `AdminLogin.tsx` |
| 5.2 | Auth context | Token management | `AuthContext.tsx` |
| 5.3 | Admin API client | Authenticated requests | `adminApi.ts` |
| 5.4 | Dashboard layout | Admin page structure | `AdminLayout.tsx` |
| 5.5 | SystemStatus widget | Service health display | `SystemStatus.tsx` |
| 5.6 | StorageWidget | Disk usage display | `StorageWidget.tsx` |
| 5.7 | JobHistory widget | Recent jobs table | `JobHistory.tsx` |
| 5.8 | SettingsPanel | Config form | `SettingsPanel.tsx` |
| 5.9 | LogViewer | Log display | `LogViewer.tsx` |
| 5.10 | QuickActions | Restart/reboot buttons | `QuickActions.tsx` |

### 5.2 Admin Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  /admin                                                         │
│      │                                                          │
│      ▼                                                          │
│  Check localStorage for token                                   │
│      │                                                          │
│      ├── No token ───────────► Show AdminLogin                  │
│      │                              │                           │
│      │                         Enter PIN                        │
│      │                              │                           │
│      │                              ▼                           │
│      │                    POST /api/admin/auth                  │
│      │                              │                           │
│      │                              ├── Success                 │
│      │                              │     │                     │
│      │                              │     └── Store token       │
│      │                              │         Navigate to       │
│      │                              │         /admin/dashboard  │
│      │                              │                           │
│      │                              └── Failure                 │
│      │                                    │                     │
│      │                                    └── Show error        │
│      │                                        "Invalid PIN"     │
│      │                                                          │
│      └── Has token ──────────► Validate token (check expiry)    │
│                                     │                           │
│                                     ├── Valid                   │
│                                     │     │                     │
│                                     │     └── Show Dashboard    │
│                                     │                           │
│                                     └── Expired                 │
│                                           │                     │
│                                           └── Clear token       │
│                                               Show AdminLogin   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 Concerns & Mitigations

| Concern | Risk | Mitigation |
|---------|------|------------|
| **PIN security** | Easy to guess | Rate limiting, lockout after 5 attempts |
| **Token in localStorage** | XSS vulnerability | Short expiry (30min), no sensitive data |
| **Service restart fails** | Admin stuck | Show error, suggest manual restart |
| **Accidental shutdown** | Pi goes offline | Confirmation dialog |
| **Large log files** | Slow to load | Pagination, limit display |
| **Admin on same Wi-Fi** | Users might access | PIN protection, not linked from main UI |

### 5.4 Verification Checklist

- [ ] PIN login works
- [ ] Invalid PIN shows error
- [ ] Token stored in localStorage
- [ ] Dashboard loads after login
- [ ] Service status displays correctly
- [ ] Storage info shows
- [ ] Job history loads
- [ ] Settings can be changed and saved
- [ ] Logs display with filtering
- [ ] Restart service works
- [ ] Test print works
- [ ] Reboot/shutdown work (with confirmation)
- [ ] Session timeout works (30 min)

---

## Phase 6: System Integration (Pi Setup)

### 6.1 Tasks

| # | Task | Description | Output |
|---|------|-------------|--------|
| 6.1 | Wi-Fi AP script | hostapd + dnsmasq setup | `setup_wifi_ap.sh` |
| 6.2 | CUPS setup script | Printer installation | `setup_cups.sh` |
| 6.3 | systemd service | Docker auto-start | `photobooth.service` |
| 6.4 | Watchdog script | Health monitoring | `watchdog.sh` |
| 6.5 | Install script | Main installer | `install.sh` |
| 6.6 | First-boot script | Initial setup | `first_boot.sh` |
| 6.7 | Update script | Pull and restart | `update.sh` |

### 6.2 Wi-Fi AP Configuration

```bash
# /etc/hostapd/hostapd.conf

interface=wlan0
driver=nl80211
ssid=photobooth
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=photobooth-1998
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP

# /etc/dnsmasq.conf

interface=wlan0
dhcp-range=192.168.4.10,192.168.4.50,255.255.255.0,24h
address=/photobooth.local/192.168.4.1
```

### 6.3 Concerns & Mitigations

| Concern | Risk | Mitigation |
|---------|------|------------|
| **Pi 5 Wi-Fi driver** | hostapd might not work | Test on actual Pi 5, fallback to USB dongle |
| **Wi-Fi interference** | Crowded 2.4GHz | Channel selection, test in deployment area |
| **mDNS resolution** | photobooth.local not resolving | Fallback to IP, dnsmasq provides it |
| **CUPS printer detection** | Selphy not auto-detected | Manual PPD configuration |
| **SD card corruption** | Power loss during write | Read-only root, data on separate partition |
| **Slow boot** | Docker images loading | Optimize image size, SSD if possible |
| **Remote debugging** | Can't SSH without network | Keep ethernet available, or serial console |

### 6.4 Verification Checklist

- [ ] Wi-Fi AP starts on boot
- [ ] iPad can connect to "photobooth"
- [ ] iPad gets IP via DHCP
- [ ] https://192.168.4.1 works from iPad
- [ ] photobooth.local resolves (if supported)
- [ ] Docker starts on boot
- [ ] All containers healthy after boot
- [ ] Printer detected by CUPS
- [ ] Test print works
- [ ] Watchdog restarts failed services
- [ ] System survives power cycle

---

## Phase 7: Testing & Hardening

### 7.1 Tasks

| # | Task | Description | Output |
|---|------|-------------|--------|
| 7.1 | Unit tests (backend) | Service layer tests | `tests/` |
| 7.2 | Integration tests | API endpoint tests | `tests/` |
| 7.3 | E2E test plan | Manual test scenarios | `TEST_PLAN.md` |
| 7.4 | Error scenario tests | Failure injection | Test results |
| 7.5 | Performance tests | Load, memory, timing | Test results |
| 7.6 | Recovery tests | Power loss, restart | Test results |
| 7.7 | Documentation | User guide, admin guide | `docs/` |

### 7.2 Critical Test Scenarios

```
┌─────────────────────────────────────────────────────────────────┐
│ MUST TEST SCENARIOS                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 1. Happy Path                                                   │
│    - Full flow: Home → Camera → Preview → Print → Complete      │
│    - Verify photo quality                                       │
│    - Verify print output                                        │
│                                                                 │
│ 2. Camera Errors                                                │
│    - Permission denied                                          │
│    - Camera not available                                       │
│    - Camera disconnects mid-capture                             │
│                                                                 │
│ 3. Print Errors                                                 │
│    - Printer offline at start                                   │
│    - Printer goes offline mid-print                             │
│    - Paper runs out                                             │
│    - CUPS service crashes                                       │
│                                                                 │
│ 4. Network Errors                                               │
│    - API timeout                                                │
│    - Backend crashes mid-request                                │
│    - Wi-Fi disconnects                                          │
│                                                                 │
│ 5. Recovery Tests                                               │
│    - Power loss during idle                                     │
│    - Power loss during print                                    │
│    - Service restart during print                               │
│    - Full system reboot                                         │
│                                                                 │
│ 6. Stress Tests                                                 │
│    - 10 consecutive prints                                      │
│    - Rapid page navigation                                      │
│    - Multiple browser tabs                                      │
│                                                                 │
│ 7. Edge Cases                                                   │
│    - Very dark photos                                           │
│    - Portrait vs landscape photos                               │
│    - Rapid retakes                                              │
│    - Cancel during countdown                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.3 Concerns & Mitigations

| Concern | Risk | Mitigation |
|---------|------|------------|
| **Can't test without hardware** | Bugs found in field | Mock services, test on actual Pi early |
| **Safari-specific bugs** | Works in Chrome, fails Safari | Test on actual iPad frequently |
| **Printer variations** | Different Selphy models behave differently | Test with exact model |
| **Field conditions** | Heat, dust, power fluctuations | Robust error handling, recovery |

---

## Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Phase 0 (Infrastructure)                                       │
│      │                                                          │
│      ├─────────────────┬─────────────────┐                      │
│      ▼                 ▼                 ▼                      │
│  Phase 1           Phase 2          Phase 6                     │
│  (Backend)         (Frontend         (Pi Setup)                 │
│      │             Foundation)           │                      │
│      │                 │                 │                      │
│      │                 ▼                 │                      │
│      │            Phase 3                │                      │
│      │            (Camera)               │                      │
│      │                 │                 │                      │
│      ▼                 ▼                 │                      │
│  ────────────► Phase 4 ◄─────────────────┘                      │
│               (Print Flow)                                      │
│                    │                                            │
│                    ▼                                            │
│               Phase 5                                           │
│               (Admin)                                           │
│                    │                                            │
│                    ▼                                            │
│               Phase 7                                           │
│               (Testing)                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Legend:
- Phase 1 & 2 can be done in parallel
- Phase 3 depends on Phase 2
- Phase 4 depends on Phase 1 (backend) and Phase 3 (camera)
- Phase 5 depends on Phase 4
- Phase 6 can be done in parallel with 1-5, but integration needs 4
- Phase 7 needs everything
```

---

## Questions Before Implementation

| # | Question | Why It Matters |
|---|----------|----------------|
| 1 | Do you have access to Pi 5 + Selphy for testing? | Critical for CUPS integration |
| 2 | iPad model and iOS version? | Safari API compatibility |
| 3 | Expected usage volume? | Affects storage cleanup policy |
| 4 | Deployment location timezone? | Log timestamps, date stamp |
| 5 | Any specific font preferences? | i18n, Korean rendering |
| 6 | Network: Any other devices on AP? | DHCP range planning |
| 7 | Backup/restore requirements? | Data export features |
| 8 | Multiple booths? | Naming, identification |

---

## Next Steps

1. **Review this plan** - Any missing concerns?
2. **Answer open questions** - Helps refine implementation
3. **Prioritize phases** - Which to tackle first?
4. **Start Phase 0** - Infrastructure is foundation for all

---

*Document Version: 1.0*
*Created: 2024-01-13*
