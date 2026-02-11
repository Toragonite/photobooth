import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../contexts/LanguageContext";
import { useSettings } from "../contexts/SettingsContext";
import { useSession } from "../contexts/SessionContext";
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
import { getPhotoCount } from "../types/layout";

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
  const { layoutType, sessionId } = useSession();

  // Get required photo count for current layout
  const requiredPhotos = getPhotoCount(layoutType);

  const [cameraState, setCameraState] = useState<CameraState>("initializing");
  const [photos, setPhotos] = useState<string[]>([]);
  const [selectedCountdown, setSelectedCountdown] = useState(
    settings.defaultCountdown,
  );
  const [error, setError] = useState<string | null>(null);
  const [selectedPreset, setSelectedPreset] = useState<PresetKey>("natural");
  const [showOptionsModal, setShowOptionsModal] = useState(false);
  const [facingMode, setFacingMode] = useState<"user" | "environment">("user");

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
  } = useCamera({ layoutType, facingMode });

  // Apply preset when selected
  const handlePresetChange = (preset: PresetKey) => {
    setSelectedPreset(preset);
    setEnhancement(ENHANCEMENT_PRESETS[preset] as EnhancementSettings);
  };

  // Get CSS filter for real-time preview
  const videoFilter = getFilterString(enhancement);

  // Initialize camera on mount and when facingMode changes
  useEffect(() => {
    setCameraState("initializing");
    start();
    return () => stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [facingMode]);

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

  const handleToggleCamera = () => {
    stop();
    setFacingMode((prev) => (prev === "user" ? "environment" : "user"));
  };

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
        if (sessionId) {
          const blob = await fetch(imageData).then((r) => r.blob());
          await api.uploadPhoto(sessionId, newPhotos.length - 1, blob);
        }

        if (newPhotos.length >= requiredPhotos) {
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
  const showControls = cameraState === "ready" && photos.length < requiredPhotos;

  return (
    <div className="flex flex-col h-full gap-1 sm:gap-2">
      {/* Title - fixed height */}
      <div className="section-fixed text-center h-10 sm:h-14 flex flex-col justify-center">
        <h1 className="text-lg sm:text-2xl font-bold text-primary">{t("camera.title")}</h1>
        <p className="text-text-muted text-xs sm:text-sm">{photos.length} / {requiredPhotos}</p>
      </div>

      {/* Camera preview - grows to fill space */}
      <div
        className="section-grow relative bg-black rounded-3xl overflow-hidden flex items-center justify-center"
      >
        {/* Video container with aspect ratio control */}
        <div
          className={`relative overflow-hidden ${
            layoutType === "1x4"
              ? "w-full aspect-video" // 16:9 aspect ratio, crops top/bottom
              : "w-full h-full"
          }`}
        >
          {/* Video element - always rendered so ref is available */}
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className={`w-full h-full object-cover ${cameraState === "initializing" ? "invisible" : ""}`}
            style={{
              transform: facingMode === "user" ? "scaleX(-1)" : "none",
              filter: videoFilter,
            }}
          />
        </div>

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
      <div className="section-fixed h-16 sm:h-20 flex justify-center items-center gap-2 sm:gap-3">
        {Array.from({ length: requiredPhotos }, (_, index) => (
          <PhotoThumbnail
            key={index}
            index={index}
            src={photos[index]}
            isActive={photos.length === index}
            isClickable={!!photos[index]}
            onClick={() => photos[index] && handleRetake(index)}
            variant={layoutType === "1x4" ? "landscape" : "square"}
          />
        ))}
      </div>

      {/* Controls - fixed height container, content visibility changes */}
      <div className="section-fixed h-20 sm:h-44 flex flex-col items-center justify-center gap-2 sm:gap-3">
        {/* Enhancement presets - tablet+ only, hidden on mobile (moved to modal) */}
        <div
          className={`hidden sm:flex flex-wrap justify-center gap-2 transition-opacity duration-200 ${
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

        {/* Countdown selector - tablet+ only, hidden on mobile (moved to modal) */}
        <div
          className={`hidden sm:flex gap-2 transition-opacity duration-200 ${
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

        {/* Capture button row with mobile options button */}
        <div className="h-18 sm:h-24 flex items-center justify-center gap-4">
          {showControls ? (
            <>
              {/* Mobile: Options button */}
              <button
                onClick={() => setShowOptionsModal(true)}
                className="sm:hidden w-12 h-12 rounded-full bg-gray-100 text-text-muted
                           flex items-center justify-center
                           hover:bg-gray-200 active:scale-95 transition-all"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </button>

              {/* Capture button */}
              <button
                onClick={startCountdown}
                className="w-16 h-16 sm:w-20 sm:h-20 rounded-full bg-primary text-white
                           flex items-center justify-center
                           shadow-lg hover:shadow-xl hover:scale-105
                           active:scale-95 transition-all"
              >
                <svg
                  className="w-8 h-8 sm:w-10 sm:h-10"
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

              {/* Camera flip button */}
              <button
                onClick={handleToggleCamera}
                className="w-12 h-12 sm:w-14 sm:h-14 rounded-full bg-gray-100 text-text-muted
                           flex items-center justify-center
                           hover:bg-gray-200 active:scale-95 transition-all"
              >
                <svg className="w-6 h-6 sm:w-7 sm:h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
            </>
          ) : cameraState === "countdown" ? (
            <p className="text-xl text-text-muted">{t("camera.instruction")}</p>
          ) : null}
        </div>
      </div>

      {/* Mobile Options Modal */}
      {showOptionsModal && (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/50" onClick={() => setShowOptionsModal(false)}>
          <div className="bg-white rounded-t-2xl w-full max-h-[70vh] overflow-y-auto safe-bottom" onClick={(e) => e.stopPropagation()}>
            {/* Modal header */}
            <div className="sticky top-0 bg-white border-b p-4 flex justify-between items-center">
              <h2 className="text-lg font-bold">{t("camera.settings")}</h2>
              <button onClick={() => setShowOptionsModal(false)} className="p-2 hover:bg-gray-100 rounded-full">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-4 space-y-6">
              {/* Enhancement presets */}
              <div>
                <label className="block text-sm font-semibold mb-3">{t("camera.enhancement.title")}</label>
                <div className="grid grid-cols-2 gap-2">
                  {PRESET_OPTIONS.map((preset) => (
                    <button
                      key={preset.id}
                      onClick={() => handlePresetChange(preset.id)}
                      className={`flex items-center gap-2 px-3 py-2.5 rounded-lg border-2 transition-all ${
                        selectedPreset === preset.id
                          ? "border-primary bg-primary/10 text-primary"
                          : "border-gray-200 hover:border-primary/50"
                      }`}
                    >
                      <span className="text-lg">{preset.icon}</span>
                      <span className="text-sm font-medium">{t(preset.labelKey)}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Camera direction */}
              <div>
                <label className="block text-sm font-semibold mb-3">{t("camera.facing.title")}</label>
                <div className="flex gap-2 justify-center">
                  <button
                    onClick={() => { stop(); setFacingMode("user"); }}
                    className={`flex-1 px-4 py-3 rounded-lg border-2 text-sm font-medium transition-all ${
                      facingMode === "user"
                        ? "border-primary bg-primary/10 text-primary"
                        : "border-gray-200 hover:border-primary/50"
                    }`}
                  >
                    {t("camera.facing.front")}
                  </button>
                  <button
                    onClick={() => { stop(); setFacingMode("environment"); }}
                    className={`flex-1 px-4 py-3 rounded-lg border-2 text-sm font-medium transition-all ${
                      facingMode === "environment"
                        ? "border-primary bg-primary/10 text-primary"
                        : "border-gray-200 hover:border-primary/50"
                    }`}
                  >
                    {t("camera.facing.rear")}
                  </button>
                </div>
              </div>

              {/* Countdown selector */}
              <div>
                <label className="block text-sm font-semibold mb-3">{t("camera.countdown.title")}</label>
                <div className="flex gap-2 justify-center">
                  {settings.countdownOptions.map((seconds) => (
                    <button
                      key={seconds}
                      onClick={() => setSelectedCountdown(seconds)}
                      className={`px-5 py-3 rounded-lg border-2 text-base font-medium transition-all ${
                        selectedCountdown === seconds
                          ? "border-primary bg-primary/10 text-primary"
                          : "border-gray-200 hover:border-primary/50"
                      }`}
                    >
                      {seconds}{t("camera.countdown.seconds")}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Done button */}
            <div className="p-4 border-t">
              <button onClick={() => setShowOptionsModal(false)} className="btn-primary w-full">
                {t("common.confirm")}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
