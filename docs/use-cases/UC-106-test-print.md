# UC-106: Test Print

## Summary

Admin prints a test page to verify printer connectivity and print quality. Uses a predefined test image or the last successful composite to validate the print pipeline.

---

## Actors

| Actor | Type | Description |
|-------|------|-------------|
| **Admin** | Primary | Operator testing printer |
| **System** | Secondary | Sends test print job |

---

## Preconditions

| ID | Condition |
|----|-----------|
| PRE-1 | Admin is authenticated |
| PRE-2 | Printer is connected |
| PRE-3 | CUPS service is running |

---

## Trigger

Admin taps [Test Print] button on dashboard.

---

## Main Flow

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Step                                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ Admin navigates to Printer section on dashboard               │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ Admin taps [Test Print] button                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ System shows test print options:                              │
│     │ - Test pattern (color bars, alignment grid)                   │
│     │ - Last composite (if available)                               │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4   │ Admin selects test type                                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5   │ System shows confirmation:                                    │
│     │ "Print test page? This will use paper and ink."               │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6   │ Admin confirms                                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7   │ Frontend sends: POST /api/admin/test-print                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8   │ Backend creates test print job:                               │
│     │ - Type: TEST                                                  │
│     │ - Session: null (admin test)                                  │
│     │ - Copies: 1                                                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 9   │ Submit to CUPS via normal print queue                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 10  │ Monitor print progress                                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ 11  │ Display result:                                               │
│     │ - Success: "Test print completed successfully"                │
│     │ - Failed: Error details with troubleshooting tips             │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Alternative Flows

### AF-1: No Previous Composite

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 3a  │ No completed sessions exist                                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3b  │ Only "Test Pattern" option available                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3c  │ Continue with test pattern                                    │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-2: Quick Test Print

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 2a  │ Admin long-presses [Test Print] button                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2b  │ Skip options dialog, use test pattern                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2c  │ Still show confirmation dialog                                │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Exception Flows

### EX-1: Printer Offline

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Printer detected as offline before sending                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Show error: "Printer is offline"                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Troubleshooting tips:                                         │
│     │ - Check printer is powered on                                 │
│     │ - Check USB cable connection                                  │
│     │ - Try restarting print service                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ [Restart Print Service] quick action button                   │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-2: Print Job Fails

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Test print job fails                                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Show error with CUPS error message                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Display troubleshooting based on error:                       │
│     │ - Paper empty: "Load paper in printer"                        │
│     │ - Ink empty: "Replace ink cartridge"                          │
│     │ - Job rejected: "Try restarting CUPS"                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ [Retry] button available                                      │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Postconditions

| ID | Condition |
|----|-----------|
| POST-1 | Test print result logged |
| POST-2 | Admin has verified printer functionality |
| POST-3 | Test job recorded (for tracking) |

---

## Business Rules

| ID | Rule |
|----|------|
| TST-BR-1 | Test prints always single copy |
| TST-BR-2 | Test prints bypass retry logic |
| TST-BR-3 | Test prints logged separately from user prints |
| TST-BR-4 | Confirmation required to prevent accidental prints |

---

## Test Pattern Design

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                     PHOTOBOOTH TEST PRINT                       │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │    ████  ████  ████  ████  ████  ████  ████  ████       │   │
│  │    RED   GRN   BLU   CYN   MAG   YEL   BLK   WHT        │   │
│  │                                                          │   │
│  │    Color Bars - Check for color accuracy                 │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │    ┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼            │   │
│  │    │   │   │   │   │   │   │   │   │   │   │            │   │
│  │    ┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼            │   │
│  │    │   │   │   │   │   │   │   │   │   │   │            │   │
│  │    ┼───┼───┼───┼───┼───┼───┼───┼───┼───┼───┼            │   │
│  │                                                          │   │
│  │    Alignment Grid - Check for alignment                  │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │    ░░▒▒▓▓██████████████████████████████████▓▓▒▒░░       │   │
│  │                                                          │   │
│  │    Gradient - Check for banding                          │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Date: 2024-01-13 14:32:00                                      │
│  Printer: Canon_SELPHY_CP1500                                   │
│  System: PhotoBooth v1.0.0                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## UI/UX Requirements

### Test Print Button

```
Printer Status Card:
┌──────────────────────────────────────────────────────────────┐
│  🖨️ Canon Selphy CP1500                                      │
│  Status: ✅ Ready (idle)                                     │
│                                                              │
│  ┌─────────────────┐                    ┌─────────────────┐  │
│  │   Test Print    │                    │  View Queue →   │  │
│  └─────────────────┘                    └─────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### Test Print Options Dialog

```
┌─────────────────────────────────────────────────────────────────┐
│     ┌─────────────────────────────────────────────────────┐     │
│     │                                                     │     │
│     │              Test Print                             │     │
│     │                                                     │     │
│     │   Select what to print:                             │     │
│     │                                                     │     │
│     │   ○ Test Pattern                                    │     │
│     │     Color bars, alignment grid                      │     │
│     │                                                     │     │
│     │   ○ Last Composite                                  │     │
│     │     From session abc-123 (2 hours ago)              │     │
│     │                                                     │     │
│     │                                                     │     │
│     │   ⚠️ This will use 1 sheet of paper and ink.        │     │
│     │                                                     │     │
│     │   ┌──────────────┐     ┌──────────────────┐         │     │
│     │   │    Cancel    │     │   Print Test     │         │     │
│     │   └──────────────┘     └──────────────────┘         │     │
│     │                                                     │     │
│     └─────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

