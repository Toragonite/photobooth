# PhotoBooth Clean Architecture

> Architectural blueprint following Uncle Bob's Clean Architecture principles

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                         CLEAN ARCHITECTURE LAYERS                           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │                    FRAMEWORKS & DRIVERS                             │   │
│  │                    (Outermost Layer)                                │   │
│  │                                                                     │   │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │   │  React   │  │  FastAPI │  │  SQLite  │  │   CUPS   │          │   │
│  │   │   Web    │  │  HTTP    │  │    DB    │  │ Printer  │          │   │
│  │   └──────────┘  └──────────┘  └──────────┘  └──────────┘          │   │
│  │                                                                     │   │
│  │   ┌─────────────────────────────────────────────────────────┐     │   │
│  │   │                                                         │     │   │
│  │   │                 INTERFACE ADAPTERS                      │     │   │
│  │   │                                                         │     │   │
│  │   │   ┌────────────┐  ┌────────────┐  ┌────────────┐       │     │   │
│  │   │   │Controllers │  │ Presenters │  │  Gateways  │       │     │   │
│  │   │   │  (API)     │  │  (DTOs)    │  │  (Repos)   │       │     │   │
│  │   │   └────────────┘  └────────────┘  └────────────┘       │     │   │
│  │   │                                                         │     │   │
│  │   │   ┌─────────────────────────────────────────────┐     │     │   │
│  │   │   │                                             │     │     │   │
│  │   │   │              USE CASES                      │     │     │   │
│  │   │   │         (Application Logic)                 │     │     │   │
│  │   │   │                                             │     │     │   │
│  │   │   │   ┌─────────────────────────────────┐     │     │     │   │
│  │   │   │   │                                 │     │     │     │   │
│  │   │   │   │           ENTITIES              │     │     │     │   │
│  │   │   │   │      (Business Objects)         │     │     │     │   │
│  │   │   │   │                                 │     │     │     │   │
│  │   │   │   └─────────────────────────────────┘     │     │     │   │
│  │   │   │                                             │     │     │   │
│  │   │   └─────────────────────────────────────────────┘     │     │   │
│  │   │                                                         │     │   │
│  │   └─────────────────────────────────────────────────────────┘     │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

