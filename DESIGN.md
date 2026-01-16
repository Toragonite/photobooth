# PhotoBooth Final Design Specification v3

> Finalized design for on-premise, error-safe, resurrection-able photo booth system

---

## 1. System Overview

| Item | Specification |
|------|---------------|
| **Purpose** | 4-cut photo booth for missionary locations in Africa |
| **Environment** | On-premise, offline, battery-capable |
| **Hardware** | Raspberry Pi 5 (8GB RAM), 256GB SD Card |
| **Printer** | Canon Selphy CP1500 (USB) |
| **Client** | iPad Air (Safari) |
| **Languages** | Korean + English (dual language) |

---

## 2. Hardware Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   iPad Air                                 Raspberry Pi 5 (8GB)          │
│  ┌────────────────┐                       ┌──────────────────────────┐   │
│  │    Safari      │                       │     systemd services     │   │
│  │    (PWA)       │      Wi-Fi AP         │  ┌────────────────────┐  │   │
│  │                │◄─────────────────────►│  │ hostapd + dnsmasq  │  │   │
│  │  Camera API    │   SSID: photobooth    │  └────────────────────┘  │   │
│  │  Touch UI      │   PASS: photobooth-   │                          │   │
│  │                │         1998          │  ┌────────────────────┐  │   │
│  └────────────────┘   IP: 192.168.4.x     │  │     Docker         │  │   │
│                           ↓               │  │  ┌──────────────┐  │  │   │
│                       HTTPS:443           │  │  │    nginx     │  │  │   │
│                                           │  │  │   (SSL/TLS)  │  │  │   │
│  Admin Phone                              │  │  ├──────────────┤  │  │   │
│  ┌────────────────┐                       │  │  │   FastAPI    │  │  │   │
│  │ Browser        │◄──────────────────────│  │  │  + Uvicorn   │  │  │   │
│  │ /admin         │   Same Wi-Fi          │  │  ├──────────────┤  │  │   │
│  │ Dashboard      │   :443/admin          │  │  │    CUPS      │  │  │   │
│  └────────────────┘                       │  │  └──────┬───────┘  │  │   │
│                                           │  └─────────┼──────────┘  │   │
│                                           └────────────┼─────────────┘   │
│   Power: PD Battery (65W) ──► Pi 5                     │ USB             │
│   Power: NB-CP2LI ──────────► Selphy           ┌───────▼───────┐         │
│                                                │ Canon Selphy  │         │
│                                                │   CP1500      │         │
│                                                │   (4x6 inch)  │         │
│                                                └───────────────┘         │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Network Configuration

| Setting | Value |
|---------|-------|
| Wi-Fi Mode | Access Point (hostapd) |
| SSID | `photobooth` |
| Password | Set via `WIFI_PASSWORD` env var |
| Hidden | No (visible) |
| Pi IP | `192.168.4.1` |
| DHCP Range | `192.168.4.10 - 192.168.4.50` |
| mDNS | `photobooth.local` (for easy access) |

---

## 3. User Flow State Machine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                              [🏠 HOME BUTTON]                               │
│                    (visible on ALL screens except PRINTING)                 │
│                                                                             │
│  ┌──────────┐                                                               │
│  │   HOME   │◄─────────────────────────────────────────────────────────┐    │
│  │          │                                                          │    │
│  │ [Start]  │    ┌──────────┐    ┌──────────┐    ┌──────────────┐     │    │
│  │ [Lang]   │───►│  CAMERA  │───►│ PREVIEW  │───►│   PRINTING   │     │    │
│  │ [Admin]  │    │          │    │          │    │              │     │    │
│  └──────────┘    │ 4 photos │    │ Composite│    │ [Home hidden]│     │    │
│       ▲          │ capture  │    │ preview  │    │              │     │    │
│       │          │          │    │          │    │ Auto-retry   │     │    │
│       │          │ [Retake] │    │ [Retake] │    │ (3 times)    │     │    │
│       │          │ [Home]   │    │ [Print]  │    │              │     │    │
│       │          │          │    │ [Copies] │    └──────┬───────┘     │    │
│       │          └──────────┘    │ [Home]   │           │             │    │
│       │               │          └──────────┘           │             │    │
│       │               │               │                 ▼             │    │
│       │               │               │          ┌──────────────┐     │    │
│       │               │               │          │   COMPLETE   │     │    │
│       │               │               │          │   or ERROR   │─────┘    │
│       │               │               │          │              │          │
│       │               │               │          │ [New Session]│          │
│       │               │               │          │ [Home]       │          │
│       │               └───────────────┘          └──────────────┘          │
│       │                     ▲                           │                  │
│       │                     │                           │                  │
│       └─────────────────────┴───────────────────────────┘                  │
│                         (Home button / timeout)                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Navigation Rules

