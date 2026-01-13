# UC-009: Change Language

## Summary

User switches the interface language between Korean and English. The change applies immediately to all UI text and persists for the current session.

---

## Actors

| Actor | Type | Description |
|-------|------|-------------|
| **User** | Primary | Person changing language preference |
| **System** | Secondary | Updates UI language |

---

## Preconditions

| ID | Condition |
|----|-----------|
| PRE-1 | Application is loaded |
| PRE-2 | Language toggle is visible on current screen |

---

## Trigger

User taps language toggle button in header.

---

## Main Flow

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Step                                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ User sees language toggle in header:                          │
│     │ - Shows current language icon (🇰🇷 or 🇬🇧)                      │
│     │ - Or text: "한국어" / "English"                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ User taps language toggle                                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ System switches to other language:                            │
│     │ - Korean → English                                            │
│     │ - English → Korean                                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4   │ All UI text updates immediately:                              │
│     │ - Buttons, labels, headings                                   │
│     │ - Error messages                                              │
│     │ - Instructions                                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5   │ Language preference stored in session state                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6   │ Toggle icon/text updates to show new current language         │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Alternative Flows

### AF-1: Language Selection Dropdown (Optional Enhancement)

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 2a  │ User taps language button                                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2b  │ Dropdown appears with language options:                       │
│     │ - 🇰🇷 한국어                                                   │
│     │ - 🇬🇧 English                                                  │
│     │ - (Future: 🇫🇷 Français, etc.)                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2c  │ User selects language                                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2d  │ Dropdown closes, continue from step 3                         │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-2: Change During Photo Flow

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 1a  │ User is in middle of photo capture session                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2a  │ Language toggle still accessible in header                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3a  │ Language changes without affecting session state              │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4a  │ User continues session in new language                        │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Exception Flows

### EX-1: Translation Missing

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Some text key has no translation for selected language        │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ System falls back to default language (Korean)                │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Log warning for developers                                    │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Postconditions

| ID | Condition |
|----|-----------|
| POST-1 | All UI displays in selected language |
| POST-2 | Language preference stored for session |
| POST-3 | User can continue current flow |

---

## Business Rules

| ID | Rule |
|----|------|
| LANG-BR-1 | Default language: Korean (한국어) |
| LANG-BR-2 | Supported languages: Korean, English |
| LANG-BR-3 | Language toggle visible on ALL screens except printing |
| LANG-BR-4 | Language change does not reset session state |
| LANG-BR-5 | Language resets to default on new session |

---

## UI/UX Requirements

### Toggle Button Designs

**Option A: Flag Icon Toggle**
```
┌──────┐
│ 🇰🇷  │  ← Current: Korean, tap to switch to English
└──────┘

┌──────┐
│ 🇬🇧  │  ← Current: English, tap to switch to Korean
└──────┘
```

**Option B: Text Toggle**
```
┌──────────┐
│ English  │  ← Tap to switch to English (currently Korean)
└──────────┘

┌──────────┐
│ 한국어   │  ← Tap to switch to Korean (currently English)
└──────────┘
```

**Option C: Globe Icon with Current**
```
┌────────────┐
│ 🌐 한국어  │
└────────────┘
```

### Header Integration

```
┌─────────────────────────────────────────────────────────────────┐
│  [🏠 Home]                                          [🇰🇷 한국어] │
│                                                                 │
│                      Welcome!                                   │
│                     환영합니다!                                  │
│                                                                 │
│                  (Page content)                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### During Printing (Toggle Hidden)

```
┌─────────────────────────────────────────────────────────────────┐
│                           (no header)                           │
│                                                                 │
│                       Printing...                               │
│                        인쇄 중...                                │
│                                                                 │
│   ← Language toggle NOT shown during print (prevents confusion) │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technical Notes

### i18n Implementation

