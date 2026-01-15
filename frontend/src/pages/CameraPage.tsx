import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../contexts/LanguageContext";
import { useSettings } from "../contexts/SettingsContext";
import { useCamera, useCountdown } from "../hooks";
import { api } from "../services/api";
import {
  LoadingSpinner,
  ErrorDisplay,
  CountdownDisplay,
  PhotoThumbnail,
} from "../components/common";
import {
  ENHANCEMENT_PRESETS,
  getFilterString,
  EnhancementSettings,
} from "../utils/imageEnhancement";

type CameraState =
  | "initializing"
  | "ready"
  | "countdown"
  | "capturing"
  | "complete"
  | "error";

// Enhancement preset options for UI
type PresetKey = keyof typeof ENHANCEMENT_PRESETS;
const PRESET_OPTIONS: { id: PresetKey; labelKey: string; icon: string }[] = [
  { id: "none", labelKey: "camera.enhancement.none", icon: "🔲" },
  { id: "natural", labelKey: "camera.enhancement.natural", icon: "✨" },
  { id: "bright", labelKey: "camera.enhancement.bright", icon: "☀️" },
  { id: "warm", labelKey: "camera.enhancement.warm", icon: "🌅" },
  { id: "soft", labelKey: "camera.enhancement.soft", icon: "🌸" },
];

