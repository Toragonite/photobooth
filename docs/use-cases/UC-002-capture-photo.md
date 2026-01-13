# UC-002: Capture Photo

## Summary

User captures a single photo during a photo booth session using the device camera. The system provides a countdown timer and visual/audio feedback during the capture process.

---

## Actors

| Actor | Type | Description |
|-------|------|-------------|
| **User** | Primary | Person being photographed |
| **Camera Hardware** | Secondary | Device camera (iPad) |
| **Browser** | Secondary | MediaDevices API provider |

---

## Preconditions

| ID | Condition |
|----|-----------|
| PRE-1 | Active session exists (status: ACTIVE) |
| PRE-2 | User is on Camera page |
| PRE-3 | Session has fewer than 4 photos |
| PRE-4 | Camera permission granted |
| PRE-5 | Camera hardware available and functional |

---

## Trigger

User taps the "Capture" / "촬영" button on the Camera page.

---

## Main Flow

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Step                                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ User positions themselves in camera preview                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ User taps "Capture" button                                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ System disables Capture button                                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4   │ System starts countdown timer (user-selected: 3/5/8/10 sec)    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5   │ System displays countdown number overlay on preview            │
│     │ - Large, centered number                                       │
│     │ - Decrements every second                                      │
│     │ - Optional tick sound on each decrement                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6   │ When countdown reaches 0:                                      │
│     │ - Display flash effect (white overlay, 100ms)                  │
│     │ - Play shutter sound (if enabled)                              │
│     │ - Capture frame from video stream                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7   │ System processes captured frame:                               │
│     │ - Draw video frame to canvas                                   │
│     │ - Mirror horizontally (selfie mode)                            │
│     │ - Export as JPEG (quality: 0.92)                               │
│     │ - Calculate dimensions and size                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8   │ System creates Photo entity:                                   │
│     │ - Generate photo ID                                            │
│     │ - Set index based on current session photo count               │
│     │ - Store base64 data URL                                        │
│     │ - Record capture timestamp                                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ 9   │ System adds photo to session                                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 10  │ System updates thumbnail strip:                                │
│     │ - Show captured photo in appropriate slot                      │
│     │ - Add checkmark indicator                                      │
│     │ - Animate thumbnail appearance                                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 11  │ System checks photo count:                                     │
│     │ - If < 4: Re-enable Capture button, stay on Camera page        │
│     │ - If = 4: Proceed to step 12                                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 12  │ If 4 photos captured:                                          │
│     │ - Mark session as COMPLETE                                     │
│     │ - Play success sound (if enabled)                              │
│     │ - Brief celebration animation (optional)                       │
│     │ - Navigate to Preview page after 500ms delay                   │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Alternative Flows

### AF-1: Cancel During Countdown

```
Trigger: User taps anywhere outside capture area during countdown

┌─────┬────────────────────────────────────────────────────────────────┐
│ 4a  │ User taps "Cancel" button or outside area during countdown    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4b  │ System cancels countdown timer                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4c  │ System hides countdown overlay                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4d  │ System re-enables Capture button                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4e  │ Return to ready state (no photo captured)                     │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-2: Change Countdown Duration

```
Trigger: User selects different countdown duration before capture

┌─────┬────────────────────────────────────────────────────────────────┐
│ 1a  │ User taps countdown selector (3/5/8/10)                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1b  │ System updates session settings with new duration             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1c  │ System highlights selected duration option                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1d  │ Continue with main flow using new duration                    │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-3: Toggle Sound Effects

