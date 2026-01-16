# Testing Strategy

> Comprehensive testing approach for PhotoBooth application

---

## Overview

### Testing Pyramid

```
                    ┌───────────┐
                    │    E2E    │  Few, slow, high confidence
                    │   Tests   │
                   ┌┴───────────┴┐
                   │ Integration │  Some, medium speed
                   │    Tests    │
                  ┌┴─────────────┴┐
                  │   Unit Tests  │  Many, fast, isolated
                  └───────────────┘
```

### Test Distribution Target

| Type | Coverage Target | Count Estimate |
|------|-----------------|----------------|
| Unit | 80% | ~200 tests |
| Integration | Critical paths | ~50 tests |
| E2E | Happy paths | ~20 tests |

---

## Unit Testing

### Backend (Python/pytest)

#### Setup

```bash
# requirements-dev.txt
pytest==8.0.0
pytest-asyncio==0.23.0
pytest-cov==4.1.0
pytest-mock==3.12.0
httpx==0.26.0
factory-boy==3.3.0
```

#### Directory Structure

```
backend/
├── app/
│   ├── domain/
│   ├── application/
│   └── infrastructure/
└── tests/
    ├── conftest.py
    ├── unit/
    │   ├── domain/
    │   │   ├── test_entities.py
    │   │   └── test_value_objects.py
    │   ├── application/
    │   │   └── use_cases/
    │   │       ├── test_start_session.py
    │   │       ├── test_capture_photo.py
    │   │       └── test_submit_print.py
    │   └── infrastructure/
    │       └── test_repositories.py
    └── integration/
        └── test_api_endpoints.py
```

#### Example Unit Tests

```python
# tests/unit/domain/test_entities.py
import pytest
from app.domain.entities import PhotoSession, PrintJob
from app.domain.value_objects import SessionStatus, PrintStatus

class TestPhotoSession:
    def test_create_session_with_defaults(self):
        session = PhotoSession.create(language="ko")

        assert session.id is not None
        assert session.language == "ko"
        assert session.status == SessionStatus.ACTIVE
        assert len(session.photos) == 0

    def test_add_photo_increases_count(self):
        session = PhotoSession.create(language="ko")
        photo = session.add_photo(index=0, file_path="/path/to/photo.jpg")

        assert len(session.photos) == 1
        assert session.photos[0].index == 0

    def test_cannot_add_more_than_four_photos(self):
        session = PhotoSession.create(language="ko")
        for i in range(4):
            session.add_photo(index=i, file_path=f"/path/{i}.jpg")

        with pytest.raises(SessionFullError):
            session.add_photo(index=4, file_path="/path/5.jpg")

    def test_session_completes_with_four_photos(self):
        session = PhotoSession.create(language="ko")
        for i in range(4):
            session.add_photo(index=i, file_path=f"/path/{i}.jpg")

        assert session.status == SessionStatus.COMPLETE
        assert session.completed_at is not None


class TestPrintJob:
    def test_create_job(self):
        job = PrintJob.create(session_id="sess-123", copies=2)

        assert job.status == PrintStatus.PENDING
        assert job.copies == 2
        assert job.retry_count == 0

    def test_job_can_retry_on_retryable_error(self):
        job = PrintJob.create(session_id="sess-123", copies=1)
        job.fail(ErrorCode.PRINTER_OFFLINE)

        assert job.can_retry() is True

    def test_job_cannot_retry_after_max_attempts(self):
        job = PrintJob.create(session_id="sess-123", copies=1)
        job.retry_count = 3

        assert job.can_retry() is False

    def test_job_cannot_retry_on_non_retryable_error(self):
        job = PrintJob.create(session_id="sess-123", copies=1)
        job.fail(ErrorCode.PRINTER_PAPER_JAM)

        assert job.can_retry() is False
```

