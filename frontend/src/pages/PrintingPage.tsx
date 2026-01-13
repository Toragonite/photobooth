import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../contexts/LanguageContext";
import { api } from "../services/api";

type PrintStatus =
  | "pending"
  | "processing"
  | "printing"
  | "completed"
  | "failed"
  | "cancelled"
  | "retry_pending";

export function PrintingPage() {
  const navigate = useNavigate();
  const { t } = useLanguage();

  const [status, setStatus] = useState<PrintStatus>("pending");
  const [progress, setProgress] = useState(0);
  const [_error, setError] = useState<string | null>(null);

  const pollIntervalRef = useRef<number | null>(null);
  const jobId = sessionStorage.getItem("jobId");

  useEffect(() => {
    if (!jobId) {
      navigate("/");
      return;
    }

    // Start polling for status
    const pollStatus = async () => {
      try {
        const response = await api.getPrintJob(jobId);

        if (response.success && response.data) {
          const data = response.data;
          setStatus(data.status as PrintStatus);
          setProgress(data.progress);

          // Handle terminal states
          if (data.status === "completed") {
            if (pollIntervalRef.current) {
              clearInterval(pollIntervalRef.current);
            }
            navigate("/complete");
          } else if (data.status === "failed") {
            if (pollIntervalRef.current) {
              clearInterval(pollIntervalRef.current);
            }
            setError(data.error?.message || "Print failed");
            navigate("/error", {
              state: {
                error: data.error,
                jobId: jobId,
              },
            });
          } else if (data.status === "cancelled") {
            if (pollIntervalRef.current) {
              clearInterval(pollIntervalRef.current);
            }
            navigate("/");
          }
        }
      } catch (err) {
        console.error("Status poll failed:", err);
      }
    };

    // Initial poll
    pollStatus();

    // Poll every second
    pollIntervalRef.current = window.setInterval(pollStatus, 1000);

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [jobId, navigate]);

  const getStatusMessage = () => {
    switch (status) {
      case "pending":
      case "processing":
        return t("printing.processing");
      case "printing":
        return t("printing.printing");
      case "retry_pending":
        return t("printing.sending");
      default:
        return t("printing.pleaseWait");
    }
  };

  return (
    <div className="center-content">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-primary mb-8">
          {t("printing.title")}
        </h1>

        {/* Progress ring */}
        <div className="relative w-48 h-48 mx-auto mb-8">
          <svg className="w-full h-full transform -rotate-90">
            {/* Background circle */}
            <circle
              cx="96"
              cy="96"
              r="88"
              fill="none"
              stroke="#E6F4FB"
              strokeWidth="12"
            />
            {/* Progress circle */}
            <circle
              cx="96"
              cy="96"
              r="88"
              fill="none"
              stroke="#00A1DE"
              strokeWidth="12"
              strokeLinecap="round"
              strokeDasharray={553}
              strokeDashoffset={553 - (553 * progress) / 100}
              className="transition-all duration-500"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-4xl font-bold text-primary">{progress}%</span>
          </div>
        </div>

        {/* Status message */}
        <p className="text-xl text-text-muted mb-4">{getStatusMessage()}</p>

        {/* Animated dots */}
        <div className="flex justify-center gap-2">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="w-3 h-3 bg-primary rounded-full animate-bounce"
              style={{ animationDelay: `${i * 0.2}s` }}
            />
          ))}
        </div>

        {/* Warning */}
        <p className="mt-8 text-sm text-text-muted">
          {t("printing.doNotLeave")}
        </p>
      </div>
    </div>
  );
}