| Current Screen | Home Button | Back Action | Auto-timeout |
|----------------|-------------|-------------|--------------|
| HOME | N/A | N/A | Never |
| CAMERA | ✅ Visible | Goes to HOME | Never |
| PREVIEW | ✅ Visible | Goes to CAMERA | Never |
| PRINTING | ❌ Hidden | Blocked | Never |
| COMPLETE | ✅ Visible | Goes to HOME | Never |
| ERROR | ✅ Visible | Goes to HOME | Never |

---

## 4. Screen Specifications

### 4.1 HOME Screen

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                         PHOTOBOOTH                              │
│                      ─────────────────                          │
│                                                                 │
│                    [Optional Logo Here]                         │
│                                                                 │
│                                                                 │
│                  ┌─────────────────────┐                        │
│                  │                     │                        │
│                  │    📸 START / 시작   │                        │
│                  │                     │                        │
│                  └─────────────────────┘                        │
│                                                                 │
│                                                                 │
│          [🇰🇷 한국어]              [🇺🇸 English]                  │
│                                                                 │
│                                                                 │
│  ┌──────┐                                                       │
│  │ ⚙️   │  ← Admin (small, corner)                              │
│  └──────┘                                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 CAMERA Screen

```
┌─────────────────────────────────────────────────────────────────┐
│  [🏠]                     Photo 2 of 4                          │
│                                                                 │
│  ┌───────┬───────┬───────┬───────┐                              │
│  │  ✅   │  📷   │  ○    │  ○    │  ← Thumbnail strip           │
│  │ Photo1│ Photo2│ Photo3│ Photo4│    (tap to retake)           │
│  └───────┴───────┴───────┴───────┘                              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │                                                         │    │
│  │                   CAMERA PREVIEW                        │    │
│  │                   (mirrored/selfie)                     │    │
│  │                                                         │    │
│  │                        ┌───┐                            │    │
│  │                        │ 5 │  ← Countdown               │    │
│  │                        └───┘                            │    │
│  │                                                         │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│     Countdown: [3] [5] [8] [10] sec     [🔊 Sound: ON/OFF]      │
│                 ↑                                               │
│              (5 = default, highlighted)                         │
│                                                                 │
│                    [📸 CAPTURE / 촬영]                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Camera Behavior:**
- Preview is mirrored (selfie mode)
- Countdown: 3, 5 (default), 8, 10 seconds selectable
- Sound effect on capture (optional, toggle)
- Tap thumbnail to retake that specific photo
- Visual flash effect on capture
- After 4th photo, auto-navigate to PREVIEW

### 4.3 PREVIEW Screen

```
┌─────────────────────────────────────────────────────────────────┐
│  [🏠]                    Preview / 미리보기                       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  ┌─────────────┬─────────────┐                          │    │
│  │  │             │             │                          │    │
│  │  │   Photo 1   │   Photo 2   │                          │    │
│  │  │             │             │                          │    │
│  │  ├─────────────┼─────────────┤                          │    │
│  │  │             │             │                          │    │
│  │  │   Photo 3   │   Photo 4   │                          │    │
│  │  │             │             │                          │    │
│  │  └─────────────┴─────────────┘                          │    │
│  │                                                         │    │
│  │              2024.01.13  [Logo if enabled]              │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│                                                                 │
│     Copies / 매수:  [ - ]  2  [ + ]     (1 ~ 4)                 │
│                                                                 │
│     [ ] Add date stamp / 날짜 추가                               │
│     [ ] Add logo / 로고 추가                                     │
│                                                                 │
│                                                                 │
│  ┌────────────────┐                    ┌────────────────────┐   │
│  │  🔄 Retake     │                    │  🖨️ Print / 인쇄    │   │
│  │     다시 촬영   │                    │                    │   │
│  └────────────────┘                    └────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.4 PRINTING Screen

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                     Printing... / 인쇄 중...                     │
│                                                                 │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │                    [Composite Image]                    │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│                                                                 │
│                          🖨️ Printing...                         │
│                                                                 │
│         ████████████████████░░░░░░░░░░░░░░  65%                │
│                                                                 │
│                   Sending to printer...                         │
│                   프린터로 전송 중...                             │
│                                                                 │
│                                                                 │
│               ⚠️ Please wait / 잠시만 기다려주세요                 │
│               Do not close this page                            │
│               이 페이지를 닫지 마세요                              │
│                                                                 │
│                                                                 │
│                    [HOME BUTTON HIDDEN]                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.5 COMPLETE Screen

