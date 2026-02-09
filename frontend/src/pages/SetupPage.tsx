import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../contexts/LanguageContext";

type Platform = "ios" | "android" | "macos" | "windows";

function detectPlatform(): Platform {
  const ua = navigator.userAgent.toLowerCase();

  if (/iphone|ipad|ipod/.test(ua)) {
    return "ios";
  }
  if (/android/.test(ua)) {
    return "android";
  }
  if (/macintosh|mac os x/.test(ua)) {
    return "macos";
  }
  return "windows";
}

export function SetupPage() {
  const navigate = useNavigate();
  const { t, toggleLanguage, language } = useLanguage();
  const [selectedPlatform, setSelectedPlatform] = useState<Platform>("ios");
  const [downloadStatus, setDownloadStatus] = useState<
    "idle" | "downloading" | "success" | "error"
  >("idle");

  useEffect(() => {
    setSelectedPlatform(detectPlatform());
  }, []);

  const handleDownload = async () => {
    setDownloadStatus("downloading");

    try {
      const response = await fetch("/api/setup/certificate");

      if (!response.ok) {
        throw new Error("Download failed");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "rootCA.pem";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setDownloadStatus("success");
    } catch {
      setDownloadStatus("error");
    }
  };

  const platforms: { key: Platform; icon: string }[] = [
    { key: "ios", icon: "" },
    { key: "android", icon: "" },
    { key: "macos", icon: "" },
    { key: "windows", icon: "" },
  ];

  const steps = [1, 2, 3, 4, 5] as const;

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-2xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-xl font-bold text-primary">
            {t("setup.title")}
          </h1>
          <button
            onClick={toggleLanguage}
            className="text-sm text-gray-600 hover:text-primary transition-colors px-3 py-1 rounded-full border border-gray-300 hover:border-primary"
          >
            {language === "ko" ? "English" : "한국어"}
          </button>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-8">
        {/* Subtitle */}
        <p className="text-center text-gray-600 mb-8">{t("setup.subtitle")}</p>

        {/* Download Section */}
        <section className="bg-white rounded-2xl shadow-md p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-2">
            {t("setup.download")}
          </h2>
          <p className="text-sm text-gray-600 mb-4">{t("setup.downloadDesc")}</p>

          <button
            onClick={handleDownload}
            disabled={downloadStatus === "downloading"}
            className={`w-full py-4 px-6 rounded-xl text-white font-medium text-lg
              transition-all duration-200 flex items-center justify-center gap-3
              ${
                downloadStatus === "downloading"
                  ? "bg-gray-400 cursor-not-allowed"
                  : downloadStatus === "success"
                    ? "bg-green-500 hover:bg-green-600"
                    : downloadStatus === "error"
                      ? "bg-red-500 hover:bg-red-600"
                      : "bg-primary hover:bg-primary-dark shadow-lg hover:shadow-xl"
              }`}
          >
            {downloadStatus === "downloading" ? (
              <>
                <svg
                  className="animate-spin h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                {t("setup.downloading")}
              </>
            ) : downloadStatus === "success" ? (
              <>
                <svg
                  className="h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                {t("setup.downloadSuccess")}
              </>
            ) : downloadStatus === "error" ? (
              <>
                <svg
                  className="h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
                {t("setup.downloadError")}
              </>
            ) : (
              <>
                <svg
                  className="h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                  />
                </svg>
                {t("setup.download")} (rootCA.pem)
              </>
            )}
          </button>
        </section>

        {/* Installation Guide Section */}
        <section className="bg-white rounded-2xl shadow-md p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">
            {t("setup.installGuide")}
          </h2>

          {/* Platform Tabs */}
          <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
            {platforms.map(({ key }) => (
              <button
                key={key}
                onClick={() => setSelectedPlatform(key)}
                className={`flex-shrink-0 px-4 py-2 rounded-full text-sm font-medium transition-all
                  ${
                    selectedPlatform === key
                      ? "bg-primary text-white shadow-md"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
              >
                {t(`setup.${key}.title`)}
              </button>
            ))}
          </div>

          {/* Steps */}
          <div className="space-y-3">
            {steps.map((stepNum) => (
              <div
                key={stepNum}
                className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl"
              >
                <span className="flex-shrink-0 w-7 h-7 bg-primary text-white rounded-full flex items-center justify-center text-sm font-bold">
                  {stepNum}
                </span>
                <p className="text-gray-700 text-sm leading-relaxed pt-0.5">
                  {t(`setup.${selectedPlatform}.step${stepNum}`)}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* Note */}
        <p className="text-center text-sm text-gray-500 mb-6">
          {t("setup.note")}
        </p>

        {/* Start Button */}
        <button
          onClick={() => navigate("/")}
          className="w-full py-4 px-6 bg-green-500 hover:bg-green-600 text-white font-medium text-lg rounded-xl
            shadow-lg hover:shadow-xl transition-all duration-200 flex items-center justify-center gap-2"
        >
          <svg
            className="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
          {t("setup.startPhotobooth")}
        </button>
      </main>
    </div>
  );
}