```python
# tests/unit/application/use_cases/test_submit_print.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.application.use_cases import SubmitPrintJobUseCase
from app.domain.entities import PhotoSession, PrintJob
from app.domain.value_objects import PrintStatus

class TestSubmitPrintJobUseCase:
    @pytest.fixture
    def mock_session_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_job_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_printer_service(self):
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_session_repo, mock_job_repo, mock_printer_service):
        return SubmitPrintJobUseCase(
            session_repository=mock_session_repo,
            job_repository=mock_job_repo,
            printer_service=mock_printer_service,
        )

    async def test_submit_creates_pending_job(
        self, use_case, mock_session_repo, mock_job_repo
    ):
        # Arrange
        session = PhotoSession.create(language="ko")
        for i in range(4):
            session.add_photo(index=i, file_path=f"/path/{i}.jpg")
        session.composite_path = "/path/composite.jpg"
        mock_session_repo.get_by_id.return_value = session

        # Act
        result = await use_case.execute(session_id="sess-123", copies=2)

        # Assert
        assert result.status == PrintStatus.PENDING
        assert result.copies == 2
        mock_job_repo.save.assert_called_once()

    async def test_submit_fails_without_composite(
        self, use_case, mock_session_repo
    ):
        # Arrange
        session = PhotoSession.create(language="ko")
        session.composite_path = None
        mock_session_repo.get_by_id.return_value = session

        # Act & Assert
        with pytest.raises(NoCompositeError):
            await use_case.execute(session_id="sess-123", copies=1)

    async def test_submit_fails_for_missing_session(
        self, use_case, mock_session_repo
    ):
        mock_session_repo.get_by_id.return_value = None

        with pytest.raises(SessionNotFoundError):
            await use_case.execute(session_id="nonexistent", copies=1)
```

#### Test Fixtures

```python
# tests/conftest.py
import pytest
import asyncio
from app.domain.entities import PhotoSession, PrintJob

@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def sample_session():
    session = PhotoSession.create(language="ko")
    for i in range(4):
        session.add_photo(index=i, file_path=f"/tmp/photo_{i}.jpg")
    return session

@pytest.fixture
def completed_session(sample_session):
    sample_session.composite_path = "/tmp/composite.jpg"
    return sample_session
```

#### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/domain/test_entities.py

# Run tests matching pattern
pytest -k "test_print"

# Verbose output
pytest -v
```

---

### Frontend (TypeScript/Vitest)

#### Setup

```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom
```

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './tests/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
    },
  },
});
```

```typescript
// tests/setup.ts
import '@testing-library/jest-dom';
```

#### Directory Structure

```
frontend/
├── src/
│   ├── components/
│   ├── hooks/
│   └── utils/
└── tests/
    ├── setup.ts
    ├── components/
    │   ├── Button.test.tsx
    │   ├── PhotoThumbnail.test.tsx
    │   └── CountdownTimer.test.tsx
    ├── hooks/
    │   ├── useCamera.test.ts
    │   └── usePrintStatus.test.ts
    └── utils/
        └── formatters.test.ts
```

#### Example Component Tests

```typescript
// tests/components/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Button } from '@/components/Button';

describe('Button', () => {
  it('renders with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    fireEvent.click(screen.getByText('Click me'));

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Click me</Button>);

    expect(screen.getByText('Click me')).toBeDisabled();
  });

  it('shows loading spinner when loading', () => {
    render(<Button loading>Submit</Button>);

    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByText('Submit')).toBeInTheDocument();
  });
});
```

```typescript
// tests/components/CountdownTimer.test.tsx
import { render, screen, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { CountdownTimer } from '@/components/CountdownTimer';

describe('CountdownTimer', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('displays initial countdown value', () => {
    render(<CountdownTimer seconds={5} onComplete={vi.fn()} />);

    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('counts down every second', () => {
    render(<CountdownTimer seconds={3} onComplete={vi.fn()} />);

    expect(screen.getByText('3')).toBeInTheDocument();

    act(() => vi.advanceTimersByTime(1000));
    expect(screen.getByText('2')).toBeInTheDocument();

    act(() => vi.advanceTimersByTime(1000));
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('calls onComplete when countdown reaches zero', () => {
    const onComplete = vi.fn();
    render(<CountdownTimer seconds={2} onComplete={onComplete} />);

    act(() => vi.advanceTimersByTime(2000));

    expect(onComplete).toHaveBeenCalledTimes(1);
  });
});
```

#### Example Hook Tests

```typescript
// tests/hooks/usePrintStatus.test.ts
import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { usePrintStatus } from '@/hooks/usePrintStatus';

describe('usePrintStatus', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches initial status', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        success: true,
        data: { status: 'PRINTING', progress: 50 },
      }),
    });

    const { result } = renderHook(() => usePrintStatus('job-123'));

    await waitFor(() => {
      expect(result.current.status).toBe('PRINTING');
      expect(result.current.progress).toBe(50);
    });
  });

  it('polls for updates', async () => {
    global.fetch = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          data: { status: 'PRINTING', progress: 25 },
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          data: { status: 'PRINTING', progress: 75 },
        }),
      });

    vi.useFakeTimers();

    const { result } = renderHook(() => usePrintStatus('job-123'));

    await waitFor(() => {
      expect(result.current.progress).toBe(25);
    });

    act(() => vi.advanceTimersByTime(1000));

    await waitFor(() => {
      expect(result.current.progress).toBe(75);
    });

    vi.useRealTimers();
  });

  it('stops polling on completion', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        success: true,
        data: { status: 'COMPLETED', progress: 100 },
      }),
    });

    const { result } = renderHook(() => usePrintStatus('job-123'));

    await waitFor(() => {
      expect(result.current.isComplete).toBe(true);
    });
  });
});
```