DEPENDENCY RULE: Dependencies point INWARD only
- Entities know nothing about Use Cases
- Use Cases know nothing about Controllers
- Controllers know nothing about Frameworks
```

---

## 2. Layer Definitions

### 2.1 Entities (Core Domain)

**Location:** `backend/app/domain/entities/`

Entities encapsulate enterprise-wide business rules. They are the most stable code and change least often.

| Entity | Description |
|--------|-------------|
| `Photo` | A captured image with metadata |
| `PhotoSession` | Collection of 4 photos for one booth session |
| `CompositeImage` | Generated 4-cut layout image |
| `PrintJob` | A print request with lifecycle state |
| `PrinterStatus` | Current state of physical printer |
| `Settings` | Application configuration |
| `User` | Admin user (simplified) |

### 2.2 Use Cases (Application Business Rules)

**Location:** `backend/app/application/use_cases/`

Use cases contain application-specific business rules. They orchestrate data flow to and from entities.

| Use Case | Actor | Description |
|----------|-------|-------------|
| `CapturePhoto` | User | Receive and validate a captured photo |
| `CreatePhotoSession` | User | Start a new 4-photo session |
| `CompletePhotoSession` | User | Finalize session with 4 photos |
| `GenerateComposite` | System | Create 4-cut layout from session |
| `SubmitPrintJob` | User | Request printing of composite |
| `GetPrintJobStatus` | User | Query current print job state |
| `RetryPrintJob` | User | Retry failed print job |
| `AbortPrintJob` | User | Cancel print job |
| `GetSystemStatus` | Admin | Check system health |
| `UpdateSettings` | Admin | Modify application settings |
| `GetPrintHistory` | Admin | List past print jobs |
| `RestartService` | Admin | Restart a system service |

### 2.3 Interface Adapters

**Location:** `backend/app/adapters/`

Convert data between use cases and external agencies.

| Adapter Type | Components |
|--------------|------------|
| **Controllers** | HTTP route handlers (FastAPI routers) |
| **Presenters** | Response formatters (DTOs, serializers) |
| **Gateways** | Repository interfaces, external service ports |

### 2.4 Frameworks & Drivers

**Location:** `backend/app/infrastructure/`

External tools and frameworks.

| Framework | Purpose |
|-----------|---------|
| FastAPI | HTTP server |
| SQLite/SQLAlchemy | Persistence |
| Pillow (PIL) | Image processing |
| pycups | Printer communication |
| React | Frontend UI |

---

## 3. Directory Structure (Backend)

```
backend/
├── app/
│   │
│   ├── domain/                      # ENTITIES LAYER
│   │   ├── __init__.py
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   ├── photo.py             # Photo entity
│   │   │   ├── photo_session.py     # PhotoSession entity
│   │   │   ├── composite_image.py   # CompositeImage entity
│   │   │   ├── print_job.py         # PrintJob entity
│   │   │   └── settings.py          # Settings entity
│   │   ├── value_objects/
│   │   │   ├── __init__.py
│   │   │   ├── job_id.py            # JobId value object
│   │   │   ├── session_id.py        # SessionId value object
│   │   │   ├── print_status.py      # PrintStatus enum
│   │   │   └── image_dimensions.py  # ImageDimensions value object
│   │   ├── events/
│   │   │   ├── __init__.py
│   │   │   ├── print_job_events.py  # Domain events
│   │   │   └── session_events.py
│   │   └── exceptions/
│   │       ├── __init__.py
│   │       └── domain_exceptions.py # Domain-specific errors
│   │
│   ├── application/                 # USE CASES LAYER
│   │   ├── __init__.py
│   │   ├── use_cases/
│   │   │   ├── __init__.py
│   │   │   ├── photo/
│   │   │   │   ├── capture_photo.py
│   │   │   │   └── create_session.py
│   │   │   ├── print/
│   │   │   │   ├── submit_print_job.py
│   │   │   │   ├── get_print_status.py
│   │   │   │   ├── retry_print_job.py
│   │   │   │   └── abort_print_job.py
│   │   │   ├── composite/
│   │   │   │   └── generate_composite.py
│   │   │   ├── admin/
│   │   │   │   ├── get_system_status.py
│   │   │   │   ├── update_settings.py
│   │   │   │   ├── get_print_history.py
│   │   │   │   └── restart_service.py
│   │   │   └── auth/
│   │   │       └── authenticate_admin.py
│   │   ├── ports/                   # Interface definitions
│   │   │   ├── __init__.py
│   │   │   ├── repositories/
│   │   │   │   ├── print_job_repository.py
│   │   │   │   ├── session_repository.py
│   │   │   │   └── settings_repository.py
│   │   │   └── services/
│   │   │       ├── printer_service.py
│   │   │       ├── image_processor.py
│   │   │       ├── storage_service.py
│   │   │       └── system_service.py
│   │   ├── dto/                     # Data Transfer Objects
│   │   │   ├── __init__.py
│   │   │   ├── print_job_dto.py
│   │   │   ├── session_dto.py
│   │   │   └── settings_dto.py
│   │   └── exceptions/
│   │       └── application_exceptions.py
│   │
│   ├── adapters/                    # INTERFACE ADAPTERS LAYER
│   │   ├── __init__.py
│   │   ├── api/                     # Controllers (FastAPI)
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── print_routes.py
│   │   │   │   ├── status_routes.py
│   │   │   │   ├── session_routes.py
│   │   │   │   └── admin_routes.py
│   │   │   ├── middleware/
│   │   │   │   ├── error_handler.py
│   │   │   │   └── auth_middleware.py
│   │   │   └── schemas/             # Pydantic request/response
│   │   │       ├── print_schemas.py
│   │   │       ├── session_schemas.py
│   │   │       └── admin_schemas.py
│   │   └── presenters/
│   │       ├── __init__.py
│   │       ├── print_job_presenter.py
│   │       └── error_presenter.py
│   │
│   ├── infrastructure/              # FRAMEWORKS & DRIVERS
│   │   ├── __init__.py
│   │   ├── persistence/
│   │   │   ├── __init__.py
│   │   │   ├── database.py          # SQLite connection
│   │   │   ├── models/              # SQLAlchemy models
│   │   │   │   ├── print_job_model.py
│   │   │   │   ├── session_model.py
│   │   │   │   └── settings_model.py
│   │   │   └── repositories/        # Repository implementations
│   │   │       ├── sqlite_print_job_repo.py
│   │   │       ├── sqlite_session_repo.py
│   │   │       └── sqlite_settings_repo.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── cups_printer_service.py
│   │   │   ├── pillow_image_processor.py
│   │   │   ├── file_storage_service.py
│   │   │   └── linux_system_service.py
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   └── settings.py          # Environment config
│   │   └── logging/
│   │       ├── __init__.py
│   │       └── logger.py
│   │
│   └── main.py                      # Application entry point
│
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   ├── application/
│   │   └── adapters/
│   ├── integration/
│   └── e2e/
│
└── requirements.txt
```

---

## 4. Directory Structure (Frontend)

```
frontend/
├── src/
│   │
│   ├── domain/                      # ENTITIES LAYER
│   │   ├── entities/
│   │   │   ├── Photo.ts
│   │   │   ├── PhotoSession.ts
│   │   │   ├── PrintJob.ts
│   │   │   └── Settings.ts
│   │   ├── value-objects/
│   │   │   ├── PrintStatus.ts
│   │   │   └── Language.ts
│   │   └── errors/
│   │       └── DomainErrors.ts
│   │
│   ├── application/                 # USE CASES LAYER
│   │   ├── use-cases/
│   │   │   ├── CapturePhotoUseCase.ts
│   │   │   ├── SubmitPrintJobUseCase.ts
│   │   │   └── GetPrintStatusUseCase.ts
│   │   ├── ports/
│   │   │   ├── ApiService.ts        # Interface
│   │   │   ├── CameraService.ts     # Interface
│   │   │   └── SoundService.ts      # Interface
│   │   └── dto/
│   │       ├── PrintJobDTO.ts
│   │       └── SessionDTO.ts
│   │
│   ├── adapters/                    # INTERFACE ADAPTERS
│   │   ├── api/
│   │   │   ├── HttpApiService.ts    # Implements ApiService
│   │   │   └── ApiClient.ts
│   │   ├── camera/
│   │   │   └── BrowserCameraService.ts
│   │   ├── sound/
│   │   │   └── WebAudioSoundService.ts
│   │   └── storage/
│   │       └── LocalStorageAdapter.ts
│   │
│   ├── presentation/                # UI LAYER
│   │   ├── pages/
│   │   │   ├── HomePage.tsx
│   │   │   ├── CameraPage.tsx
│   │   │   ├── PreviewPage.tsx
│   │   │   ├── PrintingPage.tsx
│   │   │   ├── CompletePage.tsx
│   │   │   ├── ErrorPage.tsx
│   │   │   └── admin/
│   │   │       ├── AdminLoginPage.tsx
│   │   │       └── AdminDashboardPage.tsx
│   │   ├── components/
│   │   │   ├── common/
│   │   │   ├── camera/
│   │   │   ├── preview/
│   │   │   ├── print/
│   │   │   └── admin/
│   │   ├── hooks/
│   │   │   ├── useCamera.ts
│   │   │   ├── usePrintJob.ts
│   │   │   ├── useSettings.ts
│   │   │   └── useSound.ts
│   │   ├── contexts/
│   │   │   ├── LanguageContext.tsx
│   │   │   ├── SettingsContext.tsx
│   │   │   └── SessionContext.tsx
│   │   └── styles/
│   │       ├── variables.css
│   │       └── global.css
│   │
│   ├── infrastructure/              # FRAMEWORK CONFIG
│   │   ├── i18n/
│   │   │   ├── index.ts
│   │   │   ├── ko.json
│   │   │   └── en.json
│   │   └── config/
│   │       └── constants.ts
│   │
│   ├── App.tsx
│   └── main.tsx
│
└── package.json
```

---

## 5. Dependency Injection

### Backend (Python)

```python
# app/main.py - Composition Root

