import { useNavigate, useLocation } from "react-router-dom";
import { useLanguage } from "../contexts/LanguageContext";
import { api } from "../services/api";
import { useState } from "react";

interface ErrorState {
  error?: {
    code: string;
    message: string;
  };
  jobId?: string;
}

export function ErrorPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useLanguage();
  const [isRetrying, setIsRetrying] = useState(false);

  const state = location.state as ErrorState | undefined;
  const errorCode = state?.error?.code || "unknown";
  const jobId = state?.jobId;

  // Get localized error message
  const errorMessage = (() => {
    const key = `error.messages.${errorCode}`;
    const message = t(key);
    // If translation not found, use the error message from state or default
    return message !== key
      ? message
      : state?.error?.message || t("error.messages.unknown");
  })();

  const handleRetry = async () => {
    if (!jobId) {
      navigate("/");
      return;
    }

    try {
      setIsRetrying(true);
      const response = await api.retryPrintJob(jobId);

      if (response.success) {
        navigate("/printing");
      }
    } catch (err) {
      console.error("Retry failed:", err);
    } finally {
      setIsRetrying(false);
    }
  };

  const handleAbort = async () => {
    if (jobId) {
      try {
        await api.cancelPrintJob(jobId);
      } catch (err) {
        console.error("Cancel failed:", err);
      }
    }

    sessionStorage.removeItem("sessionId");
    sessionStorage.removeItem("jobId");
    navigate("/");
  };

  return (
    <div className="center-content">
      <div className="text-center max-w-md">
        {/* Error icon */}
        <div className="w-32 h-32 mx-auto mb-8 rounded-full bg-error flex items-center justify-center">
          <svg
            className="w-16 h-16 text-white"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>

        {/* Title */}
        <h1 className="text-4xl font-bold text-error mb-4">
          {t("error.title")}
        </h1>

        {/* Error message */}
        <p className="text-xl text-text mb-8">{errorMessage}</p>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={handleRetry}
            disabled={isRetrying}
            className="btn-primary"
          >
            {isRetrying ? (
              <span className="flex items-center gap-2">
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                {t("common.loading")}
              </span>
            ) : (
              t("error.retry")
            )}
          </button>

          <button onClick={handleAbort} className="btn-outline">
            {t("error.abort")}
          </button>
        </div>

        {/* Go home link */}
        <button
          onClick={() => {
            sessionStorage.removeItem("sessionId");
            sessionStorage.removeItem("jobId");
            navigate("/");
          }}
          className="mt-8 text-text-muted hover:text-primary transition-colors"
        >
          {t("error.goHome")}
        </button>
      </div>
    </div>
  );
}
