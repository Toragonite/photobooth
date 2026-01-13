# UC-004: Preview Composite

## Summary

After capturing all 4 photos, the user previews the composite image showing the final 4-cut layout before printing. This is the decision point where users can retake individual photos or proceed to print.

---

## Actors

| Actor | Type | Description |
|-------|------|-------------|
| **User** | Primary | Person reviewing composite before print |
| **System** | Secondary | Generates and displays composite |

---

## Preconditions

| ID | Condition |
|----|-----------|
| PRE-1 | Active session exists |
| PRE-2 | Session has exactly 4 captured photos |
| PRE-3 | Session status is COMPLETE |
| PRE-4 | All photos passed validation |

---

## Trigger

Session reaches 4 photos (automatic navigation) OR user navigates from print flow.

---

## Main Flow

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Step                                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ System detects session has 4 photos                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ System generates composite image:                             │
│     │ - Arranges 4 photos in 2x2 grid                               │
│     │ - Adds event logo (if enabled)                                │
│     │ - Adds date/time stamp                                        │
│     │ - Applies 4x6 inch layout template                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ Navigate to Preview page                                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4   │ System displays:                                              │
│     │ - Large composite preview (centered)                          │
│     │ - 4 individual photo thumbnails (tappable for retake)         │
│     │ - Copy count selector (1-3)                                   │
│     │ - [Print] button                                              │
│     │ - [Home] button                                               │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5   │ User reviews composite image                                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6   │ User selects number of copies (default: 1)                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7   │ User taps [Print] button                                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8   │ Proceed to UC-005: Submit Print Job                           │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Alternative Flows

### AF-1: Retake Individual Photo

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 5a  │ User taps on a thumbnail photo                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5b  │ Proceed to UC-003: Retake Photo                               │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5c  │ After retake, return to Preview with updated composite        │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-2: Abandon Session

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 5a  │ User taps [Home] button                                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5b  │ System shows confirmation dialog:                             │
│     │ "Abandon photos? / 사진을 포기하시겠습니까?"                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5c  │ If confirmed:                                                 │
│     │ - Session status → ABANDONED                                  │
│     │ - Navigate to Home                                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5d  │ If cancelled: Remain on Preview page                          │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-3: Change Copy Count

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 6a  │ User taps [+] or [-] on copy selector                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6b  │ Count updates within range [1, 3]                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6c  │ Print button updates: "Print 2 copies / 2장 인쇄"             │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Exception Flows

### EX-1: Composite Generation Fails

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Backend fails to generate composite (memory/disk error)       │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ System displays error:                                        │
│     │ "Image processing failed. Please try again."                  │
│     │ "이미지 처리에 실패했습니다. 다시 시도해 주세요."                │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ [Retry] button attempts composite generation again            │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ If retry fails: Show [Start New Session] option               │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-2: Photo File Missing

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ One or more photo files not found during composite generation │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ System identifies missing photo(s)                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Force retake for missing photo(s)                             │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Navigate to Camera with retake mode for first missing photo   │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Postconditions

| ID | Condition |
|----|-----------|
| POST-1 | Composite image generated and stored |
| POST-2 | Composite path saved to session |
| POST-3 | User has selected copy count |
| POST-4 | Session ready for print submission |

---

## Business Rules

| ID | Rule |
|----|------|
| PREV-BR-1 | Composite generated only when session has exactly 4 photos |
| PREV-BR-2 | Copy count range: 1-3 (configurable max in settings) |
| PREV-BR-3 | Default copy count: 1 |
| PREV-BR-4 | Composite dimensions: 4x6 inches at 300 DPI (1200x1800 pixels) |
| PREV-BR-5 | Logo placement: bottom center (if enabled) |
| PREV-BR-6 | Date stamp format: configurable from admin settings |

---

## UI/UX Requirements

