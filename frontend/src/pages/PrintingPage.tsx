import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../contexts/LanguageContext";
import { usePrintJob } from "../hooks";
import { ProgressRing } from "../components/common";

export function PrintingPage() {
  const navigate = useNavigate();
  const { t } = useLanguage();

  const jobId = sessionStorage.getItem("jobId");

  const { status, progress, startPolling, stopPolling } = usePrintJob({
    onComplete: () => navigate("/complete"),
    onFailed: (error) =>
      navigate("/error", {
        state: {
          error,
          jobId,
        },
      }),
    onCancelled: () => navigate("/"),
  });

  useEffect(() => {
    if (!jobId) {
      navigate("/");
      return;
    }

    startPolling(jobId);

    return () => stopPolling();
  }, [jobId, navigate, startPolling, stopPolling]);

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
        <h1 className="text-2xl sm:text-4xl font-bold text-primary mb-4 sm:mb-8">
          {t("printing.title")}
        </h1>

        {/* Progress ring */}
        <div className="mx-auto mb-4 sm:mb-8">
          <ProgressRing
            progress={progress}
            size={192}
            strokeWidth={12}
            color="primary"
            backgroundColor="#E6F4FB"
          >
            <span className="text-2xl sm:text-4xl font-bold text-primary">{progress}%</span>
          </ProgressRing>
        </div>

        {/* Status message */}
        <p className="text-base sm:text-xl text-text-muted mb-4">{getStatusMessage()}</p>

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
        <p className="mt-4 sm:mt-8 text-xs sm:text-sm text-text-muted">
          {t("printing.doNotLeave")}
        </p>
      </div>
    </div>
  );
}
