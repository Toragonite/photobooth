# Use Cases Index

> All use cases for the PhotoBooth system

---

## Use Case Catalog

### User-Facing Use Cases

| ID | Use Case | Actor | Priority | Document |
|----|----------|-------|----------|----------|
| UC-001 | Start Photo Session | User | P0 | [UC-001](./UC-001-start-photo-session.md) |
| UC-002 | Capture Photo | User | P0 | [UC-002](./UC-002-capture-photo.md) |
| UC-003 | Retake Photo | User | P1 | [UC-003](./UC-003-retake-photo.md) |
| UC-004 | Preview Composite | User | P0 | [UC-004](./UC-004-preview-composite.md) |
| UC-005 | Submit Print Job | User | P0 | [UC-005](./UC-005-submit-print-job.md) |
| UC-006 | Monitor Print Status | User | P0 | [UC-006](./UC-006-monitor-print-status.md) |
| UC-007 | Retry Failed Print | User | P1 | [UC-007](./UC-007-retry-failed-print.md) |
| UC-008 | Abort Print Job | User | P1 | [UC-008](./UC-008-abort-print-job.md) |
| UC-009 | Change Language | User | P1 | [UC-009](./UC-009-change-language.md) |
| UC-010 | Return to Home | User | P1 | [UC-010](./UC-010-return-to-home.md) |

### Admin Use Cases

| ID | Use Case | Actor | Priority | Document |
|----|----------|-------|----------|----------|
| UC-101 | Admin Login | Admin | P0 | [UC-101](./UC-101-admin-login.md) |
| UC-102 | View System Status | Admin | P0 | [UC-102](./UC-102-view-system-status.md) |
| UC-103 | View Print History | Admin | P1 | [UC-103](./UC-103-view-print-history.md) |
| UC-104 | Update Settings | Admin | P1 | [UC-104](./UC-104-update-settings.md) |
| UC-105 | Restart Service | Admin | P1 | [UC-105](./UC-105-restart-service.md) |
| UC-106 | Test Print | Admin | P2 | [UC-106](./UC-106-test-print.md) |
| UC-107 | View Logs | Admin | P2 | [UC-107](./UC-107-view-logs.md) |
| UC-108 | Download Photos | Admin | P2 | [UC-108](./UC-108-download-photos.md) |
| UC-109 | Reboot System | Admin | P2 | [UC-109](./UC-109-reboot-system.md) |

### System Use Cases (Background)

| ID | Use Case | Actor | Priority | Document |
|----|----------|-------|----------|----------|
| UC-201 | Process Print Queue | System | P0 | [UC-201](./UC-201-process-print-queue.md) |
| UC-202 | Monitor Print Job | System | P0 | [UC-202](./UC-202-monitor-print-job.md) |
| UC-203 | Auto-Retry Print | System | P0 | [UC-203](./UC-203-auto-retry-print.md) |
| UC-204 | Cleanup Storage | System | P1 | [UC-204](./UC-204-cleanup-storage.md) |
| UC-205 | Health Check | System | P1 | [UC-205](./UC-205-health-check.md) |

---

## Priority Legend

| Priority | Meaning | When to Implement |
|----------|---------|-------------------|
| **P0** | Critical | MVP - Must have for basic functionality |
| **P1** | Important | First iteration - Expected features |
| **P2** | Nice to have | Enhancement - Can defer if needed |

---

## Use Case Document Template

Each use case document follows this structure:

```markdown
# UC-XXX: Use Case Name

## Summary
Brief description

## Actors
- Primary: Who initiates
- Secondary: Who else is involved

## Preconditions
What must be true before

## Trigger
What starts this use case

## Main Flow
1. Step by step
2. Happy path

## Alternative Flows
- 3a. Variation
- 4b. Another path

## Exception Flows
- E1. Error handling

## Postconditions
What is true after success

## Business Rules
- BR-1: Rule description

## Data Requirements
Input/output specifications

## UI/UX Requirements
Screen mockups, interaction notes

## Technical Notes
Implementation hints

## Open Questions
Unresolved items
```

---

## Traceability Matrix

| Requirement | Use Cases |
|-------------|-----------|
| Capture 4 photos | UC-001, UC-002, UC-003 |
| Print composite | UC-004, UC-005, UC-006 |
| Error recovery | UC-007, UC-008, UC-203 |
| Admin management | UC-101 through UC-109 |
| System reliability | UC-201 through UC-205 |
