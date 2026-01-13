# UC-010: Return to Home

## Summary

User navigates back to the home screen from any point in the application. Depending on the current state, this may require confirmation if there's an active session with unsaved progress.

---

## Actors

| Actor | Type | Description |
|-------|------|-------------|
| **User** | Primary | Person navigating home |
| **System** | Secondary | Handles navigation and cleanup |

---

## Preconditions

| ID | Condition |
|----|-----------|
| PRE-1 | User is not on home screen |
| PRE-2 | Home button is visible (not during active printing) |

---

## Trigger

User taps Home button (🏠) in header.

---

## Main Flow (No Active Session)

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Step                                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ User is on a screen with no active session:                   │
│     │ - Print completed screen                                      │
│     │ - Error screen after session ended                            │
│     │ - Admin dashboard                                             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ User taps Home button                                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ Navigate directly to Home screen                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4   │ Home screen displays welcome message                          │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Alternative Flow: Active Session (With Photos)

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Step                                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ User is in photo session (has captured 1+ photos)             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ User taps Home button                                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ System shows confirmation dialog:                             │
│     │ "Abandon current session?"                                    │
│     │ "현재 세션을 포기하시겠습니까?"                                 │
│     │                                                               │
│     │ "Your photos will be lost."                                   │
│     │ "사진을 잃게 됩니다."                                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4   │ User confirms                                                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5   │ System marks session as ABANDONED                             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6   │ Navigate to Home screen                                       │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Alternative Flow: User Cancels

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 4a  │ User taps "Stay" / "Cancel" on confirmation                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4b  │ Dialog closes                                                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4c  │ User remains on current screen                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4d  │ Session continues as normal                                   │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Alternative Flow: During Printing

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 1a  │ User is on print progress screen                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2a  │ Home button is HIDDEN during active printing                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2b  │ Only "Cancel Print" button available (UC-008)                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2c  │ After print completes: Home button reappears                  │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Alternative Flow: From Admin Dashboard

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 1a  │ Admin is on dashboard                                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2a  │ Admin taps Home button                                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3a  │ System shows confirmation:                                    │
│     │ "Return to photo booth mode?"                                 │
│     │ "You will be logged out of admin."                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4a  │ Admin confirms                                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5a  │ Admin session ends (JWT cleared)                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6a  │ Navigate to Home screen                                       │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Exception Flows