```
Trigger: User toggles sound on/off

┌─────┬────────────────────────────────────────────────────────────────┐
│ 1a  │ User taps sound toggle button                                 │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1b  │ System updates session settings                               │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1c  │ System updates toggle visual state (🔊 ↔ 🔇)                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1d  │ Future sounds respect this setting                            │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Exception Flows

### EX-1: Camera Permission Denied

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ getUserMedia() throws NotAllowedError                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ System displays permission error screen:                      │
│     │ - Icon: 🚫📷                                                   │
│     │ - Title: "Camera access required"                             │
│     │ - Instructions for enabling camera in Settings                │
│     │ - [Try Again] button                                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ User follows instructions, taps [Try Again]                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ System re-attempts camera initialization                      │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-2: Camera Not Found

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ getUserMedia() throws NotFoundError                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ System displays hardware error screen:                        │
│     │ - Icon: ❌📷                                                   │
│     │ - Title: "No camera found"                                    │
│     │ - Message: "Please check your device has a working camera"    │
│     │ - [Go Home] button                                            │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ User cannot proceed without camera                            │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-3: Camera Stream Interrupted

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Video stream ends unexpectedly (track.onended fires)          │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ System cancels any active countdown                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ System displays reconnection message                          │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ System attempts to restart camera stream                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ E5  │ If restart succeeds: Resume normal operation                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ E6  │ If restart fails 3 times: Show error, offer [Go Home]         │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-4: Capture Processing Fails

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Canvas drawing or toDataURL fails                             │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ System shows brief error toast: "Capture failed, try again"   │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ System re-enables Capture button                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ User can retry capture                                        │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-5: Storage/Memory Full

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Browser throws quota exceeded error on photo storage          │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ System attempts to clear old session data                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ System retries storage                                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ E4  │ If still fails: Show error, suggest refreshing page           │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Postconditions

### Success

| ID | Condition |
|----|-----------|
| POST-1 | Photo added to session at correct index |
| POST-2 | Photo contains valid JPEG data |
| POST-3 | Thumbnail displays captured image |
| POST-4 | Session photo count incremented |
| POST-5 | If 4th photo: Session status is COMPLETE |
| POST-6 | If 4th photo: User is on Preview page |

### Cancelled

| ID | Condition |
|----|-----------|
| POST-C1 | No photo added to session |
| POST-C2 | Capture button re-enabled |
| POST-C3 | User remains on Camera page |

---

## Business Rules

| ID | Rule |
|----|------|
| CAP-BR-1 | Countdown must complete before capture (no skip) |
| CAP-BR-2 | Capture button disabled during countdown |
| CAP-BR-3 | Preview must be mirrored for selfie experience |
| CAP-BR-4 | Captured image must NOT be mirrored (natural orientation) |
| CAP-BR-5 | Maximum photo size: 5MB after JPEG encoding |
| CAP-BR-6 | Photo index assigned sequentially (0, 1, 2, 3) |
| CAP-BR-7 | Sound effects respect user preference |
| CAP-BR-8 | Countdown options: 3, 5 (default), 8, 10 seconds |

---

## Data Requirements

### Captured Photo Structure

```typescript
interface CapturedPhoto {
  id: string;              // UUID
  sessionId: string;       // Parent session
  index: number;           // 0-3
  dataUrl: string;         // "data:image/jpeg;base64,..."
  width: number;           // Pixels
  height: number;          // Pixels
  sizeBytes: number;       // Approximate size
  capturedAt: Date;
}
```

### Capture Configuration

```typescript
interface CaptureConfig {
  // Video constraints
  video: {
    facingMode: 'user';           // Front camera for selfie
    width: { ideal: 1280 };       // Target resolution
    height: { ideal: 960 };
  };

  // Canvas/output settings
  output: {
    width: 1280;                  // Output dimensions
    height: 960;
    mimeType: 'image/jpeg';
    quality: 0.92;                // JPEG quality
  };

  // Preview settings
  preview: {
    mirrored: true;               // CSS transform: scaleX(-1)
  };

  // Countdown options
  countdown: {
    options: [3, 5, 8, 10];
    default: 5;
  };
}
```

---

## UI/UX Requirements

### Camera Page Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  [🏠]                  Photo 2 of 4 / 사진 2/4                   │
│                                                                 │
│  ┌───────┬───────┬───────┬───────┐                              │
│  │  ✅   │  📷   │  ○    │  ○    │  ← Thumbnail strip           │
│  │ [img] │ next  │       │       │                              │
│  └───────┴───────┴───────┴───────┘                              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │                                                         │    │
│  │                   CAMERA PREVIEW                        │    │
│  │                   (mirrored, live)                      │    │
│  │                                                         │    │
│  │                                                         │    │
│  │                                                         │    │
│  │                                                         │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│     Countdown:  [3] [5] [8] [10]        Sound: [🔊]             │
│                      ↑ selected                                 │
│                                                                 │
│                 ┌─────────────────┐                             │
│                 │  📸 CAPTURE     │                             │
│                 │     촬영         │                             │
│                 └─────────────────┘                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### During Countdown

```
┌─────────────────────────────────────────────────────────────────┐
│  [🏠]                  Photo 2 of 4 / 사진 2/4                   │
│                                                                 │
│  ┌───────┬───────┬───────┬───────┐                              │
│  │  ✅   │  📷   │  ○    │  ○    │                              │
│  │ [img] │ next  │       │       │                              │
│  └───────┴───────┴───────┴───────┘                              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │                                                         │    │
│  │                   CAMERA PREVIEW                        │    │
│  │                                                         │    │
│  │                      ╔═══╗                              │    │
│  │                      ║ 3 ║  ← Large countdown number    │    │
│  │                      ╚═══╝    (animated, pulsing)       │    │
│  │                                                         │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│     Countdown:  [3] [5] [8] [10]        Sound: [🔊]             │
│                      (disabled during countdown)                │
│                                                                 │
│                 ┌─────────────────┐                             │
│                 │    CANCEL       │                             │
│                 │    취소          │                             │
│                 └─────────────────┘                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Flash Effect (at capture moment)

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ████████████████████████████████████████████████████████████   │
│  ████████████████████████████████████████████████████████████   │
│  ████████████████████████████████████████████████████████████   │
│  ██████████████  WHITE FLASH OVERLAY  ███████████████████████   │
│  ████████████████████████████████████████████████████████████   │
│  ████████████████  (100ms duration)   ███████████████████████   │
│  ████████████████████████████████████████████████████████████   │
│  ████████████████████████████████████████████████████████████   │
│  ████████████████████████████████████████████████████████████   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Thumbnail States

