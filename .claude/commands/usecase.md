---
description: View specific use case documentation
argument-hint: <use-case-id: UC-001 to UC-205>
---

View detailed use case documentation.

**Use Case ID**: $ARGUMENTS

## Instructions

### If no ID provided
1. Read `docs/use-cases/INDEX.md`
2. Display the full use case catalog organized by category:
   - User-Facing (UC-001 to UC-010)
   - Admin (UC-101 to UC-109)
   - System (UC-201 to UC-205)
3. Show priority levels (P0, P1, P2)
4. Ask which use case to explore

### If ID provided (e.g., UC-005)
1. Read `docs/use-cases/UC-005-*.md`
2. Summarize:
   - Main flow steps
   - Alternative flows
   - Exception handling
   - Business rules
   - Technical implementation hints
3. Highlight related use cases

## Use Case Categories

| Range | Category | Count |
|-------|----------|-------|
| UC-001 to UC-010 | User-Facing | 10 |
| UC-101 to UC-109 | Admin | 9 |
| UC-201 to UC-205 | System Background | 5 |

## Priority Levels

- **P0**: Critical - MVP must-have
- **P1**: Important - First iteration
- **P2**: Nice to have - Can defer

## Example Usage

```
/usecase UC-002      # View Capture Photo use case
/usecase UC-101      # View Admin Login use case
/usecase UC-203      # View Auto-Retry Print use case
```