```
┌─────────────────────────────────────────────────────────────────┐
│  [🏠]                                                           │
│                                                                 │
│                                                                 │
│                           ✅                                    │
│                                                                 │
│                   Print Complete!                               │
│                   인쇄가 완료되었습니다!                          │
│                                                                 │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │                    [Composite Image]                    │    │
│  │                       (smaller)                         │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│               Please collect your photo!                        │
│               사진을 가져가세요!                                  │
│                                                                 │
│                                                                 │
│                                                                 │
│                  ┌─────────────────────┐                        │
│                  │  📸 New Session     │                        │
│                  │     새로 시작        │                        │
│                  └─────────────────────┘                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.6 ERROR Screen

```
┌─────────────────────────────────────────────────────────────────┐
│  [🏠]                                                           │
│                                                                 │
│                                                                 │
│                           ❌                                    │
│                                                                 │
│                    Print Failed                                 │
│                    인쇄에 실패했습니다                            │
│                                                                 │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │   Error: Printer not responding                         │    │
│  │   오류: 프린터가 응답하지 않습니다                         │    │
│  │                                                         │    │
│  │   Please check:                                         │    │
│  │   확인해 주세요:                                          │    │
│  │   • Printer is turned on / 프린터 전원                   │    │
│  │   • Paper is loaded / 용지 확인                          │    │
│  │   • USB cable connected / USB 연결                       │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│                                                                 │
│  ┌────────────────┐                    ┌────────────────────┐   │
│  │  🏠 Home       │                    │  🔄 Retry          │   │
│  │     처음으로    │                    │     다시 시도       │   │
│  └────────────────┘                    └────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Admin Dashboard