from app.infrastructure.persistence.database import Database
from app.infrastructure.persistence.repositories import (
    SqlitePrintJobRepository,
    SqliteSessionRepository,
    SqliteSettingsRepository,
)
from app.infrastructure.services import (
    CupsPrinterService,
    PillowImageProcessor,
    FileStorageService,
    LinuxSystemService,
)
from app.application.use_cases.print import (
    SubmitPrintJobUseCase,
    GetPrintStatusUseCase,
)

def create_app() -> FastAPI:
    # Infrastructure
    database = Database(path="/data/photobooth.db")

    # Repositories
    print_job_repo = SqlitePrintJobRepository(database)
    session_repo = SqliteSessionRepository(database)
    settings_repo = SqliteSettingsRepository(database)

    # Services
    printer_service = CupsPrinterService()
    image_processor = PillowImageProcessor()
    storage_service = FileStorageService(base_path="/data/output")
    system_service = LinuxSystemService()

    # Use Cases
    submit_print_job = SubmitPrintJobUseCase(
        print_job_repo=print_job_repo,
        session_repo=session_repo,
        image_processor=image_processor,
        printer_service=printer_service,
        storage_service=storage_service,
    )

    get_print_status = GetPrintStatusUseCase(
        print_job_repo=print_job_repo,
        printer_service=printer_service,
    )

    # Wire up routes
    app = FastAPI()
    app.include_router(
        create_print_router(submit_print_job, get_print_status)
    )

    return app
