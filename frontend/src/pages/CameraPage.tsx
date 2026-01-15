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

type CameraState =
  | "initializing"
  | "ready"
  | "countdown"
  | "capturing"
  | "complete"
  | "error";

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
    capture,
    start,
    stop,
    debugLog,
  } = useCamera();

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

  return (
    <div className="flex flex-col h-full">
      {/* Title */}
      <div className="text-center mb-4">
        <h1 className="text-3xl font-bold text-primary">{t("camera.title")}</h1>
        <p className="text-text-muted mt-1">{photos.length} / 4</p>
        {/* Debug info - remove later */}
        <p className="text-xs text-red-500">
          State: {cameraState} | Ready: {isReady ? "Y" : "N"} | Error: {cameraError || "none"}
        </p>
        {/* Debug log */}
        <div className="mt-2 p-2 bg-black text-green-400 text-xs text-left rounded max-h-32 overflow-y-auto font-mono">
          {debugLog.length === 0 ? "Waiting for logs..." : debugLog.map((log, i) => (
            <div key={i}>{log}</div>
          ))}
        </div>
      </div>

      {/* Camera preview */}
      <div className="flex-1 relative bg-black rounded-3xl overflow-hidden mb-4">
        {/* Video element - always rendered so ref is available */}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className={`w-full h-full object-cover ${cameraState === "initializing" ? "invisible" : ""}`}
          style={{ transform: "scaleX(-1)" }} // Mirror for selfie
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

      {/* Thumbnail strip */}
      <div className="flex justify-center gap-3 mb-4">
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

      {/* Controls */}
      <div className="flex flex-col items-center gap-4">
        {/* Countdown selector */}
        {cameraState === "ready" && photos.length < 4 && (
          <div className="flex gap-2">
            {settings.countdownOptions.map((seconds) => (
              <button
                key={seconds}
                onClick={() => setSelectedCountdown(seconds)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors
                           ${
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
        )}

        {/* Capture button */}
        {cameraState === "ready" && photos.length < 4 && (
          <button
            onClick={startCountdown}
            className="w-24 h-24 rounded-full bg-primary text-white
                       flex items-center justify-center
                       shadow-lg hover:shadow-xl hover:scale-105
                       active:scale-95 transition-all"
          >
            <svg
              className="w-12 h-12"
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
        )}

        {/* Countdown in progress */}
        {cameraState === "countdown" && (
          <p className="text-xl text-text-muted">{t("camera.instruction")}</p>
        )}
      </div>
    </div>
  );
}