```
┌───────────────────────────────────────────────────────────────────────┐
│                         THUMBNAIL STATES                              │
│                                                                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐                  │
│  │         │  │         │  │         │  │         │                  │
│  │    1    │  │    2    │  │    3    │  │    4    │  Empty (pending) │
│  │   ○     │  │   ○     │  │   ○     │  │   ○     │  - Gray border   │
│  │         │  │         │  │         │  │         │  - Number shown  │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘                  │
│                                                                       │
│  ┌─────────┐                                                          │
│  │ ┌─────┐ │                                                          │
│  │ │photo│ │  Captured                                                │
│  │ └─────┘ │  - Photo thumbnail                                       │
│  │   ✅    │  - Green checkmark                                       │
│  └─────────┘  - Tappable (for retake)                                │
│                                                                       │
│  ┌─────────┐                                                          │
│  │ ┌─────┐ │                                                          │
│  │ │     │ │  Current (next to capture)                              │
│  │ └─────┘ │  - Pulsing border                                       │
│  │   📷    │  - Camera icon                                          │
│  └─────────┘  - Highlighted                                          │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## Technical Notes

### useCamera Hook Implementation

```typescript
// hooks/useCamera.ts

interface UseCameraReturn {
  // State
  state: CameraState;
  isReady: boolean;
  error: CameraError | null;

  // Refs
  videoRef: RefObject<HTMLVideoElement>;

  // Actions
  start: () => Promise<void>;
  stop: () => void;
  capture: () => Promise<CapturedPhoto>;

  // Info
  capabilities: MediaTrackCapabilities | null;
}

const useCamera = (options: CameraOptions): UseCameraReturn => {
  const [state, setState] = useState<CameraState>({ status: 'idle' });
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const start = async () => {
    setState({ status: 'initializing' });

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: options.facingMode,
          width: { ideal: options.width },
          height: { ideal: options.height },
        },
        audio: false,
      });

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      setState({ status: 'ready', stream });
    } catch (err) {
      const error = mapMediaError(err);
      setState({ status: 'error', error });
    }
  };

  const capture = async (): Promise<CapturedPhoto> => {
    if (!videoRef.current || !streamRef.current) {
      throw new Error('Camera not ready');
    }

    const video = videoRef.current;

    // Create canvas if needed
    if (!canvasRef.current) {
      canvasRef.current = document.createElement('canvas');
    }
    const canvas = canvasRef.current;

    // Set canvas size
    canvas.width = options.output.width;
    canvas.height = options.output.height;

    const ctx = canvas.getContext('2d')!;

    // Mirror the image (flip horizontally for natural photo)
    // Note: Preview is mirrored via CSS, but captured image should be natural
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);

    // Draw video frame
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Reset transform
    ctx.setTransform(1, 0, 0, 1, 0, 0);

    // Export as JPEG
    const dataUrl = canvas.toDataURL('image/jpeg', options.output.quality);

    return {
      id: generateUUID(),
      dataUrl,
      width: canvas.width,
      height: canvas.height,
      sizeBytes: Math.ceil((dataUrl.length - 22) * 0.75),
      capturedAt: new Date(),
    };
  };

  const stop = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setState({ status: 'idle' });
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => stop();
  }, []);

  return {
    state,
    isReady: state.status === 'ready',
    error: state.status === 'error' ? state.error : null,
    videoRef,
    start,
    stop,
    capture,
    capabilities: null, // Can be implemented if needed
  };
};
```

### Countdown Component

```typescript
// components/camera/Countdown.tsx