```

### Frontend (TypeScript)

```typescript
// src/infrastructure/di/container.ts

import { HttpApiService } from '@/adapters/api/HttpApiService';
import { BrowserCameraService } from '@/adapters/camera/BrowserCameraService';
import { WebAudioSoundService } from '@/adapters/sound/WebAudioSoundService';
import { SubmitPrintJobUseCase } from '@/application/use-cases/SubmitPrintJobUseCase';

// Create service instances
const apiService = new HttpApiService(API_BASE_URL);
const cameraService = new BrowserCameraService();
const soundService = new WebAudioSoundService();

// Create use cases
export const submitPrintJobUseCase = new SubmitPrintJobUseCase(apiService);
export const capturePhotoUseCase = new CapturePhotoUseCase(cameraService);

// Export for React context
export const services = {
  api: apiService,
  camera: cameraService,
  sound: soundService,
};
```

---

## 6. Data Flow Examples

### 6.1 Submit Print Job Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  USER ACTION: Tap "Print" button                                            │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ PRESENTATION LAYER (React)                                          │   │
│  │                                                                     │   │
│  │   PreviewPage.tsx                                                   │   │
│  │       │                                                             │   │
│  │       │ onClick={() => submitPrintJob(photos, options)}             │   │
│  │       ▼                                                             │   │
│  │   usePrintJob.ts (hook)                                            │   │
│  │       │                                                             │   │
│  │       │ Validates input, transforms to DTO                         │   │
│  │       ▼                                                             │   │
│  └───────┼─────────────────────────────────────────────────────────────┘   │
│          │                                                                  │
│  ┌───────┼─────────────────────────────────────────────────────────────┐   │
│  │ APPLICATION LAYER (Use Case)                                        │   │
│  │       │                                                             │   │
│  │       ▼                                                             │   │
│  │   SubmitPrintJobUseCase.execute(request)                           │   │
│  │       │                                                             │   │
│  │       │ Calls ApiService.submitPrintJob()                          │   │
│  │       ▼                                                             │   │
│  └───────┼─────────────────────────────────────────────────────────────┘   │
│          │                                                                  │
│  ┌───────┼─────────────────────────────────────────────────────────────┐   │
│  │ ADAPTER LAYER (HTTP)                                                │   │
│  │       │                                                             │   │
│  │       ▼                                                             │   │
│  │   HttpApiService.submitPrintJob()                                  │   │
│  │       │                                                             │   │
│  │       │ POST /api/print { images, copies, options }                │   │
│  │       │                                                             │   │
│  └───────┼─────────────────────────────────────────────────────────────┘   │
│          │                                                                  │
│          │ ═══════════════ NETWORK ═══════════════                         │
│          │                                                                  │
│  ┌───────┼─────────────────────────────────────────────────────────────┐   │
│  │ BACKEND: ADAPTER LAYER (FastAPI)                                    │   │
│  │       │                                                             │   │
│  │       ▼                                                             │   │
│  │   print_routes.py                                                   │   │
│  │       │                                                             │   │
│  │       │ Validates request schema (Pydantic)                        │   │
│  │       │ Creates PrintRequest DTO                                    │   │
│  │       ▼                                                             │   │
│  └───────┼─────────────────────────────────────────────────────────────┘   │
│          │                                                                  │
│  ┌───────┼─────────────────────────────────────────────────────────────┐   │
│  │ BACKEND: APPLICATION LAYER (Use Case)                               │   │
│  │       │                                                             │   │
│  │       ▼                                                             │   │
│  │   SubmitPrintJobUseCase.execute(request)                           │   │
│  │       │                                                             │   │
│  │       ├── 1. Validate session exists                               │   │
│  │       ├── 2. Create PrintJob entity                                │   │
│  │       ├── 3. Generate composite image                              │   │
│  │       ├── 4. Save to storage                                       │   │
│  │       ├── 5. Submit to printer                                     │   │
│  │       ├── 6. Persist job to repository                             │   │
│  │       └── 7. Return PrintJobDTO                                    │   │
│  │       │                                                             │   │
│  └───────┼─────────────────────────────────────────────────────────────┘   │
│          │                                                                  │
│  ┌───────┼─────────────────────────────────────────────────────────────┐   │
│  │ BACKEND: DOMAIN LAYER (Entities)                                    │   │
│  │       │                                                             │   │
│  │       ▼                                                             │   │
│  │   PrintJob.create(session_id, copies, options)                     │   │
│  │       │                                                             │   │
│  │       │ - Generates JobId                                          │   │
│  │       │ - Sets initial status: PROCESSING                          │   │
│  │       │ - Validates business rules                                 │   │
│  │       │                                                             │   │
│  └───────┼─────────────────────────────────────────────────────────────┘   │
│          │                                                                  │
│  ┌───────┼─────────────────────────────────────────────────────────────┐   │
│  │ BACKEND: INFRASTRUCTURE LAYER                                       │   │
│  │       │                                                             │   │
│  │       ├── ImageProcessor.create_composite(photos)                  │   │
│  │       ├── StorageService.save(composite)                           │   │
│  │       ├── PrinterService.print(file_path)                          │   │
│  │       └── PrintJobRepository.save(print_job)                       │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Interface Contracts

### 7.1 Repository Interfaces

```python
# app/application/ports/repositories/print_job_repository.py