Accessible at `https://192.168.4.1/admin` or `https://photobooth.local/admin`

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                    🔧 PhotoBooth Admin                          │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  System Status                                                  │
│  ─────────────                                                  │
│  │ Service        │ Status    │ Action         │                │
│  ├────────────────┼───────────┼────────────────┤                │
│  │ nginx          │ ✅ Running │ [Restart]      │                │
│  │ FastAPI        │ ✅ Running │ [Restart]      │                │
│  │ CUPS           │ ✅ Running │ [Restart]      │                │
│  │ Printer        │ ✅ Ready   │ [Test Print]   │                │
│  └────────────────┴───────────┴────────────────┘                │
│                                                                 │
│  Storage                                                        │
│  ───────                                                        │
│  │ Used: 12.5 GB / 256 GB (4.9%)                │               │
│  │ Photos stored: 1,234                          │               │
│  │ [Download All Photos]  [Clear Old Photos]     │               │
│  └───────────────────────────────────────────────┘               │
│                                                                 │
│  Recent Print Jobs                                              │
│  ─────────────────                                              │
│  │ Job ID   │ Time       │ Status    │ Copies │                 │
│  ├──────────┼────────────┼───────────┼────────┤                 │
│  │ abc123   │ 14:32:05   │ ✅ Done   │ 2      │                 │
│  │ def456   │ 14:28:11   │ ✅ Done   │ 3      │                 │
│  │ ghi789   │ 14:25:03   │ ❌ Error  │ 2      │                 │
│  └──────────┴────────────┴───────────┴────────┘                 │
│                                                                 │
│  Quick Actions                                                  │
│  ─────────────                                                  │
│  [🔄 Restart All Services]                                      │
│  [📊 View Logs]                                                 │
│  [⬇️ Download Logs]                                              │
│  [🖨️ CUPS Web UI (Advanced)]                                    │
│  [🔌 Reboot Pi]                                                 │
│  [⏻ Shutdown Pi]                                                │
│                                                                 │
│  Settings                                                       │
│  ────────                                                       │
│  │ Default copies: [2]                           │               │
│  │ Default countdown: [5] sec                    │               │
│  │ Sound effects: [ON/OFF]                       │               │
│  │ Date stamp default: [ON/OFF]                  │               │
│  │ Logo default: [ON/OFF]                        │               │
│  │ Log level: [Errors Only ▼]                    │               │
│  │                             [Save Settings]   │               │
│  └───────────────────────────────────────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Admin Authentication

Simple PIN-based (no complex auth for on-premise):
- PIN: `1998` (configurable)
- Session timeout: 30 minutes
- Stored in browser localStorage

---

## 6. API Specification

### Base URL
```
https://192.168.4.1/api
https://photobooth.local/api
```

### Endpoints

#### 6.1 System Status
```
GET /api/status

Response:
{
  "online": true,
  "printer": {
    "name": "Canon_CP1500",
    "is_available": true,
    "status": "idle",           // idle | printing | error | offline
    "paper_status": "ok",       // ok | low | empty | unknown
    "error_message": null
  },
  "storage": {
    "used_bytes": 13421772800,
    "total_bytes": 256060514304,
    "photo_count": 1234
  },
  "uptime_seconds": 86400
}
```

#### 6.2 Create Print Job
```
POST /api/print

Request:
{
  "images": [
    "data:image/jpeg;base64,/9j/4AAQ...",  // Photo 1
    "data:image/jpeg;base64,/9j/4AAQ...",  // Photo 2
    "data:image/jpeg;base64,/9j/4AAQ...",  // Photo 3
    "data:image/jpeg;base64,/9j/4AAQ..."   // Photo 4
  ],
  "copies": 2,                              // 1-4
  "add_date": true,
  "add_logo": false
}

Response:
{
  "job_id": "abc12345",
  "status": "processing",
  "message": "Processing images...",
  "message_ko": "이미지 처리 중...",
  "created_at": "2024-01-13T14:32:05Z",
  "preview_image": "data:image/jpeg;base64,..."  // Composite preview
}
```

#### 6.3 Get Print Job Status
```
GET /api/print/{job_id}

Response:
{
  "job_id": "abc12345",
  "status": "printing",         // processing | sending | printing | completed | error
  "progress": 65,               // 0-100
  "message": "Printing...",
  "message_ko": "인쇄 중...",
  "retry_count": 0,             // 0-3
  "can_go_home": false,         // true when completed or final error
  "created_at": "2024-01-13T14:32:05Z",
  "completed_at": null,
  "error_code": null,           // printer_offline | paper_empty | etc.
  "error_message": null
}
```

#### 6.4 Cancel/Abort Print Job
```
POST /api/print/{job_id}/abort

Response:
{
  "job_id": "abc12345",
  "status": "aborted",
  "message": "Job aborted by user"
}
```

