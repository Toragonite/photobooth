# PhotoBooth - Remaining Tasks

## Backend Architecture Completion

The application layer (ports, DTOs, use cases) has been created following Clean Architecture principles. The following tasks remain to complete the architecture refactor:

### 1. Repository Implementations
Create SQLAlchemy adapters that implement the repository ports.

**Files to create:**
- `backend/app/infrastructure/repositories/sqlalchemy_session_repository.py`
- `backend/app/infrastructure/repositories/sqlalchemy_print_job_repository.py`

**Tasks:**
- [ ] Implement `SessionRepository` interface with SQLAlchemy
- [ ] Implement `PrintJobRepository` interface with SQLAlchemy
- [ ] Add entity-to-model and model-to-entity mapping functions
- [ ] Handle async database operations

### 2. Dependency Injection Container
Set up DI to wire use cases with their dependencies.

**Files to create:**
- `backend/app/infrastructure/container.py` - DI container definition
- `backend/app/infrastructure/dependencies.py` - FastAPI dependency providers

**Tasks:**
- [ ] Create container class with all service registrations
- [ ] Create FastAPI `Depends()` functions for each use case
- [ ] Configure singleton vs request-scoped services

### 3. Update Infrastructure Services
Make existing services implement the port interfaces.

**Files to modify:**
- `backend/app/infrastructure/services/printer_service.py` → implement `PrinterPort`
- `backend/app/infrastructure/services/storage_service.py` → implement `StoragePort`
- `backend/app/infrastructure/services/image_processor.py` → implement `ImageProcessorPort`
- `backend/app/infrastructure/services/system_service.py` → implement `SystemServicePort`

**Tasks:**
- [ ] Add port interface inheritance to each service class
- [ ] Ensure method signatures match port definitions
- [ ] Add any missing methods required by ports

### 4. Controller Refactoring
Update API routes to use use cases instead of direct service calls.

**Files to modify:**
- `backend/app/adapters/api/session.py`
- `backend/app/adapters/api/print_jobs.py`
- `backend/app/adapters/api/admin.py`
- `backend/app/adapters/api/health.py`

**Tasks:**
- [ ] Inject use cases via FastAPI dependencies
- [ ] Replace direct service calls with use case execution
- [ ] Map use case results to HTTP responses
- [ ] Handle use case errors appropriately

---

## Created Files Reference

### Ports (Interfaces)
| File | Interface |
|------|-----------|
| `application/ports/repositories/session_repository.py` | `SessionRepository` |
| `application/ports/repositories/print_job_repository.py` | `PrintJobRepository` |
| `application/ports/services/printer_port.py` | `PrinterPort` |
| `application/ports/services/storage_port.py` | `StoragePort` |
| `application/ports/services/image_processor_port.py` | `ImageProcessorPort` |
| `application/ports/services/system_service_port.py` | `SystemServicePort` |

### DTOs
| File | DTOs |
|------|------|
| `application/dto/session_dto.py` | `PhotoDTO`, `SessionDTO`, `CreateSessionRequest/Response` |
| `application/dto/print_job_dto.py` | `PrintJobDTO`, `CreatePrintJobRequest`, `PrintJobStatusResponse` |
| `application/dto/admin_dto.py` | `LoginRequest/Response`, `SystemStatusDTO`, `PrintHistoryDTO`, `LogsDTO` |

### Use Cases
| Domain | Use Cases |
|--------|-----------|
| Session | `CreateSession`, `GetSession`, `CapturePhoto`, `GenerateComposite`, `AbandonSession` |
| Print | `SubmitPrintJob`, `GetPrintStatus`, `RetryPrintJob`, `CancelPrintJob` |
| Admin | `Authenticate`, `GetSystemStatus`, `GetPrintHistory`, `GetLogs`, `TestPrint`, `RebootSystem` |
| System | `CleanupStorage`, `HealthCheck` |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Adapters Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ session.py  │  │print_jobs.py│  │  admin.py   │  (API)   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │
└─────────┼────────────────┼────────────────┼─────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ Use Cases   │  │    DTOs     │  │   Ports     │          │
│  │ (Session,   │  │ (Request/   │  │ (Repository │          │
│  │  Print,     │  │  Response)  │  │  & Service  │          │
│  │  Admin)     │  │             │  │  Interfaces)│          │
│  └──────┬──────┘  └─────────────┘  └──────┬──────┘          │
└─────────┼─────────────────────────────────┼─────────────────┘
          │                                 │
          ▼                                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ Repositories│  │  Services   │  │  Database   │          │
│  │ (SQLAlchemy)│  │ (Printer,   │  │  (SQLite)   │          │
│  │  [TODO]     │  │  Storage)   │  │             │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                      Domain Layer                            │
│  ┌─────────────┐  ┌─────────────┐                           │
│  │  Entities   │  │   Value     │                           │
│  │ (Session,   │  │   Objects   │                           │
│  │  PrintJob)  │  │ (IDs, Enums)│                           │
│  └─────────────┘  └─────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Priority Order

1. **Repository Implementations** - Required to persist data via use cases
2. **DI Container** - Required to wire everything together
3. **Service Port Implementation** - Low risk, just adding inheritance
4. **Controller Refactoring** - Final step, can be done incrementally