from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities.print_job import PrintJob
from app.domain.value_objects.job_id import JobId

class PrintJobRepository(ABC):
    """Port for PrintJob persistence"""

    @abstractmethod
    def save(self, job: PrintJob) -> None:
        """Persist a print job"""
        pass

    @abstractmethod
    def find_by_id(self, job_id: JobId) -> Optional[PrintJob]:
        """Find job by ID, returns None if not found"""
        pass

    @abstractmethod
    def find_active(self) -> List[PrintJob]:
        """Find all jobs not in terminal state"""
        pass

    @abstractmethod
    def find_by_status(self, status: PrintStatus) -> List[PrintJob]:
        """Find jobs by status"""
        pass

    @abstractmethod
    def find_recent(self, limit: int = 50) -> List[PrintJob]:
        """Find most recent jobs"""
        pass

    @abstractmethod
    def update(self, job: PrintJob) -> None:
        """Update existing job"""
        pass
```

### 7.2 Service Interfaces

```python
# app/application/ports/services/printer_service.py

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

@dataclass
class PrinterInfo:
    name: str
    is_available: bool
    status: str
    paper_status: Optional[str]
    error_message: Optional[str]

@dataclass
class PrintResult:
    success: bool
    cups_job_id: Optional[int]
    error_code: Optional[str]
    error_message: Optional[str]

class PrinterService(ABC):
    """Port for printer operations"""

    @abstractmethod
    def get_status(self) -> PrinterInfo:
        """Get current printer status"""
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """Check if printer is ready to print"""
        pass

    @abstractmethod
    def print_file(
        self,
        file_path: Path,
        copies: int = 1,
        options: dict = None
    ) -> PrintResult:
        """Send file to printer"""
        pass

    @abstractmethod
    def get_job_status(self, cups_job_id: int) -> str:
        """Get CUPS job status"""
        pass

    @abstractmethod
    def cancel_job(self, cups_job_id: int) -> bool:
        """Cancel a CUPS job"""
        pass
```

---

## 8. Testing Strategy by Layer

| Layer | Test Type | What to Test | Mocking Strategy |
|-------|-----------|--------------|------------------|
| **Entities** | Unit | Business rules, validation | No mocks needed |
| **Value Objects** | Unit | Immutability, equality | No mocks needed |
| **Use Cases** | Unit | Orchestration logic | Mock all ports |
| **Adapters** | Integration | Data transformation | Mock infrastructure |
| **Infrastructure** | Integration | External system integration | Real systems or containers |
| **E2E** | System | Full user flows | Real system |

---

## 9. Cross-Cutting Concerns

### 9.1 Error Handling

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  DOMAIN LAYER EXCEPTIONS                                        │
│  └── InvalidPhotoError                                          │
│  └── SessionNotFoundError                                       │
│  └── JobAlreadyCompletedError                                  │
│                                                                 │
│  APPLICATION LAYER EXCEPTIONS                                   │
│  └── PrinterNotReadyError                                      │
│  └── StorageFullError                                          │
│  └── AuthenticationError                                       │
│                                                                 │
│  ADAPTER LAYER HANDLING                                        │
│  └── Maps domain/app exceptions to HTTP status codes           │
│  └── Formats user-friendly error messages                      │
│  └── Logs technical details                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 Logging

- **Domain Layer:** No logging (pure business logic)
- **Use Case Layer:** Log business events (job created, job completed)
- **Adapter Layer:** Log request/response summaries
- **Infrastructure Layer:** Log technical details (CUPS commands, SQL queries)

### 9.3 Configuration

All configuration flows inward:
- Infrastructure reads from environment/files
- Provides configuration to use cases via dependency injection
- Domain entities are configuration-agnostic

---

*Next: See individual use case documents in `docs/use-cases/`*