### Preview Page Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  [🏠]                                           [Language: 🌐]  │
│                                                                 │
│                    Your Photos Are Ready!                       │
│                      사진이 준비되었습니다!                       │
│                                                                 │
│       ┌─────────────────────────────────────────────┐           │
│       │                                             │           │
│       │         ┌─────────┬─────────┐               │           │
│       │         │         │         │               │           │
│       │         │  Photo  │  Photo  │               │           │
│       │         │    1    │    2    │               │           │
│       │         │         │         │               │           │
│       │         ├─────────┼─────────┤               │           │
│       │         │         │         │               │           │
│       │         │  Photo  │  Photo  │               │           │
│       │         │    3    │    4    │               │           │
│       │         │         │         │               │           │
│       │         └─────────┴─────────┘               │           │
│       │              [Logo]   2024.01.13            │           │
│       │                                             │           │
│       └─────────────────────────────────────────────┘           │
│                     ↑ Composite Preview                         │
│                                                                 │
│       Tap photo to retake / 사진을 탭하여 다시 찍기              │
│                                                                 │
│  ┌─────────┬─────────┬─────────┬─────────┐                     │
│  │  [1]    │  [2]    │  [3]    │  [4]    │ ← Tappable          │
│  │ thumb   │ thumb   │ thumb   │ thumb   │   thumbnails        │
│  └─────────┴─────────┴─────────┴─────────┘                     │
│                                                                 │
│                    Number of Copies                             │
│                       인쇄 매수                                  │
│                                                                 │
│               [−]      ⟨ 1 ⟩      [+]                           │
│                                                                 │
│                                                                 │
│  ┌────────────────┐                    ┌────────────────────┐   │
│  │  🏠 Home       │                    │  🖨️ Print          │   │
│  │     처음으로    │                    │     인쇄하기        │   │
│  └────────────────┘                    └────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Thumbnail Interaction States

```
Normal State:           Hover/Focus State:      Retaking State:
┌─────────┐             ┌─────────┐             ┌─────────┐
│         │             │▓▓▓▓▓▓▓▓▓│             │░░░░░░░░░│
│  Photo  │             │▓ Photo ▓│             │░ Retake ░│
│         │             │▓▓▓▓▓▓▓▓▓│             │░░░░░░░░░│
└─────────┘             └─────────┘             └─────────┘
  Gray border           Blue border               Pulsing
                        + overlay hint            dashed border
```

### Copy Selector Component

```
┌───────────────────────────────────────────┐
│                                           │
│      ┌─────┐    ┌─────────┐    ┌─────┐   │
│      │  −  │    │    1    │    │  +  │   │
│      │     │    │  copy   │    │     │   │
│      └─────┘    └─────────┘    └─────┘   │
│                                           │
│      Disabled     Current      Enabled    │
│      at min       count        if < max   │
│                                           │
└───────────────────────────────────────────┘
```

---

## Technical Notes

### Composite Generation

```python
# Backend composite generator (ImageProcessor)

from PIL import Image
from pathlib import Path

class CompositeGenerator:
    # 4x6 inch at 300 DPI
    OUTPUT_WIDTH = 1200
    OUTPUT_HEIGHT = 1800

    # Photo grid dimensions (leaving room for logo/date)
    GRID_WIDTH = 1100
    GRID_HEIGHT = 1500
    GRID_TOP = 50
    GRID_LEFT = 50

    # Individual photo size
    PHOTO_WIDTH = 540
    PHOTO_HEIGHT = 720
    PHOTO_GAP = 20

    def generate_composite(
        self,
        photos: list[Path],
        output_path: Path,
        logo_path: Path | None,
        date_stamp: str,
        date_format: str,
    ) -> Path:
        # Create white background
        composite = Image.new('RGB', (self.OUTPUT_WIDTH, self.OUTPUT_HEIGHT), 'white')

        # Photo positions in 2x2 grid
        positions = [
            (self.GRID_LEFT, self.GRID_TOP),                                           # Top-left
            (self.GRID_LEFT + self.PHOTO_WIDTH + self.PHOTO_GAP, self.GRID_TOP),      # Top-right
            (self.GRID_LEFT, self.GRID_TOP + self.PHOTO_HEIGHT + self.PHOTO_GAP),     # Bottom-left
            (self.GRID_LEFT + self.PHOTO_WIDTH + self.PHOTO_GAP,
             self.GRID_TOP + self.PHOTO_HEIGHT + self.PHOTO_GAP),                      # Bottom-right
        ]

        # Place each photo
        for i, photo_path in enumerate(photos):
            photo = Image.open(photo_path)
            photo = self._resize_and_crop(photo, self.PHOTO_WIDTH, self.PHOTO_HEIGHT)
            composite.paste(photo, positions[i])

        # Add logo if enabled
        if logo_path and logo_path.exists():
            logo = Image.open(logo_path)
            logo = self._resize_logo(logo, max_height=100)
            logo_x = (self.OUTPUT_WIDTH - logo.width) // 2
            logo_y = self.OUTPUT_HEIGHT - 150
            composite.paste(logo, (logo_x, logo_y), logo if logo.mode == 'RGBA' else None)

        # Add date stamp
        self._add_date_stamp(composite, date_stamp, date_format)

        # Save with maximum quality
        composite.save(output_path, 'JPEG', quality=95, dpi=(300, 300))

        return output_path

    def _resize_and_crop(self, img: Image, target_w: int, target_h: int) -> Image:
        """Resize maintaining aspect ratio, then center crop."""
        # Calculate scaling
        w_ratio = target_w / img.width
        h_ratio = target_h / img.height
        ratio = max(w_ratio, h_ratio)

        # Resize
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Center crop
        left = (img.width - target_w) // 2
        top = (img.height - target_h) // 2
        return img.crop((left, top, left + target_w, top + target_h))
```

