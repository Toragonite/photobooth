---
description: Run linters and formatters on the codebase
argument-hint: [target: all|backend|frontend|fix]
---

Run code quality checks on PhotoBooth codebase.

**Target**: $ARGUMENTS (default: all)

## Instructions

### Backend (Python)
```bash
# Check formatting
black --check backend/

# Check import sorting
isort --check-only backend/

# Type checking
mypy backend/app/ --ignore-missing-imports

# Linting
ruff check backend/
```

### Frontend (TypeScript/React)
```bash
cd frontend

# ESLint
npm run lint

# Type checking
npx tsc --noEmit

# Prettier check
npx prettier --check "src/**/*.{ts,tsx,js,jsx,json,css}"
```

### If "fix" is specified
Auto-fix all issues that can be automatically resolved:

```bash
# Backend
black backend/
isort backend/
ruff check --fix backend/

# Frontend
cd frontend
npm run lint -- --fix
npx prettier --write "src/**/*.{ts,tsx,js,jsx,json,css}"
```

## Output

1. List all linting errors grouped by file
2. Show count of fixable vs non-fixable issues
3. Suggest fixes for common patterns
4. Offer to auto-fix if issues found
