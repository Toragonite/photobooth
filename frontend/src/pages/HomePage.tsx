import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { useLanguage } from "../contexts/LanguageContext";
import { api } from "../services/api";
import { LoadingSpinner } from "../components/common";

export function HomePage() {
  const navigate = useNavigate();
  const { t, language } = useLanguage();
  const [isLoading, setIsLoading] = useState(false);

  const handleStart = async () => {
    try {
      setIsLoading(true);
      const response = await api.createSession(language);

      if (response.success && response.data) {
        // Store session ID for the flow
        sessionStorage.setItem("sessionId", response.data.session_id);
        navigate("/camera");
      }
    } catch (error) {
      console.error("Failed to create session:", error);
      // Still navigate for demo purposes
      navigate("/camera");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="center-content text-center">
      {/* Logo/Title area */}
      <div className="mb-12">
        <h1 className="text-5xl md:text-6xl font-bold text-primary mb-4">
          {t("home.title")}
        </h1>
        <p className="text-xl text-text-muted">{t("home.subtitle")}</p>
      </div>

      {/* 4-cut preview illustration */}
      <div className="mb-12">
        <div className="grid grid-cols-2 gap-2 w-48 h-64 mx-auto">
          {[0, 1, 2, 3].map((i) => (
            <div
              key={i}
              className="bg-primary-light rounded-lg flex items-center justify-center"
            >
              <svg
                className="w-12 h-12 text-primary opacity-50"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
            </div>
          ))}
        </div>
      </div>

      {/* Start button */}
      <button
        onClick={handleStart}
        disabled={isLoading}
        className="btn-primary text-2xl px-16 py-6 rounded-full
                   shadow-lg hover:shadow-xl transform hover:scale-105
                   transition-all duration-300"
      >
        {isLoading ? (
          <LoadingSpinner size="sm" color="white" />
        ) : (
          t("home.startButton")
        )}
      </button>

      {/* Admin link (subtle) */}
      <button
        onClick={() => navigate("/admin")}
        className="mt-16 text-text-muted text-sm hover:text-primary transition-colors"
      >
        {t("admin.title")}
      </button>
    </div>
  );
}