#### Running Frontend Tests

```bash
# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Watch mode
npm test -- --watch

# Run specific file
npm test -- tests/components/Button.test.tsx
```

---

## Integration Testing

### API Integration Tests

```python
# tests/integration/test_api_endpoints.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

class TestSessionAPI:
    async def test_create_session(self, client):
        response = await client.post("/api/session", json={"language": "ko"})

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "session_id" in data["data"]
        assert data["data"]["language"] == "ko"

    async def test_get_session(self, client):
        # Create session first
        create_response = await client.post("/api/session", json={})
        session_id = create_response.json()["data"]["session_id"]

        # Get session
        response = await client.get(f"/api/session/{session_id}")

        assert response.status_code == 200
        assert response.json()["data"]["session_id"] == session_id

    async def test_get_nonexistent_session_returns_404(self, client):
        response = await client.get("/api/session/nonexistent-id")

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "SESSION_NOT_FOUND"


class TestPrintAPI:
    async def test_submit_print_without_composite_fails(self, client):
        # Create session without completing it
        create_response = await client.post("/api/session", json={})
        session_id = create_response.json()["data"]["session_id"]

        response = await client.post("/api/print", json={
            "session_id": session_id,
            "copies": 1,
        })

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "PRINT_NO_COMPOSITE"


class TestAdminAPI:
    async def test_login_with_correct_pin(self, client):
        # Note: In dev environment, default PIN is "0000"
        # In production, ADMIN_PIN must be set via environment variable
        response = await client.post("/api/admin/login", json={
            "pin": os.environ.get("ADMIN_PIN", "0000")  # Dev default
        })

        assert response.status_code == 200
        assert "token" in response.json()["data"]

    async def test_login_with_wrong_pin(self, client):
        response = await client.post("/api/admin/login", json={
            "pin": "9999"  # Wrong PIN
        })

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "AUTH_INVALID_PIN"

    async def test_protected_endpoint_requires_auth(self, client):
        response = await client.get("/api/admin/status")

        assert response.status_code == 401

    async def test_protected_endpoint_with_valid_token(self, client):
        # Login first
        login_response = await client.post("/api/admin/login", json={
            "pin": os.environ.get("ADMIN_PIN", "0000")  # Dev default
        })
        token = login_response.json()["data"]["token"]

        # Access protected endpoint
        response = await client.get(
            "/api/admin/status",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
```

### Database Integration Tests

```python
# tests/integration/test_repositories.py
import pytest
from app.infrastructure.persistence import SQLiteSessionRepository
from app.domain.entities import PhotoSession

@pytest.fixture
async def session_repo(tmp_path):
    db_path = tmp_path / "test.db"
    repo = SQLiteSessionRepository(str(db_path))
    await repo.initialize()
    yield repo
    await repo.close()

class TestSQLiteSessionRepository:
    async def test_save_and_get_session(self, session_repo):
        session = PhotoSession.create(language="en")

        await session_repo.save(session)
        retrieved = await session_repo.get_by_id(session.id)

        assert retrieved is not None
        assert retrieved.id == session.id
        assert retrieved.language == "en"

    async def test_update_session(self, session_repo):
        session = PhotoSession.create(language="ko")
        await session_repo.save(session)

        session.language = "en"
        await session_repo.update(session)

        retrieved = await session_repo.get_by_id(session.id)
        assert retrieved.language == "en"

    async def test_get_nonexistent_returns_none(self, session_repo):
        result = await session_repo.get_by_id("nonexistent")
        assert result is None
```

---

## End-to-End Testing

### Setup (Playwright)

