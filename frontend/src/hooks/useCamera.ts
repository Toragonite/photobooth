import { useRef, useState, useCallback } from "react";

interface UseCameraOptions {
  facingMode?: "user" | "environment";
  width?: number;
  height?: number;
}

interface UseCameraReturn {
  videoRef: React.RefObject<HTMLVideoElement>;
  isReady: boolean;
  error: string | null;
  stream: MediaStream | null;
  start: () => Promise<void>;
  stop: () => void;
  capture: () => Promise<string | null>;
  debugLog: string[];
}

export function useCamera(options: UseCameraOptions = {}): UseCameraReturn {
  const { facingMode = "user", width = 1280, height = 960 } = options;

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [debugLog, setDebugLog] = useState<string[]>([]);

  const addLog = (msg: string) => {
    console.log(msg);
    setDebugLog((prev) => [...prev.slice(-10), `${new Date().toLocaleTimeString()}: ${msg}`]);
  };

  const start = useCallback(async () => {
    try {
      setError(null);
      setIsReady(false);
      setDebugLog([]);

      addLog("Starting camera...");
      addLog(`mediaDevices: ${!!navigator.mediaDevices}`);
      addLog(`getUserMedia: ${!!navigator.mediaDevices?.getUserMedia}`);
      addLog(`Protocol: ${window.location.protocol}`);

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

      addLog("Requesting getUserMedia...");

      const mediaStream =
        await navigator.mediaDevices.getUserMedia(constraints);

      addLog(`Got stream! Tracks: ${mediaStream.getTracks().length}`);

      setStream(mediaStream);

      addLog(`videoRef exists: ${!!videoRef.current}`);

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        addLog("srcObject set");

        videoRef.current.onloadedmetadata = async () => {
          addLog("Metadata loaded");
          try {
            await videoRef.current?.play();
            addLog("Video playing!");
            setIsReady(true);
          } catch (playError) {
            addLog(`Play error: ${playError}`);
            setIsReady(true);
          }
        };
      } else {
        addLog("ERROR: videoRef is null!");
        setError("Video element not found");
      }
    } catch (err) {
      addLog(`ERROR: ${err}`);

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

    // Convert to JPEG
    return canvas.toDataURL("image/jpeg", 0.92);
  }, [isReady]);

  return {
    videoRef,
    isReady,
    error,
    stream,
    start,
    stop,
    capture,
    debugLog,
  };
}