#### 6.5 Health Check
```
GET /health

Response:
{
  "status": "healthy",
  "timestamp": "2024-01-13T14:32:05Z",
  "services": {
    "database": "ok",
    "cups": "ok",
    "printer": "ok"
  }
}
```

### Admin Endpoints

#### 6.6 Admin Authentication
```
POST /api/admin/auth

Request:
{
  "pin": "1998"
}

Response:
{
  "success": true,
  "token": "eyJ...",           // JWT, 30min expiry
  "expires_at": "2024-01-13T15:02:05Z"
}
```

#### 6.7 Get All Jobs (Admin)
```
GET /api/admin/jobs?limit=50&offset=0

Headers:
  Authorization: Bearer eyJ...

Response:
{
  "jobs": [...],
  "total": 1234,
  "limit": 50,
  "offset": 0
}
```

#### 6.8 Get System Logs (Admin)
```
GET /api/admin/logs?level=error&limit=100

Response:
{
  "logs": [
    {
      "timestamp": "2024-01-13T14:32:05Z",
      "level": "error",
      "message": "CUPS connection failed",
      "details": {...}
    }
  ]
}
```

#### 6.9 Service Control (Admin)
```
POST /api/admin/services/{service}/restart

service: nginx | fastapi | cups | all

Response:
{
  "success": true,
  "message": "Service restarted"
}
```

#### 6.10 System Control (Admin)
```
POST /api/admin/system/reboot
POST /api/admin/system/shutdown

Response:
{
  "success": true,
  "message": "System will reboot in 5 seconds"
}
```

#### 6.11 Test Print (Admin)
```
POST /api/admin/printer/test

Response:
{
  "success": true,
  "job_id": "test_001",
  "message": "Test page sent to printer"
}
```

#### 6.12 Update Settings (Admin)
```
PUT /api/admin/settings

Request:
{
  "default_copies": 2,
  "default_countdown": 5,
  "sound_enabled": true,
  "date_stamp_default": true,
  "logo_default": false,
  "log_level": "error"        // debug | info | error
}

Response:
{
  "success": true,
  "settings": {...}
}
```

#### 6.13 Download Photos Archive (Admin)
```
GET /api/admin/photos/download?from=2024-01-01&to=2024-01-13

Response: ZIP file stream
```

---

## 7. Error Handling & Recovery

### Print Job Retry Logic

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Print Request                                                  │
│       │                                                         │
│       ▼                                                         │
│  ┌─────────┐                                                    │
│  │ Attempt │                                                    │
│  │   #1    │                                                    │
│  └────┬────┘                                                    │
│       │                                                         │
│       ├── Success ──────────────────────────► COMPLETED         │
│       │                                                         │
│       └── Failure                                               │
│            │                                                    │
│            ▼                                                    │
│       ┌─────────┐                                               │
│       │ Attempt │  (auto, 3 sec delay)                          │
│       │   #2    │                                               │
│       └────┬────┘                                               │
│            │                                                    │
│            ├── Success ─────────────────────► COMPLETED         │
│            │                                                    │
│            └── Failure                                          │
│                 │                                               │
│                 ▼                                               │
│            ┌─────────┐                                          │
│            │ Attempt │  (auto, 5 sec delay)                     │
│            │   #3    │                                          │
│            └────┬────┘                                          │
│                 │                                               │
│                 ├── Success ────────────────► COMPLETED         │
│                 │                                               │
│                 └── Failure                                     │
│                      │                                          │
│                      ▼                                          │
│               ┌─────────────┐                                   │
│               │ ASK USER    │                                   │
│               │             │                                   │
│               │ [Retry]     │── User clicks ──► Back to #1      │
│               │ [Abort]     │── User clicks ──► ERROR screen    │
│               │             │                   (session ends)  │
│               └─────────────┘                                   │
│                                                                 │
│  Note: If error is NOT printer-related (e.g., image processing  │
│        error), skip retries and show error immediately.         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Error Classification

