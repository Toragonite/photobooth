import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../contexts/LanguageContext";

const AUTO_RETURN_SECONDS = 30;

export function CompletePage() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [countdown, setCountdown] = useState(AUTO_RETURN_SECONDS);

  // Auto-return to home
  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          // Clear session data
          sessionStorage.removeItem("sessionId");
          sessionStorage.removeItem("jobId");
          navigate("/");
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [navigate]);

  const handleNewSession = () => {
    sessionStorage.removeItem("sessionId");
    sessionStorage.removeItem("jobId");
    navigate("/");
  };

  return (
    <div className="center-content">
      <div className="text-center">
        {/* Success icon */}
        <div className="w-32 h-32 mx-auto mb-8 rounded-full bg-secondary flex items-center justify-center">
          <svg
            className="w-16 h-16 text-white"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={3}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M5 13l4 4L19 7"
            />
          </svg>
        </div>

        {/* Title */}
        <h1 className="text-5xl font-bold text-secondary mb-4">
          {t("complete.title")}
        </h1>

        {/* Message */}
        <p className="text-2xl text-text mb-2">{t("complete.message")}</p>
        <p className="text-xl text-text-muted mb-12">
          {t("complete.thankYou")}
        </p>

        {/* New session button */}
        <button
          onClick={handleNewSession}
          className="btn-primary text-xl px-12"
        >
          {t("complete.newSession")}
        </button>

        {/* Auto return countdown */}
        <p className="mt-8 text-text-muted">
          {t("complete.autoReturn").replace("{{seconds}}", String(countdown))}
        </p>
      </div>
    </div>
  );
}
