# Pre-PR Quality Check Command

Run comprehensive code quality checks before creating a pull request.

## Usage

```
/pre-pr [options]
```

## Options

- `--quick` - Run only formatting and lint checks (fast)
- `--fix` - Auto-fix issues where possible
- `--backend` - Check backend only
- `--frontend` - Check frontend only
- `--coverage` - Include coverage report
- `--security` - Include security scan

## What It Checks

### Quick Mode (--quick)
1. Code formatting (black, prettier)
2. Import sorting (isort)
3. Linting (flake8, eslint)

### Full Mode (default)
1. All quick checks
2. Type checking (mypy, tsc)
3. Unit tests
4. Code coverage (≥80% required)
5. Security vulnerabilities
6. Code complexity

## Example Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Pre-PR Quality Check
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Branch: feature/add-photo-filters
Changes: 12 files (+340, -89)

[1/6] Formatting............ ✅ PASS
[2/6] Linting............... ✅ PASS
[3/6] Type Check............ ✅ PASS
[4/6] Unit Tests............ ✅ 47/47 passed
[5/6] Coverage.............. ✅ 84.2%
[6/6] Security.............. ✅ No vulnerabilities

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Result: ✅ READY FOR PR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Instructions

When this command is invoked, perform the following:

1. **Identify changed files**
   ```bash
   git diff --name-only origin/main...HEAD
   ```

2. **Run backend checks** (if Python files changed)
   ```bash
   cd backend
   black app/ tests/ --check
   isort app/ tests/ --check-only
   flake8 app/ tests/
   mypy app/ --ignore-missing-imports
   pytest tests/ -v --cov=app --cov-fail-under=80
   bandit -r app/ -ll
   ```

3. **Run frontend checks** (if TS/TSX files changed)
   ```bash
   cd frontend
   npm run lint
   npx prettier --check "src/**/*.{ts,tsx}"
   npx tsc --noEmit
   npm test -- --run --coverage
   npm audit --audit-level=high
   ```

4. **Generate report**
   - Summarize pass/fail status for each check
   - List specific issues that need fixing
   - Provide fix commands where applicable

5. **Update state**
   - Record quality check result in `.claude/state/development.json`

## Auto-Fix Mode

When `--fix` is specified:

```bash
# Backend
black backend/app/ backend/tests/
isort backend/app/ backend/tests/

# Frontend
npm run lint -- --fix
npx prettier --write "src/**/*.{ts,tsx,css}"
```

## Quality Gates

| Gate | Threshold | Blocking |
|------|-----------|----------|
| Formatting | 0 errors | Yes |
| Linting | 0 errors | Yes |
| Type errors | 0 errors | Yes |
| Test failures | 0 failures | Yes |
| Coverage | ≥80% | Yes |
| Security (critical) | 0 issues | Yes |
| Security (high) | 0 issues | Yes |
| Complexity | ≤15 | Warning |
