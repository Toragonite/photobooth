---
description: Build the application for development or production
argument-hint: [target: dev|prod|docker|frontend|backend]
---

Build the PhotoBooth application.

**Target**: $ARGUMENTS (default: dev)

## Instructions

### If target is "dev":
1. Install backend dependencies: `pip install -r backend/requirements.txt`
2. Install frontend dependencies: `cd frontend && npm install`
3. Run type checking and linting
4. Report any issues

### If target is "prod":
1. Build frontend for production: `cd frontend && npm run build`
2. Validate build output
3. Check for any build warnings

### If target is "docker":
1. Build Docker images: `docker compose build`
2. Verify images created successfully
3. Report image sizes

### If target is "frontend":
1. `cd frontend && npm install && npm run build`
2. Report bundle size

### If target is "backend":
1. `pip install -r backend/requirements.txt`
2. Run `python -m py_compile` on all Python files
3. Report any syntax errors

## Validation

After build:
1. Check for TypeScript errors (frontend)
2. Check for Python syntax errors (backend)
3. Verify all dependencies resolved
4. Report build time and artifact sizes