| Error Type | Retryable | User Message |
|------------|-----------|--------------|
| `printer_offline` | Yes (3x) | Check printer power and USB |
| `printer_busy` | Yes (3x) | Printer is busy, retrying... |
| `paper_empty` | Yes (3x) | Please add paper |
| `ink_empty` | Yes (3x) | Please replace ink cartridge |
| `cups_connection` | Yes (3x) | Print service error, retrying... |
| `image_processing` | No | Image processing failed |
| `invalid_request` | No | Invalid request |
| `storage_full` | No | Storage full, contact admin |

---

## 8. Database Schema (SQLite)

```sql
-- /data/photobooth.db

-- Print jobs table
CREATE TABLE print_jobs (
    job_id TEXT PRIMARY KEY,
    cups_job_id INTEGER,
    status TEXT NOT NULL DEFAULT 'processing',
    -- status: processing | sending | printing | completed | error | aborted
    progress INTEGER DEFAULT 0,
    message TEXT,
    message_ko TEXT,
    error_code TEXT,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    copies INTEGER DEFAULT 2,
    add_date INTEGER DEFAULT 1,      -- boolean
    add_logo INTEGER DEFAULT 0,      -- boolean
    image_path TEXT,                 -- path to composite image
    original_images_path TEXT,       -- path to originals (JSON array)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    file_size_bytes INTEGER
);

-- System logs table
CREATE TABLE system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL,             -- debug | info | warning | error
    category TEXT,                   -- print | cups | system | api
    message TEXT NOT NULL,
    details TEXT,                    -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System settings table (key-value)
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Default settings
INSERT INTO settings (key, value) VALUES
    ('default_copies', '2'),
    ('default_countdown', '5'),
    ('sound_enabled', 'true'),
    ('date_stamp_default', 'true'),
    ('logo_default', 'false'),
    ('log_level', 'error'),
    ('admin_pin', '1998');

-- Indexes
CREATE INDEX idx_jobs_status ON print_jobs(status);
CREATE INDEX idx_jobs_created ON print_jobs(created_at);
CREATE INDEX idx_logs_level ON system_logs(level);
CREATE INDEX idx_logs_created ON system_logs(created_at);
```

---

## 9. File Storage Structure

```
/data/
├── photobooth.db                    # SQLite database
├── settings.json                    # Runtime settings cache
├── logo.png                         # Custom logo (optional)
│
├── output/                          # Composite images (permanent)
│   ├── 2024/
│   │   ├── 01/
│   │   │   ├── 13/
│   │   │   │   ├── abc12345.jpg    # Composite (compressed)
│   │   │   │   ├── abc12345_original.zip  # Original 4 photos
│   │   │   │   ├── def67890.jpg
│   │   │   │   └── def67890_original.zip
│   │   │   └── ...
│   │   └── ...
│   └── ...
│
├── temp/                            # Temporary processing (auto-cleanup)
│   └── ...
│
└── logs/                            # Application logs
    ├── app.log                      # Current log
    ├── app.log.1                    # Rotated
    └── ...
```

### Storage Policy (256GB SD)

| Category | Retention | Compression |
|----------|-----------|-------------|
| Composite images | Forever | JPEG quality 85% (post-print) |
| Original photos | Forever | ZIP archive |
| Temp files | Delete after 1 hour | N/A |
| Logs | 30 days, max 100MB | Rotated |

---

## 10. System Services (systemd)

### Boot Sequence

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Pi 5 Boot                                                      │
│      │                                                          │
│      ▼                                                          │
│  systemd                                                        │
│      │                                                          │
│      ├──► network-online.target                                 │
│      │                                                          │
│      ├──► hostapd.service (Wi-Fi AP)                           │
│      │         └── Creates "photobooth" network                 │
│      │                                                          │
│      ├──► dnsmasq.service (DHCP)                               │
│      │         └── Assigns IPs to connected devices             │
│      │                                                          │
│      └──► docker.service                                        │
│               │                                                 │
│               └──► photobooth.service (docker-compose)          │
│                        │                                        │
│                        ├── nginx (ready in ~5s)                 │
│                        ├── fastapi (ready in ~10s)              │
│                        └── cups (ready in ~5s)                  │
│                                                                 │
│  Total boot to ready: ~30-45 seconds                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Service Files