```bash
npm install -D @playwright/test
npx playwright install
```

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  retries: 2,
  use: {
    baseURL: 'http://localhost:80',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'iPad',
      use: {
        viewport: { width: 820, height: 1180 },
        deviceScaleFactor: 2,
        isMobile: true,
        hasTouch: true,
      },
    },
  ],
});
```

### E2E Test Examples

```typescript
// e2e/photo-session.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Photo Session Flow', () => {
  test('complete photo session happy path', async ({ page }) => {
    // Start on home page
    await page.goto('/');
    await expect(page.getByText('Start Session')).toBeVisible();

    // Start session
    await page.getByText('Start Session').click();
    await expect(page.getByText('Photo 1 of 4')).toBeVisible();

    // Capture 4 photos (mocked camera)
    for (let i = 1; i <= 4; i++) {
      await page.getByRole('button', { name: 'Capture' }).click();
      await page.waitForTimeout(500); // Wait for countdown

      if (i < 4) {
        await expect(page.getByText(`Photo ${i + 1} of 4`)).toBeVisible();
      }
    }

    // Preview page
    await expect(page.getByText('Your Photos Are Ready')).toBeVisible();
    await expect(page.locator('.composite-preview')).toBeVisible();

    // Submit print
    await page.getByRole('button', { name: 'Print' }).click();

    // Print status
    await expect(page.getByText(/Printing|Completed/)).toBeVisible();
  });

  test('can retake a photo from preview', async ({ page }) => {
    // ... setup session with 4 photos

    await page.goto('/preview/session-id');

    // Click first thumbnail to retake
    await page.locator('.thumbnail-button').first().click();

    // Should be back at camera
    await expect(page.getByText('Retake Photo 1')).toBeVisible();

    // Capture new photo
    await page.getByRole('button', { name: 'Capture' }).click();

    // Back to preview
    await expect(page.getByText('Your Photos Are Ready')).toBeVisible();
  });

  test('can change language', async ({ page }) => {
    await page.goto('/');

    // Default is Korean
    await expect(page.getByText('시작하기')).toBeVisible();

    // Change to English
    await page.getByRole('button', { name: 'Language' }).click();
    await page.getByText('English').click();

    // Now shows English
    await expect(page.getByText('Start Session')).toBeVisible();
  });
});

test.describe('Admin Dashboard', () => {
  test('admin login and view status', async ({ page }) => {
    await page.goto('/admin');

    // Login form
    await expect(page.getByText('Enter PIN')).toBeVisible();

    // Enter PIN
    await page.getByRole('button', { name: '1' }).click();
    await page.getByRole('button', { name: '9' }).click();
    await page.getByRole('button', { name: '9' }).click();
    await page.getByRole('button', { name: '8' }).click();

    // Dashboard loads
    await expect(page.getByText('System Status')).toBeVisible();
    await expect(page.getByText(/Healthy|Warning/)).toBeVisible();
  });
});
```

### Running E2E Tests

```bash
# Run all e2e tests
npx playwright test

# Run with UI
npx playwright test --ui

# Run specific file
npx playwright test e2e/photo-session.spec.ts

# Debug mode
npx playwright test --debug

# Generate HTML report
npx playwright show-report
```

---

## Test Environment

### Docker Test Environment

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  backend-test:
    build:
      context: ./backend
      dockerfile: Dockerfile.test
    environment:
      - DATABASE_URL=sqlite:///tmp/test.db
      - TESTING=true
    volumes:
      - ./backend:/app
    command: pytest --cov=app

  frontend-test:
    build:
      context: ./frontend
      dockerfile: Dockerfile.test
    volumes:
      - ./frontend:/app
    command: npm test

  e2e-test:
    build:
      context: ./e2e
    depends_on:
      - backend-test
      - frontend-test
    command: npx playwright test
```

### CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Run tests
        run: |
          cd frontend
          npm test -- --coverage

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]
    steps:
      - uses: actions/checkout@v4

      - name: Start services
        run: docker compose -f docker-compose.test.yml up -d

      - name: Run E2E tests
        run: |
          cd e2e
          npx playwright test

      - name: Upload test artifacts
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: e2e/playwright-report/
```

---

## Test Data

### Factories

```python
# tests/factories.py
import factory
from app.domain.entities import PhotoSession, PrintJob, Photo

class PhotoSessionFactory(factory.Factory):
    class Meta:
        model = PhotoSession

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    language = "ko"
    status = "ACTIVE"
    created_at = factory.LazyFunction(datetime.utcnow)

class PhotoFactory(factory.Factory):
    class Meta:
        model = Photo

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    index = factory.Sequence(lambda n: n % 4)
    file_path = factory.LazyAttribute(lambda o: f"/tmp/photo_{o.index}.jpg")

class PrintJobFactory(factory.Factory):
    class Meta:
        model = PrintJob

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    session_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    status = "PENDING"
    copies = 1
```

---

## Coverage Requirements

| Module | Minimum Coverage |
|--------|------------------|
| Domain entities | 90% |
| Use cases | 85% |
| API routes | 80% |
| UI components | 75% |
| Utilities | 90% |

### Coverage Commands

```bash
# Backend
pytest --cov=app --cov-report=html --cov-fail-under=80

# Frontend
npm test -- --coverage --coverageThreshold='{"global":{"lines":75}}'
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
