# UI Style Guide

> Visual design specifications for PhotoBooth application

---

## Brand Identity

### Color Palette - Rwanda Flag Inspired

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| **Sky Blue** (Primary) | `#00A1DE` | rgb(0, 161, 222) | Primary buttons, headers, accents |
| **Green** (Secondary) | `#20603D` | rgb(32, 96, 61) | Success states, secondary elements |
| **Yellow** (Accent) | `#FAD201` | rgb(250, 210, 1) | Highlights, warnings, sun icon |
| **White** | `#FFFFFF` | rgb(255, 255, 255) | Backgrounds, text on dark |
| **Dark Gray** | `#333333` | rgb(51, 51, 51) | Primary text |
| **Light Gray** | `#F5F5F5` | rgb(245, 245, 245) | Card backgrounds |
| **Error Red** | `#DC3545` | rgb(220, 53, 69) | Error states, destructive actions |

### CSS Variables

```css
:root {
  /* Primary colors */
  --color-primary: #00A1DE;
  --color-primary-hover: #0089BE;
  --color-primary-active: #007AA8;

  /* Secondary colors */
  --color-secondary: #20603D;
  --color-secondary-hover: #1A4F32;
  --color-secondary-active: #154027;

  /* Accent */
  --color-accent: #FAD201;
  --color-accent-hover: #E0BC01;

  /* Semantic colors */
  --color-success: #20603D;
  --color-warning: #FAD201;
  --color-error: #DC3545;
  --color-info: #00A1DE;

  /* Neutrals */
  --color-white: #FFFFFF;
  --color-background: #F5F5F5;
  --color-surface: #FFFFFF;
  --color-text-primary: #333333;
  --color-text-secondary: #666666;
  --color-text-disabled: #999999;
  --color-border: #E0E0E0;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);

  /* Border radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 16px;
  --radius-full: 9999px;

  /* Spacing */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;

  /* Typography */
  --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans KR', sans-serif;
  --font-size-xs: 12px;
  --font-size-sm: 14px;
  --font-size-md: 16px;
  --font-size-lg: 18px;
  --font-size-xl: 24px;
  --font-size-2xl: 32px;
  --font-size-3xl: 48px;

  /* Line heights */
  --line-height-tight: 1.25;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.75;

  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-normal: 250ms ease;
  --transition-slow: 350ms ease;
}
```

---

## Typography

### Font Stack

```css
/* Primary font */
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans KR', sans-serif;

/* Korean support via Noto Sans KR */
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
```

### Type Scale

| Style | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| Display | 48px | 700 | 1.2 | Hero text |
| Heading 1 | 32px | 700 | 1.25 | Page titles |
| Heading 2 | 24px | 600 | 1.3 | Section titles |
| Heading 3 | 18px | 600 | 1.4 | Card titles |
| Body Large | 18px | 400 | 1.5 | Instructions |
| Body | 16px | 400 | 1.5 | Default text |
| Body Small | 14px | 400 | 1.5 | Secondary text |
| Caption | 12px | 400 | 1.4 | Labels, hints |

### Typography Components

```css
.display {
  font-size: 48px;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.02em;
}

.h1 {
  font-size: 32px;
  font-weight: 700;
  line-height: 1.25;
}

.h2 {
  font-size: 24px;
  font-weight: 600;
  line-height: 1.3;
}

.body-large {
  font-size: 18px;
  font-weight: 400;
  line-height: 1.5;
}

.body {
  font-size: 16px;
  font-weight: 400;
  line-height: 1.5;
}

.caption {
  font-size: 12px;
  font-weight: 400;
  line-height: 1.4;
  color: var(--color-text-secondary);
}
```

---

## Components

### Buttons

#### Primary Button

```
┌─────────────────────────────────────┐
│          Start Session              │  Sky Blue bg
│           시작하기                   │  White text
└─────────────────────────────────────┘
```

```css
.btn-primary {
  background-color: var(--color-primary);
  color: var(--color-white);
  padding: 16px 32px;
  border-radius: var(--radius-md);
  font-size: 18px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: background-color var(--transition-fast);
  min-height: 56px;
  min-width: 200px;
}

.btn-primary:hover {
  background-color: var(--color-primary-hover);
}

.btn-primary:active {
  background-color: var(--color-primary-active);
}

.btn-primary:disabled {
  background-color: var(--color-text-disabled);
  cursor: not-allowed;
}
```

#### Secondary Button

```
┌─────────────────────────────────────┐
│            Go Back                  │  White bg
│            돌아가기                  │  Primary text
└─────────────────────────────────────┘  Primary border
```