### Test Print Progress

```
┌─────────────────────────────────────────────────────────────────┐
│     ┌─────────────────────────────────────────────────────┐     │
│     │                                                     │     │
│     │              Printing Test Page...                  │     │
│     │                                                     │     │
│     │                   ◐ ◓ ◑ ◒                           │     │
│     │                                                     │     │
│     │              Status: Processing                     │     │
│     │                                                     │     │
│     └─────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technical Notes

### API Endpoint

```typescript
// POST /api/admin/test-print

interface TestPrintRequest {
  type: 'pattern' | 'last_composite';
}

interface TestPrintResponse {
  success: boolean;
  job_id: string;
  message: string;
  error?: string;
}
```

### Backend Implementation

```python
# Test print use case

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

class TestPrintUseCase:
    TEST_PATTERN_PATH = Path('/app/assets/test-pattern.jpg')

    def __init__(
        self,
        print_job_repo: PrintJobRepository,
        session_repo: SessionRepository,
        printer_service: PrinterService,
    ):
        self._jobs = print_job_repo
        self._sessions = session_repo
        self._printer = printer_service

    async def execute(self, test_type: str) -> TestPrintResponse:
        # Check printer status first
        status = await self._printer.get_status()
        if status.status == 'offline':
            raise PrinterOfflineError("Printer is offline")

        # Get test image path
        if test_type == 'pattern':
            image_path = self._generate_test_pattern()
        else:
            image_path = await self._get_last_composite()

        # Create test print job
        job = PrintJob(
            id=str(uuid.uuid4()),
            session_id=None,  # Admin test
            composite_path=image_path,
            copies=1,
            status=PrintStatus.PENDING,
            job_type='TEST',
        )

        await self._jobs.create(job)

        # Submit directly (bypass queue for immediate feedback)
        try:
            result = await self._printer.print_file(
                image_path,
                PrintOptions(media='4x6', quality='high', copies=1)
            )

            if result.success:
                job.status = PrintStatus.COMPLETED
                job.cups_job_id = result.cups_job_id
                await self._jobs.update(job)

                return TestPrintResponse(
                    success=True,
                    job_id=job.id,
                    message="Test print submitted successfully",
                )
            else:
                job.status = PrintStatus.FAILED
                job.error_message = result.error_message
                await self._jobs.update(job)

                return TestPrintResponse(
                    success=False,
                    job_id=job.id,
                    message="Test print failed",
                    error=result.error_message,
                )

        except Exception as e:
            job.status = PrintStatus.FAILED
            job.error_message = str(e)
            await self._jobs.update(job)
            raise

    def _generate_test_pattern(self) -> Path:
        """Generate test pattern image."""
        if self.TEST_PATTERN_PATH.exists():
            return self.TEST_PATTERN_PATH

        # Generate dynamically
        width, height = 1200, 1800  # 4x6 at 300 DPI
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)

        # Add title
        draw.text((width//2, 50), "PHOTOBOOTH TEST PRINT",
                  fill='black', anchor='mt')

        # Color bars
        colors = ['red', 'green', 'blue', 'cyan', 'magenta', 'yellow', 'black', 'white']
        bar_width = width // len(colors)
        for i, color in enumerate(colors):
            x = i * bar_width
            draw.rectangle([x, 150, x + bar_width, 350], fill=color)

        # Grid
        for x in range(100, width - 100, 50):
            draw.line([(x, 400), (x, 700)], fill='gray')
        for y in range(400, 700, 50):
            draw.line([(100, y), (width - 100, y)], fill='gray')

        # Gradient
        for x in range(100, width - 100):
            gray = int((x - 100) / (width - 200) * 255)
            draw.line([(x, 750), (x, 850)], fill=(gray, gray, gray))

        # Metadata
        from datetime import datetime
        draw.text((50, height - 100),
                  f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                  fill='black')

        # Save
        self.TEST_PATTERN_PATH.parent.mkdir(parents=True, exist_ok=True)
        img.save(self.TEST_PATTERN_PATH, 'JPEG', quality=95)

        return self.TEST_PATTERN_PATH

    async def _get_last_composite(self) -> Path:
        """Get last completed session's composite."""
        session = await self._sessions.get_last_completed()
        if not session or not session.composite_path:
            raise ValueError("No previous composite available")

        path = Path(session.composite_path)
        if not path.exists():
            raise ValueError("Previous composite file not found")

        return path
```

---

## Related Use Cases

- **UC-102**: View System Status (printer status display)
- **UC-105**: Restart Service (troubleshooting action)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
