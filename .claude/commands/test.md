---
description: Run tests for backend, frontend, or all
argument-hint: [scope: backend|frontend|all|unit|integration|e2e]
---

Run tests for the PhotoBooth application.

**Scope**: $ARGUMENTS (default: all)

## Instructions

Based on the scope provided, execute the appropriate test suite:

### If scope is "backend" or "unit":
```bash
cd backend && pytest tests/unit/ -v --tb=short
```

### If scope is "frontend":
```bash
cd frontend && npm test
```

### If scope is "integration":
```bash
cd backend && pytest tests/integration/ -v --tb=short
```

### If scope is "e2e":
```bash
cd e2e && npx playwright test
```

### If scope is "all" or empty:
Run both backend and frontend tests sequentially.

## Expected Output

1. Show test results with pass/fail counts
2. Highlight any failing tests
3. Suggest fixes for common test failures
4. Report coverage percentage if available

## On Failure

If tests fail:
1. Analyze the error messages
2. Identify the root cause
3. Suggest specific fixes
4. Offer to fix automatically if straightforward