### EX-1: Session Cleanup Fails

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Backend fails to mark session as abandoned                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Log error                                                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Navigate to Home anyway (don't block user)                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ Session will be cleaned up by background process              │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Postconditions

| ID | Condition |
|----|-----------|
| POST-1 | User is on Home screen |
| POST-2 | Any active session marked as ABANDONED |
| POST-3 | Frontend state is reset |
| POST-4 | Ready for new session |

---

## Business Rules

| ID | Rule |
|----|------|
| HOME-BR-1 | Home button visible on all screens except during printing |
| HOME-BR-2 | Confirmation required if session has photos |
| HOME-BR-3 | No confirmation needed after print complete |
| HOME-BR-4 | Admin logout on return to user mode |
| HOME-BR-5 | Navigation should never be blocked by errors |

---

## UI/UX Requirements

### Home Button Placement

```
Standard Header:
┌─────────────────────────────────────────────────────────────────┐
│  ┌──────────┐                                    ┌───────────┐  │
│  │ 🏠 Home  │                                    │ 🇰🇷 한국어 │  │
│  └──────────┘                                    └───────────┘  │
│                                                                 │
│                      (Page content)                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

During Printing (Home Hidden):
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                       Printing...                               │
│                        인쇄 중...                                │
│                                                                 │
│                    ████████████░░░░  75%                        │
│                                                                 │
│                    [Cancel Print]                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Confirmation Dialog

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│     ┌─────────────────────────────────────────────────────┐     │
│     │                                                     │     │
│     │              Abandon Session?                       │     │
│     │              세션을 포기하시겠습니까?                │     │
│     │                                                     │     │
│     │   Your {{photoCount}} photos will not be saved.     │     │
│     │   {{photoCount}}장의 사진이 저장되지 않습니다.      │     │
│     │                                                     │     │
│     │   ┌──────────────┐     ┌──────────────────┐         │     │
│     │   │    Stay      │     │   Go Home        │         │     │
│     │   │   계속하기    │     │   홈으로 가기     │         │     │
│     │   └──────────────┘     └──────────────────┘         │     │
│     │                                                     │     │
│     └─────────────────────────────────────────────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Home Button States

```
Normal:             Hover/Focus:         Hidden (Printing):
┌──────────┐        ┌──────────┐
│ 🏠 Home  │        │ 🏠 Home  │         (not rendered)
└──────────┘        └──────────┘
 Default bg          Highlighted
```

---

## Technical Notes

### Navigation Logic

```typescript
// Home navigation hook

import { useNavigate, useLocation } from 'react-router-dom';
import { useSession } from '../contexts/SessionContext';
import { useAuth } from '../contexts/AuthContext';

interface UseHomeNavigationReturn {
  canGoHome: boolean;
  needsConfirmation: boolean;
  goHome: () => void;
  confirmAndGoHome: () => Promise<void>;
}

const useHomeNavigation = (): UseHomeNavigationReturn => {
  const navigate = useNavigate();
  const location = useLocation();
  const { session, abandonSession, clearSession } = useSession();
  const { isAdmin, logout } = useAuth();

  // Can't go home during printing
  const isPrinting = location.pathname === '/print' &&
                     session?.printJob?.status === 'PRINTING';
  const canGoHome = !isPrinting;

  // Need confirmation if session has photos
  const hasPhotos = (session?.photos?.length ?? 0) > 0;
  const needsConfirmation = hasPhotos || isAdmin;

  const goHome = () => {
    clearSession();
    if (isAdmin) {
      logout();
    }
    navigate('/', { replace: true });
  };

  const confirmAndGoHome = async () => {
    if (session?.id && hasPhotos) {
      try {
        await abandonSession(session.id);
      } catch (error) {
        // Log but don't block navigation
        console.error('Failed to abandon session:', error);
      }
    }
    goHome();
  };

  return {
    canGoHome,
    needsConfirmation,
    goHome,
    confirmAndGoHome,
  };
};
```

### Home Button Component

```typescript
// Home button with confirmation logic

interface HomeButtonProps {
  className?: string;
}

const HomeButton: React.FC<HomeButtonProps> = ({ className }) => {
  const [showConfirm, setShowConfirm] = useState(false);
  const { canGoHome, needsConfirmation, goHome, confirmAndGoHome } = useHomeNavigation();
  const { session } = useSession();
  const { t } = useTranslation();

  if (!canGoHome) {
    return null; // Don't render during printing
  }

  const handleClick = () => {
    if (needsConfirmation) {
      setShowConfirm(true);
    } else {
      goHome();
    }
  };

  const handleConfirm = async () => {
    await confirmAndGoHome();
    setShowConfirm(false);
  };

  return (
    <>
      <button
        className={`home-button ${className ?? ''}`}
        onClick={handleClick}
        aria-label={t('common.home')}
      >
        <HomeIcon />
        <span>{t('common.home')}</span>
      </button>

      <ConfirmDialog
        open={showConfirm}
        title={t('home.abandonTitle')}
        message={t('home.abandonMessage', {
          photoCount: session?.photos?.length ?? 0
        })}
        confirmText={t('home.goHome')}
        cancelText={t('home.stay')}
        onConfirm={handleConfirm}
        onCancel={() => setShowConfirm(false)}
        destructive
      />
    </>
  );
};
```

### Backend Abandon Endpoint

```python
# Abandon session endpoint

@router.post("/session/{session_id}/abandon")
async def abandon_session(
    session_id: str,
    session_repo: SessionRepository = Depends(get_session_repo),
):
    """Mark a session as abandoned."""
    session = await session_repo.get_by_id(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Already terminal state
    if session.status in (SessionStatus.COMPLETED, SessionStatus.ABANDONED):
        return {"success": True, "status": session.status.value}

    # Mark as abandoned
    session.status = SessionStatus.ABANDONED
    session.abandoned_at = datetime.utcnow()
    await session_repo.update(session)

    logger.info(
        f"Session {session_id} abandoned",
        extra={
            'session_id': session_id,
            'photo_count': len(session.photos),
        }
    )

    return {"success": True, "status": "ABANDONED"}
```

### CSS Styling

```css
/* Home button styles */

.home-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 1rem;
  cursor: pointer;
  border-radius: 8px;
  transition: background 0.2s ease;
}

.home-button:hover {
  background: rgba(0, 0, 0, 0.1);
}

.home-button:active {
  background: rgba(0, 0, 0, 0.2);
}

.home-button svg {
  width: 1.5rem;
  height: 1.5rem;
}

/* Large touch target for tablet */
@media (max-width: 1024px) {
  .home-button {
    padding: 0.75rem 1.25rem;
    font-size: 1.125rem;
  }

  .home-button svg {
    width: 1.75rem;
    height: 1.75rem;
  }
}
```

---

## Screen Visibility Matrix

| Screen | Home Button | Confirmation |
|--------|-------------|--------------|
| Home | Hidden (already home) | - |
| Camera (no photos) | Visible | No |
| Camera (has photos) | Visible | Yes |
| Preview | Visible | Yes |
| Printing (active) | **Hidden** | - |
| Print Complete | Visible | No |
| Print Failed | Visible | No (via Cancel) |
| Admin Dashboard | Visible | Yes (logout) |

---

## Related Use Cases

- **UC-001**: Start Photo Session (destination)
- **UC-008**: Abort Print Job (alternative during print)
- **UC-101**: Admin Login (admin logout on home)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
