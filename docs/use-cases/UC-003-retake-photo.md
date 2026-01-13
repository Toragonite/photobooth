# UC-003: Retake Photo

## Summary

User retakes a previously captured photo by tapping on its thumbnail. The system allows replacing any individual photo without losing other captured photos.

---

## Actors

| Actor | Type | Description |
|-------|------|-------------|
| **User** | Primary | Person who wants to retake a photo |

---

## Preconditions

| ID | Condition |
|----|-----------|
| PRE-1 | Active session exists |
| PRE-2 | User is on Camera page OR Preview page |
| PRE-3 | At least one photo has been captured |
| PRE-4 | Camera is ready (if on Camera page) |

---

## Trigger

User taps on a captured photo's thumbnail.

---

## Main Flow

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Step                                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ User taps on a thumbnail showing a captured photo              │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ System displays confirmation dialog:                           │
│     │ - "Retake this photo?" / "이 사진을 다시 찍으시겠습니까?"         │
│     │ - Shows the selected photo                                     │
│     │ - [Cancel] [Retake] buttons                                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ User taps [Retake]                                             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4   │ System marks the photo slot for replacement:                   │
│     │ - Sets target_index = tapped photo's index                     │
│     │ - Thumbnail shows "retaking" state (pulsing border)            │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5   │ If on Preview page:                                            │
│     │ - Navigate to Camera page                                      │
│     │ - Session status changes from COMPLETE to ACTIVE               │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6   │ Camera page shows retake mode indicator:                       │
│     │ - "Retaking photo 2" / "사진 2 다시 찍기"                       │
│     │ - Target thumbnail highlighted                                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7   │ User captures new photo (UC-002 flow)                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8   │ System replaces photo at target_index:                         │
│     │ - Removes old photo from session                               │
│     │ - Adds new photo at same index                                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 9   │ If session now has 4 photos:                                   │
│     │ - Session status → COMPLETE                                    │
│     │ - Navigate to Preview page                                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ 10  │ If session has < 4 photos:                                     │
│     │ - Clear retake mode                                            │
│     │ - Continue normal capture flow                                 │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Alternative Flows

### AF-1: Cancel Retake

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 3a  │ User taps [Cancel] on confirmation dialog                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3b  │ System dismisses dialog                                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3c  │ No changes to session                                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3d  │ User remains on current page                                  │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-2: Cancel During Retake Capture

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 7a  │ User taps Home button during retake mode                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7b  │ System shows warning: "Abandon session?"                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7c  │ If confirmed: Navigate home, session abandoned                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7d  │ If cancelled: Remain in retake mode                           │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-3: Retake From Preview Page

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 5a  │ User initiated retake from Preview page                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5b  │ Session status: COMPLETE → ACTIVE                             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5c  │ Navigate to Camera page with retake mode active               │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5d  │ After capture, auto-return to Preview (since was complete)    │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Exception Flows

### EX-1: Camera Not Ready

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Camera initialization fails when entering retake mode         │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ System shows camera error (see UC-002 EX-1)                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Retake mode is cleared                                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ If came from Preview: Navigate back to Preview                │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Postconditions

| ID | Condition |
|----|-----------|
| POST-1 | Photo at target index replaced with new capture |
| POST-2 | Other photos unchanged |
| POST-3 | Session photo count unchanged |
| POST-4 | Retake mode cleared |

---

## Business Rules

| ID | Rule |
|----|------|
| RET-BR-1 | Any captured photo can be retaken |
| RET-BR-2 | Retake replaces at same index (preserves order) |
| RET-BR-3 | Session with 4 photos returns to COMPLETE after retake |
| RET-BR-4 | Retake requires confirmation dialog |
| RET-BR-5 | Only one photo can be retaken at a time |

---

## UI/UX Requirements

### Retake Confirmation Dialog

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│          ┌───────────────────────────────┐                      │
│          │                               │                      │
│          │      [Selected Photo]         │                      │
│          │                               │                      │
│          └───────────────────────────────┘                      │
│                                                                 │
│              Retake this photo?                                 │
│           이 사진을 다시 찍으시겠습니까?                          │
│                                                                 │
│      ┌────────────┐          ┌────────────────┐                │
│      │   Cancel   │          │    Retake      │                │
│      │   취소      │          │    다시 찍기    │                │
│      └────────────┘          └────────────────┘                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Retake Mode Indicator

```
┌─────────────────────────────────────────────────────────────────┐
│  [🏠]              ↓ Retake indicator                           │
│            ┌──────────────────────────┐                         │
│            │ 🔄 Retaking Photo 2      │                         │
│            │    사진 2 다시 찍기       │                         │
│            └──────────────────────────┘                         │
│                                                                 │
│  ┌───────┬───────┬───────┬───────┐                              │
│  │  ✅   │ 🔄    │  ✅   │  ✅   │  ← Index 1 highlighted       │
│  │ [img] │TARGET │ [img] │ [img] │     with pulsing border      │
│  └───────┴───────┴───────┴───────┘                              │
│                                                                 │
│        ... camera preview and capture button ...                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technical Notes

```typescript
// Session context retake handling

interface SessionState {
  photos: CapturedPhoto[];
  retakeMode: {
    active: boolean;
    targetIndex: number | null;
    returnToPreview: boolean;  // Was session complete when retake started?
  };
}

const retakePhoto = (index: number) => {
  setState(prev => ({
    ...prev,
    retakeMode: {
      active: true,
      targetIndex: index,
      returnToPreview: prev.status === 'complete',
    },
    status: 'active',  // Revert to active if was complete
  }));
};

const handleCaptureComplete = (photo: CapturedPhoto) => {
  setState(prev => {
    if (prev.retakeMode.active) {
      // Replace photo at target index
      const newPhotos = prev.photos.map(p =>
        p.index === prev.retakeMode.targetIndex
          ? { ...photo, index: prev.retakeMode.targetIndex }
          : p
      );

      return {
        ...prev,
        photos: newPhotos,
        retakeMode: { active: false, targetIndex: null, returnToPreview: false },
        status: newPhotos.length === 4 ? 'complete' : 'active',
      };
    }
    // Normal capture flow...
  });
};
```

---

## Related Use Cases

- **UC-002**: Capture Photo (invoked for new capture)
- **UC-004**: Preview Composite (return destination if was complete)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
