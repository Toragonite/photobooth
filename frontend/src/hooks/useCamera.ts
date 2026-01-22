import { useRef, useState, useCallback } from "react";
import {
  EnhancementSettings,
  DEFAULT_ENHANCEMENT,
  applyEnhancement,
  hasEnhancement,
} from "../utils/imageEnhancement";
import { LayoutType, LAYOUT_CONFIGS } from "../types/layout";

interface UseCameraOptions {
  facingMode?: "user" | "environment";
  width?: number;
  height?: number;
  layoutType?: LayoutType;
}

interface UseCameraReturn {
  videoRef: React.RefObject<HTMLVideoElement>;
  isReady: boolean;
  error: string | null;
  stream: MediaStream | null;
  enhancement: EnhancementSettings;
  setEnhancement: (settings: EnhancementSettings) => void;
  start: () => Promise<void>;
  stop: () => void;
  capture: () => Promise<string | null>;
}

export function useCamera(options: UseCameraOptions = {}): UseCameraReturn {
  const { facingMode = "user", layoutType = "2x2" } = options;

  // Get resolution based on layout type
  const layoutConfig = LAYOUT_CONFIGS[layoutType];
  const width = options.width ?? layoutConfig.resolution.width;
  const height = options.height ?? layoutConfig.resolution.height;

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [enhancement, setEnhancement] = useState<EnhancementSettings>(DEFAULT_ENHANCEMENT);

  const start = useCallback(async () => {
    try {
      setError(null);
      setIsReady(false);

      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("Camera API not available");
      }

      const constraints: MediaStreamConstraints = {
        video: {
          facingMode,
          width: { ideal: width },
          height: { ideal: height },
        },
        audio: false,
      };

      const mediaStream =
        await navigator.mediaDevices.getUserMedia(constraints);

      setStream(mediaStream);

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;

        videoRef.current.onloadedmetadata = async () => {
          try {
            await videoRef.current?.play();
            setIsReady(true);
          } catch (playError) {
            console.error("Video play error:", playError);
            setIsReady(true);
          }
        };
      } else {
        setError("Video element not found");
      }
    } catch (err) {
      console.error("Camera start error:", err);

      if (err instanceof Error) {
        if (err.name === "NotAllowedError") {
          setError("Camera permission denied");
        } else if (err.name === "NotFoundError") {
          setError("No camera found");
        } else if (err.name === "NotSupportedError") {
          setError("Camera not supported");
        } else {
          setError(`Camera error: ${err.message}`);
        }
      } else {
        setError("Unknown camera error");
      }
    }
  }, [facingMode, width, height]);

  const stop = useCallback(() => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsReady(false);
  }, [stream]);

  const capture = useCallback(async (): Promise<string | null> => {
    if (!videoRef.current || !isReady) {
      return null;
    }

    const video = videoRef.current;

    // Create canvas if not exists
    if (!canvasRef.current) {
      canvasRef.current = document.createElement("canvas");
    }
    const canvas = canvasRef.current;

    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");
    if (!ctx) {
      return null;
    }

    // Mirror the image for selfie camera
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);

    // Draw video frame to canvas
    ctx.drawImage(video, 0, 0);

    // Reset transform
    ctx.setTransform(1, 0, 0, 1, 0, 0);

    // Apply enhancement if any settings are active
    if (hasEnhancement(enhancement)) {
      applyEnhancement(ctx, canvas.width, canvas.height, enhancement);
    }

    // Convert to JPEG
    return canvas.toDataURL("image/jpeg", 0.92);
  }, [isReady, enhancement]);

  return {
    videoRef,
    isReady,
    error,
    stream,
    enhancement,
    setEnhancement,
    start,
    stop,
    capture,
  };
}