export function CameraPage() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const { settings } = useSettings();

  const [cameraState, setCameraState] = useState<CameraState>("initializing");
  const [photos, setPhotos] = useState<string[]>([]);
  const [selectedCountdown, setSelectedCountdown] = useState(
    settings.defaultCountdown,
  );
  const [error, setError] = useState<string | null>(null);
  const [selectedPreset, setSelectedPreset] = useState<PresetKey>("natural");

  const {
    count: countdown,
    isRunning: isCountdownRunning,
    start: startCountdownTimer,
    reset: _resetCountdown,
  } = useCountdown(selectedCountdown, {
    onComplete: () => handleCapture(),
  });

  const {
    videoRef,
    isReady,
    error: cameraError,
    enhancement,
    setEnhancement,
    capture,
    start,
    stop,
  } = useCamera();

  // Apply preset when selected
  const handlePresetChange = (preset: PresetKey) => {
    setSelectedPreset(preset);
    setEnhancement(ENHANCEMENT_PRESETS[preset] as EnhancementSettings);
  };

  // Get CSS filter for real-time preview
  const videoFilter = getFilterString(enhancement);

  // Initialize camera on mount
  useEffect(() => {
    start();
    return () => stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update state when camera is ready
  useEffect(() => {
    if (isReady) {
      setCameraState("ready");
    }
    if (cameraError) {
      setCameraState("error");
      setError(cameraError);
    }
  }, [isReady, cameraError]);

  // Sync countdown state with camera state
  useEffect(() => {
    if (isCountdownRunning && cameraState !== "countdown") {
      setCameraState("countdown");
    }
  }, [isCountdownRunning, cameraState]);

  const startCountdown = () => {
    setCameraState("countdown");
    startCountdownTimer(selectedCountdown);
  };

  const handleCapture = async () => {
    setCameraState("capturing");

    try {
      const imageData = await capture();
      if (imageData) {
        const newPhotos = [...photos, imageData];
        setPhotos(newPhotos);

        // Upload to server
        const sessionId = sessionStorage.getItem("sessionId");
        if (sessionId) {
          const blob = await fetch(imageData).then((r) => r.blob());
          await api.uploadPhoto(sessionId, newPhotos.length - 1, blob);
        }

        if (newPhotos.length >= 4) {
          setCameraState("complete");
          // Navigate to preview after short delay
          setTimeout(() => navigate("/preview"), 500);
        } else {
          setCameraState("ready");
        }
      }
    } catch (err) {
      console.error("Capture failed:", err);
      setCameraState("ready");
    }
  };

  const handleRetake = async (index: number) => {
    // Remove photo at index and all after it
    setPhotos(photos.slice(0, index));
    setCameraState("ready");
  };

  if (cameraState === "error") {
    return (
      <div className="center-content">
        <ErrorDisplay
          title={t("camera.permissionDenied")}
          message={error || t("camera.error")}
          onRetry={() => {
            setError(null);
            setCameraState("initializing");
            start();
          }}
        />
      </div>
    );
  }

  // Check if controls should be visible
  const showControls = cameraState === "ready" && photos.length < 4;

  return (
    <div className="flex flex-col h-full">
      {/* Title - fixed height */}
      <div className="section-fixed text-center h-14 flex flex-col justify-center">
        <h1 className="text-2xl font-bold text-primary">{t("camera.title")}</h1>
        <p className="text-text-muted text-sm">{photos.length} / 4</p>
      </div>

      {/* Camera preview - grows to fill space */}
      <div className="section-grow relative bg-black rounded-3xl overflow-hidden">
        {/* Video element - always rendered so ref is available */}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className={`w-full h-full object-cover ${cameraState === "initializing" ? "invisible" : ""}`}
          style={{
            transform: "scaleX(-1)", // Mirror for selfie
            filter: videoFilter, // Apply real-time enhancement preview
          }}
        />

        {/* Loading overlay */}
        {cameraState === "initializing" && (
          <div className="absolute inset-0 flex items-center justify-center">
            <LoadingSpinner color="white" message={t("common.loading")} />
          </div>
        )}

        {/* Countdown overlay */}
        {cameraState === "countdown" && countdown > 0 && (
          <CountdownDisplay count={countdown} size="xl" variant="overlay" />
        )}

        {/* Flash effect */}
        {cameraState === "capturing" && (
          <div className="absolute inset-0 bg-white flash" />
        )}
      </div>

      {/* Thumbnail strip - fixed height */}
      <div className="section-fixed h-20 flex justify-center items-center gap-3">
        {[0, 1, 2, 3].map((index) => (
          <PhotoThumbnail
            key={index}
            index={index}
            src={photos[index]}
            isActive={photos.length === index}
            isClickable={!!photos[index]}
            onClick={() => photos[index] && handleRetake(index)}
          />
        ))}
      </div>

      {/* Controls - fixed height container, content visibility changes */}
      <div className="section-fixed h-44 flex flex-col items-center justify-center gap-3">
        {/* Enhancement presets - always rendered but visibility controlled */}
        <div
          className={`flex flex-wrap justify-center gap-2 transition-opacity duration-200 ${
            showControls ? "opacity-100" : "opacity-0 pointer-events-none"
          }`}
        >
          {PRESET_OPTIONS.map((preset) => (
            <button
              key={preset.id}
              onClick={() => handlePresetChange(preset.id)}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-full text-sm transition-all ${
                selectedPreset === preset.id
                  ? "bg-primary text-white"
                  : "bg-gray-100 text-text-muted hover:bg-gray-200"
              }`}
            >
              <span>{preset.icon}</span>
              <span>{t(preset.labelKey)}</span>
            </button>
          ))}
        </div>

        {/* Countdown selector - always rendered but visibility controlled */}
        <div
          className={`flex gap-2 transition-opacity duration-200 ${
            showControls ? "opacity-100" : "opacity-0 pointer-events-none"
          }`}
        >
          {settings.countdownOptions.map((seconds) => (
            <button
              key={seconds}
              onClick={() => setSelectedCountdown(seconds)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                selectedCountdown === seconds
                  ? "bg-primary text-white"
                  : "bg-gray-100 text-text-muted hover:bg-gray-200"
              }`}
            >
              {seconds}
              {t("camera.countdown.seconds")}
            </button>
          ))}
        </div>

        {/* Capture button / Countdown message - same space */}
        <div className="h-24 flex items-center justify-center">
          {showControls ? (
            <button
              onClick={startCountdown}
              className="w-20 h-20 rounded-full bg-primary text-white
                         flex items-center justify-center
                         shadow-lg hover:shadow-xl hover:scale-105
                         active:scale-95 transition-all"
            >
              <svg
                className="w-10 h-10"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
            </button>
          ) : cameraState === "countdown" ? (
            <p className="text-xl text-text-muted">{t("camera.instruction")}</p>
          ) : null}
        </div>
      </div>
    </div>
  );
}