### Frontend Preview Component

```typescript
// Preview page component

interface PreviewPageProps {
  session: PhotoSession;
  onRetake: (photoIndex: number) => void;
  onPrint: (copies: number) => void;
  onHome: () => void;
}

const PreviewPage: React.FC<PreviewPageProps> = ({
  session,
  onRetake,
  onPrint,
  onHome,
}) => {
  const [copies, setCopies] = useState(1);
  const [showHomeConfirm, setShowHomeConfirm] = useState(false);
  const { t } = useTranslation();

  const MAX_COPIES = 3;

  const handleCopiesChange = (delta: number) => {
    setCopies(prev => Math.max(1, Math.min(MAX_COPIES, prev + delta)));
  };

  const handleHomeClick = () => {
    setShowHomeConfirm(true);
  };

  const handleHomeConfirm = () => {
    onHome();
  };

  return (
    <div className="preview-page">
      <Header onHome={handleHomeClick} />

      <h1 className="title">
        {t('preview.title')}
      </h1>

      {/* Composite Preview */}
      <div className="composite-preview">
        <img
          src={session.compositeUrl}
          alt="Composite preview"
          className="composite-image"
        />
      </div>

      {/* Retake hint */}
      <p className="retake-hint">
        {t('preview.retakeHint')}
      </p>

      {/* Thumbnail strip */}
      <div className="thumbnail-strip">
        {session.photos.map((photo, index) => (
          <button
            key={photo.id}
            className="thumbnail-button"
            onClick={() => onRetake(index)}
            aria-label={t('preview.retakePhoto', { number: index + 1 })}
          >
            <img src={photo.thumbnailUrl} alt={`Photo ${index + 1}`} />
            <span className="thumbnail-number">{index + 1}</span>
          </button>
        ))}
      </div>

      {/* Copy selector */}
      <div className="copy-selector">
        <span className="copy-label">{t('preview.copies')}</span>
        <div className="copy-controls">
          <button
            onClick={() => handleCopiesChange(-1)}
            disabled={copies <= 1}
            aria-label={t('preview.decreaseCopies')}
          >
            −
          </button>
          <span className="copy-count">{copies}</span>
          <button
            onClick={() => handleCopiesChange(1)}
            disabled={copies >= MAX_COPIES}
            aria-label={t('preview.increaseCopies')}
          >
            +
          </button>
        </div>
      </div>

      {/* Action buttons */}
      <div className="action-buttons">
        <Button variant="secondary" onClick={handleHomeClick}>
          <HomeIcon />
          {t('common.home')}
        </Button>
        <Button variant="primary" onClick={() => onPrint(copies)}>
          <PrintIcon />
          {t('preview.print')}
        </Button>
      </div>

      {/* Confirmation dialog */}
      <ConfirmDialog
        open={showHomeConfirm}
        title={t('preview.abandonTitle')}
        message={t('preview.abandonMessage')}
        confirmText={t('common.confirm')}
        cancelText={t('common.cancel')}
        onConfirm={handleHomeConfirm}
        onCancel={() => setShowHomeConfirm(false)}
      />
    </div>
  );
};
```

### API Endpoint

```typescript
// POST /api/session/{session_id}/composite

interface GenerateCompositeRequest {
  session_id: string;
}

interface GenerateCompositeResponse {
  success: boolean;
  composite_url: string;
  composite_path: string;
  error?: string;
}
```

---

## Related Use Cases

- **UC-002**: Capture Photo (source of photos)
- **UC-003**: Retake Photo (initiated from preview)
- **UC-005**: Submit Print Job (next step)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