```typescript
// i18n configuration with react-i18next

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

// Translation resources
const resources = {
  ko: {
    translation: {
      // Home
      'home.title': '환영합니다!',
      'home.subtitle': '사진을 찍어보세요',
      'home.startButton': '시작하기',

      // Camera
      'camera.title': '사진 {{current}}/{{total}}',
      'camera.countdown': '{{seconds}}',
      'camera.ready': '준비',
      'camera.capture': '촬영',

      // Preview
      'preview.title': '사진이 준비되었습니다!',
      'preview.retakeHint': '사진을 탭하여 다시 찍기',
      'preview.copies': '인쇄 매수',
      'preview.print': '인쇄하기',

      // Print
      'print.printing': '인쇄 중...',
      'print.complete': '인쇄 완료!',
      'print.failed': '인쇄 실패',
      'print.retry': '다시 시도',
      'print.cancel': '취소',

      // Common
      'common.home': '처음으로',
      'common.back': '뒤로',
      'common.confirm': '확인',
      'common.cancel': '취소',

      // Errors
      'error.printerOffline': '프린터가 오프라인입니다',
      'error.paperEmpty': '용지를 확인해주세요',
      'error.networkError': '네트워크 오류가 발생했습니다',
    },
  },
  en: {
    translation: {
      // Home
      'home.title': 'Welcome!',
      'home.subtitle': 'Take your photos',
      'home.startButton': 'Start',

      // Camera
      'camera.title': 'Photo {{current}}/{{total}}',
      'camera.countdown': '{{seconds}}',
      'camera.ready': 'Ready',
      'camera.capture': 'Capture',

      // Preview
      'preview.title': 'Your Photos Are Ready!',
      'preview.retakeHint': 'Tap photo to retake',
      'preview.copies': 'Number of Copies',
      'preview.print': 'Print',

      // Print
      'print.printing': 'Printing...',
      'print.complete': 'Print Complete!',
      'print.failed': 'Print Failed',
      'print.retry': 'Retry',
      'print.cancel': 'Cancel',

      // Common
      'common.home': 'Home',
      'common.back': 'Back',
      'common.confirm': 'Confirm',
      'common.cancel': 'Cancel',

      // Errors
      'error.printerOffline': 'Printer is offline',
      'error.paperEmpty': 'Please check paper',
      'error.networkError': 'Network error occurred',
    },
  },
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: 'ko', // Default language
    fallbackLng: 'ko',
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
```

### Language Context

```typescript
// Language context for app-wide state

import { createContext, useContext, useState, ReactNode } from 'react';
import i18n from './i18n';

type Language = 'ko' | 'en';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  toggleLanguage: () => void;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>('ko');

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    i18n.changeLanguage(lang);
  };

  const toggleLanguage = () => {
    const newLang = language === 'ko' ? 'en' : 'ko';
    setLanguage(newLang);
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, toggleLanguage }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within LanguageProvider');
  }
  return context;
};
```

### Language Toggle Component

```typescript
// Language toggle button component

import { useLanguage } from '../contexts/LanguageContext';

interface LanguageToggleProps {
  variant?: 'icon' | 'text' | 'full';
}

const LanguageToggle: React.FC<LanguageToggleProps> = ({ variant = 'full' }) => {
  const { language, toggleLanguage } = useLanguage();

  const getLabel = () => {
    switch (variant) {
      case 'icon':
        return language === 'ko' ? '🇰🇷' : '🇬🇧';
      case 'text':
        return language === 'ko' ? 'English' : '한국어';
      case 'full':
      default:
        return language === 'ko' ? '🇰🇷 한국어' : '🇬🇧 English';
    }
  };

  return (
    <button
      className="language-toggle"
      onClick={toggleLanguage}
      aria-label={`Switch to ${language === 'ko' ? 'English' : 'Korean'}`}
    >
      {getLabel()}
    </button>
  );
};

// Usage in Header
const Header: React.FC<{ showLanguage?: boolean }> = ({ showLanguage = true }) => {
  return (
    <header className="app-header">
      <HomeButton />
      {showLanguage && <LanguageToggle />}
    </header>
  );
};
```

### CSS Styling

```css
/* Language toggle styles */

.language-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: inherit;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.language-toggle:hover {
  background: rgba(255, 255, 255, 0.2);
}

.language-toggle:active {
  transform: scale(0.98);
}

/* Responsive sizing */
@media (max-width: 768px) {
  .language-toggle {
    padding: 0.75rem;
    font-size: 1.25rem;
  }
}
```

---

## Translation Keys Structure

```
translation/
├── ko.json
│   ├── home.*
│   ├── camera.*
│   ├── preview.*
│   ├── print.*
│   ├── admin.*
│   ├── common.*
│   └── error.*
└── en.json
    └── (same structure)
```

---

## Related Use Cases

- **UC-001**: Start Photo Session (language shown on home)
- **UC-101**: Admin Login (admin also has language toggle)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