```ini
# /etc/systemd/system/photobooth.service

[Unit]
Description=PhotoBooth Docker Compose
Requires=docker.service
After=docker.service network-online.target hostapd.service dnsmasq.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/photobooth
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=120

[Install]
WantedBy=multi-user.target
```

### Watchdog (cron)

```bash
# /opt/photobooth/watchdog.sh
# Runs every 2 minutes via cron

#!/bin/bash

HEALTH_URL="http://127.0.0.1:8000/health"
MAX_FAILURES=3
FAILURE_FILE="/tmp/photobooth_failures"

# Check health endpoint
if ! curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
    # Increment failure counter
    FAILURES=$(cat "$FAILURE_FILE" 2>/dev/null || echo 0)
    FAILURES=$((FAILURES + 1))
    echo $FAILURES > "$FAILURE_FILE"

    if [ $FAILURES -ge $MAX_FAILURES ]; then
        # Restart services
        logger "PhotoBooth watchdog: Restarting services after $FAILURES failures"
        cd /opt/photobooth && docker compose restart
        echo 0 > "$FAILURE_FILE"
    fi
else
    # Reset counter on success
    echo 0 > "$FAILURE_FILE"
fi
```

---

## 11. Docker Configuration

### docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: photobooth-app
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./data:/data                    # Persistent storage
      - ./certs:/certs:ro               # SSL certificates
      - /var/run/cups:/var/run/cups     # CUPS socket
    environment:
      - TZ=Africa/Johannesburg          # Adjust timezone
      - LOG_LEVEL=error
      - DATABASE_PATH=/data/photobooth.db
    depends_on:
      cups:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  cups:
    image: olbat/cupsd:latest
    container_name: photobooth-cups
    restart: unless-stopped
    privileged: true
    ports:
      - "631:631"
    volumes:
      - /dev/bus/usb:/dev/bus/usb       # USB access for printer
      - cups_data:/etc/cups              # CUPS configuration
    environment:
      - CUPS_ADMIN_USER=admin
      - CUPS_ADMIN_PASSWORD=photobooth1998
    healthcheck:
      test: ["CMD", "lpstat", "-r"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  cups_data:
```

### Dockerfile

```dockerfile
# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci --production=false
COPY frontend/ ./
RUN npm run build

# Stage 2: Production Image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    openssl \
    curl \
    cups-client \
    libcups2-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/app ./app

# Copy frontend build
COPY --from=frontend-builder /build/dist /app/static

# Copy nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Copy startup script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Create data directories
RUN mkdir -p /data/output /data/temp /data/logs

EXPOSE 80 443

CMD ["/start.sh"]
```

---

## 12. Project File Structure (Final)

```
photobooth/
├── DESIGN.md                        # This document
├── docker-compose.yml
├── Dockerfile
├── nginx.conf
├── start.sh
├── .env.example
│
├── frontend/
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── i18n/
│       │   ├── index.ts
│       │   ├── ko.json
│       │   └── en.json
│       ├── types/
│       │   └── index.ts
│       ├── contexts/
│       │   ├── LanguageContext.tsx
│       │   └── SettingsContext.tsx
│       ├── pages/
│       │   ├── HomePage.tsx
│       │   ├── CameraPage.tsx
│       │   ├── PreviewPage.tsx
│       │   ├── PrintingPage.tsx
│       │   ├── CompletePage.tsx
│       │   ├── ErrorPage.tsx
│       │   └── admin/
│       │       ├── AdminLogin.tsx
│       │       └── AdminDashboard.tsx
│       ├── components/
│       │   ├── common/
│       │   │   ├── HomeButton.tsx
│       │   │   ├── LanguageToggle.tsx
│       │   │   └── LoadingSpinner.tsx
│       │   ├── camera/
│       │   │   ├── CameraPreview.tsx
│       │   │   ├── Countdown.tsx
│       │   │   ├── CountdownSelector.tsx
│       │   │   ├── ThumbnailStrip.tsx
│       │   │   └── CaptureButton.tsx
│       │   ├── preview/
│       │   │   ├── CompositePreview.tsx
│       │   │   ├── CopySelector.tsx
│       │   │   └── OptionsToggle.tsx
│       │   └── print/
│       │       ├── PrintProgress.tsx
│       │       └── PrintStatus.tsx
│       ├── hooks/
│       │   ├── useCamera.ts
│       │   ├── usePrintJob.ts
│       │   ├── useSound.ts
│       │   └── useSettings.ts
│       ├── services/
│       │   ├── api.ts
│       │   └── adminApi.ts
│       └── styles/
│           ├── global.css
│           ├── variables.css
│           └── components/
│               └── ...
│
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py
│   │   │   └── db_models.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── image_processor.py
│   │   │   ├── printer_service.py
│   │   │   ├── storage_service.py
│   │   │   └── job_manager.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── print_router.py
│   │   │   ├── status_router.py
│   │   │   └── admin_router.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── logger.py
│   │       └── retry.py
│   └── tests/
│       └── ...
│
├── setup/
│   ├── install.sh                   # Main installation script
│   ├── setup_wifi_ap.sh             # hostapd + dnsmasq setup
│   ├── setup_cups.sh                # CUPS + printer setup
│   └── setup_systemd.sh             # Service files setup
│
├── certs/                           # Generated on first run
│   ├── cert.pem
│   └── key.pem
│
└── data/                            # Persistent data (mounted volume)
    ├── photobooth.db
    ├── output/
    ├── temp/
    └── logs/
```

---

## 13. Implementation Checklist

### Phase 1: Core Infrastructure
- [ ] Docker setup (compose, Dockerfile)
- [ ] nginx configuration (SSL, proxy)
- [ ] FastAPI skeleton with health check
- [ ] SQLite database setup
- [ ] Basic logging

### Phase 2: Backend Services
- [ ] PrinterService (CUPS integration)
- [ ] ImageProcessor (4-cut layout)
- [ ] JobManager (state machine, retries)
- [ ] StorageService (file management)
- [ ] Print API endpoints

### Phase 3: Frontend Core
- [ ] React + Vite setup
- [ ] Routing configuration
- [ ] i18n (Korean + English)
- [ ] HomePage
- [ ] CameraPage + useCamera hook
- [ ] PreviewPage
- [ ] PrintingPage + status polling
- [ ] CompletePage
- [ ] ErrorPage

### Phase 4: Admin Dashboard
- [ ] Admin authentication
- [ ] Dashboard UI
- [ ] Service status display
- [ ] Job history
- [ ] Settings management
- [ ] Log viewer

### Phase 5: System Setup
- [ ] Wi-Fi AP setup script
- [ ] CUPS printer setup script
- [ ] systemd service files
- [ ] Watchdog script
- [ ] Installation script

### Phase 6: Testing & Polish
- [ ] End-to-end testing
- [ ] Error scenario testing
- [ ] Recovery testing (power loss simulation)
- [ ] Performance optimization
- [ ] Documentation

---

## 14. Open Questions / Confirmations Needed

| # | Question | Status |
|---|----------|--------|
| 1 | Logo file format and dimensions? | Need file |
| 2 | Timezone for deployment location? | Africa/? |
| 3 | Any specific branding colors? | Need info |
| 4 | Sound effect files needed? | Need files |
| 5 | Test with actual Canon Selphy? | Need hardware |

---

*Document Version: 3.0*
*Last Updated: 2024-01-13*
*Ready for Implementation: Yes (pending confirmations above)*