```css
.btn-secondary {
  background-color: var(--color-white);
  color: var(--color-primary);
  padding: 16px 32px;
  border-radius: var(--radius-md);
  font-size: 18px;
  font-weight: 600;
  border: 2px solid var(--color-primary);
  cursor: pointer;
  transition: all var(--transition-fast);
  min-height: 56px;
}

.btn-secondary:hover {
  background-color: var(--color-primary);
  color: var(--color-white);
}
```

#### Destructive Button

```css
.btn-destructive {
  background-color: var(--color-error);
  color: var(--color-white);
  padding: 16px 32px;
  border-radius: var(--radius-md);
  font-size: 18px;
  font-weight: 600;
  border: none;
}

.btn-destructive:hover {
  background-color: #C82333;
}
```

#### Icon Button

```css
.btn-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: transparent;
  border: none;
  cursor: pointer;
}

.btn-icon:hover {
  background-color: rgba(0, 0, 0, 0.05);
}
```

### Cards

```
┌─────────────────────────────────────────┐
│                                         │
│  ┌─────────────────────────────────┐    │
│  │                                 │    │
│  │         Photo Content           │    │
│  │                                 │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Card Title                             │
│  Card description text                  │
│                                         │
└─────────────────────────────────────────┘
```

```css
.card {
  background-color: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  padding: var(--space-6);
  transition: box-shadow var(--transition-normal);
}

.card:hover {
  box-shadow: var(--shadow-lg);
}

.card-elevated {
  box-shadow: var(--shadow-lg);
}
```

### Photo Thumbnail

```css
.photo-thumbnail {
  width: 150px;
  height: 200px;
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 3px solid transparent;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.photo-thumbnail:hover {
  border-color: var(--color-primary);
  transform: scale(1.02);
}

.photo-thumbnail.selected {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(0, 161, 222, 0.3);
}

.photo-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
```

### Progress Indicators

#### Linear Progress

```
████████████░░░░░░░░░░░░  50%
```

```css
.progress-bar {
  width: 100%;
  height: 8px;
  background-color: var(--color-border);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background-color: var(--color-primary);
  border-radius: var(--radius-full);
  transition: width var(--transition-normal);
}
```

#### Circular Progress (Countdown)

```css
.countdown-circle {
  width: 200px;
  height: 200px;
  border-radius: 50%;
  background: conic-gradient(
    var(--color-primary) calc(var(--progress) * 360deg),
    var(--color-border) 0deg
  );
  display: flex;
  align-items: center;
  justify-content: center;
}

.countdown-number {
  font-size: 72px;
  font-weight: 700;
  color: var(--color-text-primary);
}
```

### Dialogs/Modals

```
┌───────────────────────────────────────────────┐
│                                               │
│                  Dialog Title                 │
│                                               │
│       Dialog message content goes here        │
│       with supporting information.            │
│                                               │
│     ┌─────────────┐   ┌─────────────────┐     │
│     │   Cancel    │   │    Confirm      │     │
│     └─────────────┘   └─────────────────┘     │
│                                               │
└───────────────────────────────────────────────┘
```

```css
.dialog-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background-color: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-8);
  max-width: 400px;
  width: 90%;
  box-shadow: var(--shadow-lg);
}

.dialog-title {
  font-size: 24px;
  font-weight: 600;
  text-align: center;
  margin-bottom: var(--space-4);
}

.dialog-message {
  font-size: 16px;
  text-align: center;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-6);
}

.dialog-actions {
  display: flex;
  gap: var(--space-4);
  justify-content: center;
}
```

### Toast Notifications

```css
.toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  padding: 16px 24px;
  border-radius: var(--radius-md);
  color: var(--color-white);
  font-weight: 500;
  box-shadow: var(--shadow-lg);
  z-index: 1100;
  animation: slideUp 0.3s ease;
}

.toast-success {
  background-color: var(--color-success);
}

.toast-error {
  background-color: var(--color-error);
}

.toast-warning {
  background-color: var(--color-warning);
  color: var(--color-text-primary);
}

@keyframes slideUp {
  from {
    transform: translateX(-50%) translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateX(-50%) translateY(0);
    opacity: 1;
  }
}
```

---

## Layout

### Screen Dimensions

Target device: iPad Air (10.9")
- Portrait: 820 x 1180 (CSS pixels)
- Landscape: 1180 x 820 (CSS pixels)

**Design for portrait orientation.**

### Grid System

```css
.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 var(--space-6);
}

.grid {
  display: grid;
  gap: var(--space-4);
}

.grid-2 {
  grid-template-columns: repeat(2, 1fr);
}

.grid-4 {
  grid-template-columns: repeat(4, 1fr);
}
```

### Page Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Header (fixed)                                    h: 64px  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                                                             │
│                      Main Content                           │
│                    (scrollable area)                        │
│                                                             │
│                                                             │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Footer/Actions (fixed)                           h: 100px  │
└─────────────────────────────────────────────────────────────┘
```

```css
.page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--color-background);
}

