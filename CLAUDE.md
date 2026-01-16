# PhotoBooth Project - Claude Code Context

> 4-cut photo booth application for missionary locations in Africa (Rwanda)
> Running on Raspberry Pi 5 (8GB RAM) with Canon Selphy CP1500 printer

---

## Project Overview

This is an **offline, on-premise** photo booth system designed for reliability in environments with:
- No internet connectivity
- Limited technical support
- High durability requirements ("resurrection-able")

### Key Features
- 4-cut photo capture (인생네컷 style)
- Automatic composite generation
- Thermal printing via CUPS
- Bilingual UI (Korean + English)
- Admin dashboard for phone-based management

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18+, TypeScript, Vite, Tailwind CSS |
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy |
| **Database** | SQLite (persistence across restarts) |
| **Printing** | CUPS, Canon Selphy CP1500 |
| **Networking** | hostapd (Wi-Fi AP), dnsmasq (DHCP) |
| **Container** | Docker, Docker Compose |
| **Hardware** | Raspberry Pi 5 (8GB), iPad Air (client) |

---

## Project Structure

```
photobooth/
├── backend/
│   └── app/
│       ├── domain/           # Entities, value objects
│       ├── application/      # Use cases, ports
│       ├── adapters/         # API routes
│       └── infrastructure/   # DB, services
├── frontend/
│   └── src/
│       ├── components/       # React components
│       ├── hooks/            # Custom hooks
│       ├── pages/            # Route pages
│       └── services/         # API clients
├── docs/                     # Documentation
│   ├── use-cases/            # 24 use case documents
│   ├── API_SPECIFICATION.md
│   ├── DATABASE_SCHEMA.md
│   └── ...
├── docker/                   # Docker configuration
├── scripts/                  # Deployment scripts
└── .claude/                  # Claude Code config
```

---

## Hardware Specifications

### Raspberry Pi 5
- **RAM**: 8GB
- **Storage**: 256GB microSD
- **OS**: Raspberry Pi OS (64-bit)
- **Network**: Wi-Fi AP mode (SSID: `photobooth`, Password: set via `WIFI_PASSWORD` env var)

### Camera
- iPad Air camera via browser (getUserMedia API)
- Resolution: 1920x1080 minimum
- Mirror mode for natural selfie experience

### Printer
- **Model**: Canon Selphy CP1500
- **Connection**: USB
- **Paper**: 4x6 inch (postcard size)
- **Quality**: Maximum (300 DPI)

---

## Critical Requirements

### Error Handling
- **Never silently fail** - All errors must be logged and shown to user
- **Auto-retry**: 3 attempts with delays (3s, 5s, 8s) for retryable errors
- **Graceful degradation**: Show meaningful error messages in both languages

### Persistence
- SQLite database survives restarts
- All sessions and print jobs persisted
- Photos stored compressed on disk

### Retryable Errors
```
PRINTER_OFFLINE, PRINTER_BUSY, PRINTER_PAPER_EMPTY,
PRINTER_INK_EMPTY, PRINTER_DOOR_OPEN,
CUPS_UNAVAILABLE, CUPS_REJECTED
```

### Non-Retryable Errors
```
PRINTER_PAPER_JAM (requires physical intervention)
STORAGE_FULL (requires admin cleanup)
```

---

## UI/UX Guidelines

### Color Palette (Rwanda Flag)
| Color | Hex | Usage |
|-------|-----|-------|
| Sky Blue | `#00A1DE` | Primary buttons, headers |
| Green | `#20603D` | Success states, accents |
| Yellow | `#FAD201` | Warnings, highlights |
| White | `#FFFFFF` | Backgrounds |
| Dark Gray | `#333333` | Text |

### Typography
- **Headings**: Inter Bold
- **Body**: Inter Regular
- **Korean**: Noto Sans KR

### Touch Targets
- Minimum: 44x44px (iOS standard)
- Recommended: 60x60px for primary actions
- Spacing: 16px minimum between targets

---

## API Quick Reference

### Session Flow
```
POST /api/session              → Create session
POST /api/session/{id}/photo   → Upload photo
POST /api/session/{id}/composite → Generate composite
POST /api/print                → Submit print job
GET  /api/print/{id}           → Get job status
POST /api/print/{id}/cancel    → Cancel job
```

### Admin Flow
```
POST /api/admin/login          → PIN authentication
GET  /api/admin/status         → System health
GET  /api/admin/print-history  → Job history
PUT  /api/admin/settings       → Update settings
POST /api/admin/system/reboot  → Reboot Pi
```

---

## Development Commands

```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend && npm install
npm run dev

# Docker (production)
docker compose up -d

# Tests
pytest backend/tests/
npm test --prefix frontend

# Linting
black backend/ && isort backend/
npm run lint --prefix frontend
```

---

## Deployment Checklist

1. [ ] Flash Raspberry Pi OS to SD card
2. [ ] Configure Wi-Fi AP (hostapd + dnsmasq)
3. [ ] Install Docker and Docker Compose
4. [ ] Configure CUPS and add printer
5. [ ] Deploy containers via `docker compose up -d`
6. [ ] Enable systemd services for auto-start
7. [ ] Test full flow: capture → preview → print
8. [ ] Verify admin dashboard access

---

## Available Skills

| Skill | Description |
|-------|-------------|
| `/hardware` | Camera, GPIO, printer diagnostics |
| `/print` | Print queue management, CUPS operations |
| `/deploy` | Deployment, systemd, Docker operations |
| `/test` | Run test suites |
| `/build` | Build and validation |

---

## Development Agents

| Agent | Phase | Description |
|-------|-------|-------------|
| `dev-planner` | Planning | Break down features into implementation tasks |
| `usecase-resolver` | Planning | Map use case docs to code implementation |
| `api-implementer` | Development | FastAPI backend following Clean Architecture |
| `frontend-implementer` | Development | React/TypeScript components |
| `code-reviewer` | Development | Code quality and security review |
| `code-quality-resolver` | Pre-PR | Lint, type check, test, coverage validation |
| `test-runner` | Development | Run and analyze test results |
| `hardware-debugger` | Development | Pi 5 hardware diagnostics |
| `maintenance-agent` | Post-impl | Code health, updates, documentation sync |

---

## Additional Commands

| Command | Description |
|---------|-------------|
| `/state` | Manage development state and progress |
| `/pre-pr` | Run pre-PR quality checks |
| `/usecase` | View use case documentation |
| `/docs` | Browse project documentation |

---

## State Management

Development progress is tracked in `.claude/state/`:
- `development.json` - Use case status, component progress, tech debt
- `context.json` - Session context, recent files

Use case status flow:
```
not_started → in_progress → implemented → tested → complete
```

---

## Git Workflow

- **Branch naming**: `feature/description`, `fix/description`
- **Commit prefixes**: `feat:`, `fix:`, `docs:`, `test:`, `chore:`
- **PR requirements**: Link to use case, test on staging

---

## Important Files

| File | Purpose |
|------|---------|
| `DESIGN.md` | Complete design specification |
| `docs/use-cases/INDEX.md` | All 24 use cases |
| `docs/API_SPECIFICATION.md` | REST API reference |
| `docs/DATABASE_SCHEMA.md` | SQLite schema |
| `docs/DEPLOYMENT.md` | Pi setup guide |
| `docs/ERROR_CODES.md` | Error code reference |

---

## Contacts & Resources

- **Original Spec**: `init.md` (Korean)
- **Architecture**: Clean Architecture (Ports & Adapters)
- **Target Users**: Missionaries, church events in Rwanda
