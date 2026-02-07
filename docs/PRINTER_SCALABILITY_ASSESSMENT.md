# Printer Scalability Assessment

> Assessment of multi-printer support for PhotoBooth system
> Date: 2026-02-07

---

## Summary

The current PhotoBooth system is **designed for single-printer operation**. Scaling from 1 to 2+ Canon Selphy CP1500 printers requires changes across all application layers. This document details the gaps, risks, and recommended implementation path.

---

## Current Architecture Analysis

### Single-Printer Constraints

| Component | File | Issue |
|-----------|------|-------|
| Configuration | `backend/app/config.py:40` | Single `printer_name: str` setting |
| Environment | `.env.example:13` | Single `PRINTER_NAME` variable |
| PrinterService | `infrastructure/services/printer_service.py:61` | `self.printer_name` is singular |
| Job Submission | `infrastructure/services/printer_service.py:166-171` | Always prints to `self.printer_name` |
| DB Schema | `infrastructure/database.py:93-130` | No `printer_name` column in `print_jobs` |
| Domain Entity | `domain/entities/print_job.py:11-27` | No printer field on `PrintJob` |
| API Request | `adapters/api/print_jobs.py:24-67` | No printer parameter on `POST /api/print` |
| Admin Status | `application/use_cases/admin/get_system_status.py:52-59` | Hardcoded single printer display |
| Queue Processing | UC-201 | Simple FIFO, no printer-aware distribution |

### Existing Multi-Printer Capabilities

The `PrinterService` already has methods that query all CUPS printers:

```python
# printer_service.py:93-135
def get_printers(self) -> List[PrinterInfo]:
    printers = self._cups.getPrinters()  # Gets ALL printers from CUPS
    ...

def get_printer_info(self, name: Optional[str] = None) -> Optional[PrinterInfo]:
    ...
```

These methods exist but are **never used for job submission or load balancing**.

---

## Risk: Deploying 2 Printers Without Changes

If two printers are registered in CUPS (`Selphy1`, `Selphy2`) with the current code:

1. Only `Selphy1` (from `PRINTER_NAME` env) receives jobs
2. `Selphy2` is completely ignored by the application
3. No audit trail of which printer handled which job
4. Admin dashboard shows stale/incorrect status (hardcoded name)
5. If `Selphy1` goes offline, jobs fail - no failover to `Selphy2`

---

## Required Changes for Multi-Printer Support

### Layer 1: Configuration

**File:** `backend/app/config.py`

```python
# Before
printer_name: str = "SelphyCP1500"

# After
printer_names: List[str] = ["SelphyCP1500"]  # Support multiple
printer_selection_strategy: str = "least-busy"  # round-robin | least-busy | random
```

**File:** `.env.example`

```bash
PRINTER_NAMES=Selphy1,Selphy2
PRINTER_SELECTION_STRATEGY=least-busy
```

### Layer 2: Database Schema

Add `printer_name` column to `print_jobs`:

```sql
ALTER TABLE print_jobs ADD COLUMN printer_name TEXT;
```

### Layer 3: Domain Entity

**File:** `backend/app/domain/entities/print_job.py`

```python
@dataclass
class PrintJob:
    # ... existing fields ...
    printer_name: Optional[str] = None  # NEW: which printer handles this job
```

### Layer 4: Printer Selection Service (New)

```python
class PrinterSelector:
    """Selects the best available printer based on strategy."""

    def __init__(self, strategy: str, printer_service: PrinterService):
        self.strategy = strategy
        self.printer_service = printer_service

    async def select(self) -> Optional[str]:
        printers = self.printer_service.get_printers()
        available = [p for p in printers if p.state == PrinterState.IDLE]

        if not available:
            return None

        if self.strategy == "round-robin":
            return self._round_robin(available)
        elif self.strategy == "least-busy":
            return self._least_busy(available)
        else:
            return available[0].name
```

### Layer 5: PrinterService Refactor

**File:** `backend/app/infrastructure/services/printer_service.py`

```python
# Before
async def print_image(self, image_path: str, copies: int = 1) -> PrintResult:
    ...
    job_id = self._cups.printFile(self.printer_name, ...)

# After
async def print_image(self, image_path: str, copies: int = 1,
                       printer_name: Optional[str] = None) -> PrintResult:
    target = printer_name or self.printer_names[0]
    ...
    job_id = self._cups.printFile(target, ...)
```

### Layer 6: API Endpoint

**File:** `backend/app/adapters/api/print_jobs.py`

```python
class PrintJobRequest(BaseModel):
    session_id: str
    copies: int = 1
    printer_name: Optional[str] = None  # NEW: optional printer selection
```

### Layer 7: Admin Dashboard

**File:** `frontend/src/pages/AdminDashboard.tsx`

Change from single printer card to a printer list:

```typescript
// Before: status.printer (single object)
// After: status.printers (array of printer objects)
{status.printers.map(printer => (
    <PrinterCard key={printer.name} printer={printer} />
))}
```

### Layer 8: Queue Processing

Modify UC-201 to:
1. Check all printers for availability (not just one)
2. Select best printer via `PrinterSelector`
3. Record selected printer in `print_jobs.printer_name`
4. Support per-printer retry logic

---

## Implementation Priority

### Phase 1: Core Multi-Printer (Required)

1. Config: Support `PRINTER_NAMES` list
2. DB: Add `printer_name` column + migration
3. Domain: Add `printer_name` to `PrintJob`
4. Service: Accept `printer_name` parameter in `print_image()`
5. Use Case: Integrate printer selection before submission

### Phase 2: Smart Distribution (Recommended)

6. Create `PrinterSelector` with least-busy strategy
7. Queue processor: printer-aware job assignment
8. Failover: if selected printer fails, retry on another

### Phase 3: Admin Visibility (Important)

9. API: Expose printer list endpoint (`GET /api/printers`)
10. Admin UI: Show all printers with individual status
11. Print history: Filter by printer

---

## Short-Term Workaround (Without Code Changes)

If two printers are needed immediately before implementing changes:

1. Deploy two PhotoBooth backend instances on different ports (8000, 8001)
2. Configure `PRINTER_NAME=Selphy1` on instance 1, `PRINTER_NAME=Selphy2` on instance 2
3. Use an nginx reverse proxy to distribute requests between them
4. Both share the same SQLite database (caution: concurrent write locking)

**Limitations of this approach:**
- Two separate systems to manage
- SQLite concurrent access issues
- No unified admin view
- No intelligent load balancing

---

## CUPS Setup for Multiple Same-Model Printers

When connecting two Canon Selphy CP1500 printers via USB:

```bash
# CUPS will auto-detect both printers with different URIs
# e.g., usb://Canon/SELPHY%20CP1500?serial=ABC123
#        usb://Canon/SELPHY%20CP1500?serial=DEF456

# Add them with distinct names
lpadmin -p Selphy1 -E -v usb://Canon/SELPHY%20CP1500?serial=ABC123 -m everywhere
lpadmin -p Selphy2 -E -v usb://Canon/SELPHY%20CP1500?serial=DEF456 -m everywhere

# Verify both are recognized
lpstat -p -d
```

CUPS differentiates same-model printers by USB serial number, so two identical CP1500s can coexist without conflict.

---

## Conclusion

The current system **cannot use two printers as-is**. The architecture is single-printer throughout all layers. However, the existing `get_printers()` infrastructure method provides a foundation to build upon. The recommended approach is to implement Phase 1 changes first, which provides basic multi-printer support, then progressively add smart distribution and admin visibility.