.page-header {
  height: 64px;
  padding: 0 var(--space-6);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 100;
}

.page-content {
  flex: 1;
  padding: var(--space-6);
  overflow-y: auto;
}

.page-footer {
  padding: var(--space-6);
  background-color: var(--color-surface);
  border-top: 1px solid var(--color-border);
}
```

---

## Icons

### Icon System

Use Lucide React icons for consistency.

```bash
npm install lucide-react
```

### Common Icons

| Icon | Usage | Import |
|------|-------|--------|
| Home | Home button | `Home` |
| Camera | Capture | `Camera` |
| RotateCcw | Retake | `RotateCcw` |
| Printer | Print | `Printer` |
| Check | Success | `Check` |
| X | Close/Error | `X` |
| AlertTriangle | Warning | `AlertTriangle` |
| Settings | Settings | `Settings` |
| Globe | Language | `Globe` |
| ChevronLeft | Back | `ChevronLeft` |
| Plus/Minus | Count | `Plus`, `Minus` |

### Icon Sizes

| Size | Pixels | Usage |
|------|--------|-------|
| sm | 16px | Inline text |
| md | 24px | Buttons, UI elements |
| lg | 32px | Feature icons |
| xl | 48px | Hero icons |

```tsx
import { Camera } from 'lucide-react';

<Camera size={24} strokeWidth={2} />
```

---

## Animation

### Transitions

```css
/* Default transition for interactive elements */
.interactive {
  transition: all 150ms ease;
}

/* Page transitions */
.page-enter {
  opacity: 0;
  transform: translateX(20px);
}

.page-enter-active {
  opacity: 1;
  transform: translateX(0);
  transition: all 300ms ease;
}
```

### Flash Effect (Photo Capture)

```css
@keyframes flash {
  0% {
    opacity: 0;
  }
  50% {
    opacity: 1;
  }
  100% {
    opacity: 0;
  }
}

.flash-overlay {
  position: fixed;
  inset: 0;
  background-color: white;
  pointer-events: none;
  animation: flash 200ms ease-out;
}
```

### Pulse (Active/Recording)

```css
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.recording-indicator {
  animation: pulse 1.5s ease-in-out infinite;
}
```

### Spin (Loading)

```css
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.spinner {
  animation: spin 1s linear infinite;
}
```

---

## Accessibility

### Touch Targets

- Minimum touch target: 44x44 pixels
- Recommended: 48x48 pixels for primary actions

### Color Contrast

| Text Type | Background | Ratio |
|-----------|------------|-------|
| Primary text | White | 12.6:1 |
| White text | Primary blue | 4.8:1 |
| White text | Secondary green | 7.2:1 |

### Focus States

```css
.focusable:focus-visible {
  outline: 3px solid var(--color-primary);
  outline-offset: 2px;
}

/* Remove default outline when using custom */
.focusable:focus {
  outline: none;
}
```

### Screen Reader

```tsx
// Visually hidden but accessible
<span className="sr-only">
  Photo 1 of 4 captured
</span>

// CSS
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
```

---

## Bilingual Support

### Text Wrapper Component

```tsx
interface BilingualTextProps {
  ko: string;
  en: string;
  className?: string;
}

const BilingualText: React.FC<BilingualTextProps> = ({ ko, en, className }) => {
  const { language } = useLanguage();

  return (
    <span className={className}>
      {language === 'ko' ? ko : en}
    </span>
  );
};

// Usage
<BilingualText
  ko="시작하기"
  en="Start"
/>
```

### Stacked Display (Both Languages)

```
┌─────────────────────────────────────┐
│          Start Session              │  English (primary)
│            시작하기                  │  Korean (secondary)
└─────────────────────────────────────┘
```

```css
.bilingual-stack {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.bilingual-primary {
  font-size: 18px;
  font-weight: 600;
}

.bilingual-secondary {
  font-size: 14px;
  font-weight: 400;
  color: var(--color-text-secondary);
}
```

---

## Dark Mode (Future)

Reserved CSS variables for potential dark mode:

```css
:root.dark {
  --color-background: #1A1A1A;
  --color-surface: #2D2D2D;
  --color-text-primary: #FFFFFF;
  --color-text-secondary: #B0B0B0;
  --color-border: #404040;
}
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