interface CountdownProps {
  seconds: number;
  onComplete: () => void;
  onCancel: () => void;
  soundEnabled: boolean;
}

const Countdown: React.FC<CountdownProps> = ({
  seconds,
  onComplete,
  onCancel,
  soundEnabled,
}) => {
  const [remaining, setRemaining] = useState(seconds);
  const { playTick } = useSound();

  useEffect(() => {
    if (remaining <= 0) {
      onComplete();
      return;
    }

    const timer = setTimeout(() => {
      if (soundEnabled) {
        playTick();
      }
      setRemaining(r => r - 1);
    }, 1000);

    return () => clearTimeout(timer);
  }, [remaining, soundEnabled, onComplete, playTick]);

  return (
    <div className="countdown-overlay" onClick={onCancel}>
      <div className="countdown-number" key={remaining}>
        {remaining}
      </div>
    </div>
  );
};
```

### CSS for Mirrored Preview

```css
/* styles/camera.css */

.camera-preview {
  transform: scaleX(-1); /* Mirror for selfie view */
}

.camera-preview.capturing {
  /* Slight zoom effect during capture */
  animation: capture-pulse 0.1s ease-out;
}

@keyframes capture-pulse {
  0% { transform: scaleX(-1) scale(1); }
  50% { transform: scaleX(-1) scale(1.02); }
  100% { transform: scaleX(-1) scale(1); }
}

.flash-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: white;
  opacity: 0;
  pointer-events: none;
  z-index: 1000;
}

.flash-overlay.active {
  animation: flash 0.15s ease-out;
}

@keyframes flash {
  0% { opacity: 0; }
  30% { opacity: 0.9; }
  100% { opacity: 0; }
}

.countdown-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.3);
}

.countdown-number {
  font-size: 120px;
  font-weight: bold;
  color: white;
  text-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
  animation: countdown-pop 1s ease-out;
}

@keyframes countdown-pop {
  0% { transform: scale(1.5); opacity: 0; }
  20% { transform: scale(1); opacity: 1; }
  80% { transform: scale(1); opacity: 1; }
  100% { transform: scale(0.8); opacity: 0.5; }
}
```

---

## Sequence Diagram

```
┌──────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌─────────┐
│ User │     │  Camera  │     │Countdown │     │  Canvas  │     │ Session │
│      │     │  Page    │     │Component │     │ (hidden) │     │ Context │
└──┬───┘     └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬────┘
   │              │                │                │                │
   │ Tap Capture  │                │                │                │
   │─────────────►│                │                │                │
   │              │                │                │                │
   │              │ Start countdown│                │                │
   │              │───────────────►│                │                │
   │              │                │                │                │
   │              │                │ Tick (5,4,3..) │                │
   │◄─────────────┼────────────────│                │                │
   │  See number  │                │                │                │
   │              │                │                │                │
   │              │                │ onComplete()   │                │
   │              │◄───────────────│                │                │
   │              │                │                │                │
   │              │ Draw frame     │                │                │
   │              │───────────────────────────────►│                │
   │              │                │                │                │
   │              │ toDataURL()    │                │                │
   │              │◄───────────────────────────────│                │
   │              │                │                │                │
   │              │ Add photo      │                │                │
   │              │────────────────────────────────────────────────►│
   │              │                │                │                │
   │              │                │                │  Photo added   │
   │              │◄────────────────────────────────────────────────│
   │              │                │                │                │
   │ See thumbnail│                │                │                │
   │◄─────────────│                │                │                │
   │              │                │                │                │
```

---

## Open Questions

| # | Question | Status |
|---|----------|--------|
| 1 | Should countdown have haptic feedback? | **Decision: No (not reliable cross-platform)** |
| 2 | Allow photo during countdown tap to skip? | **Decision: No (maintains anticipation)** |
| 3 | Resolution priority: quality vs speed? | **Decision: 1280x960 balanced** |

---

## Related Use Cases

- **UC-001**: Start Photo Session (precedes this)
- **UC-003**: Retake Photo (variation of this)
- **UC-004**: Preview Composite (follows when 4 photos captured)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
