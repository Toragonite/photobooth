import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../contexts/LanguageContext";
import { useSettings } from "../contexts/SettingsContext";
import { api } from "../services/api";
import { LoadingSpinner, CopySelector } from "../components/common";

export function PreviewPage() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const { settings } = useSettings();

  const [compositeUrl, setCompositeUrl] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(true);
  const [copies, setCopies] = useState(1);
  const [includeDate, setIncludeDate] = useState(true);
  const [includeLogo, setIncludeLogo] = useState(settings.logoEnabled);
  const [error, setError] = useState<string | null>(null);

  const sessionId = sessionStorage.getItem("sessionId");

  // Generate composite on mount
  useEffect(() => {
    const generateComposite = async () => {
      if (!sessionId) {
        navigate("/");
        return;
      }

      try {
        setIsGenerating(true);
        const response = await api.generateComposite(
          sessionId,
          includeDate,
          includeLogo,
        );

        if (response.success && response.data) {
          setCompositeUrl(api.getCompositeUrl(sessionId));
        } else {
          setError("Failed to generate composite");
        }
      } catch (err) {
        console.error("Composite generation failed:", err);
        setError("Failed to generate composite");
      } finally {
        setIsGenerating(false);
      }
    };

    generateComposite();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, includeDate, includeLogo]);

  const handlePrint = async () => {
    if (!sessionId) return;

    try {
      const response = await api.createPrintJob(sessionId, copies);

      if (response.success && response.data) {
        sessionStorage.setItem("jobId", response.data.job_id);
        navigate("/printing");
      }
    } catch (err) {
      console.error("Print job creation failed:", err);
      setError("Failed to start print job");
    }
  };

  const handleRetake = () => {
    navigate("/camera");
  };

  return (
    <div className="flex flex-col h-full">
      {/* Title */}
      <div className="text-center mb-4">
        <h1 className="text-3xl font-bold text-primary">
          {t("preview.title")}
        </h1>
        <p className="text-text-muted mt-1">{t("preview.instruction")}</p>
      </div>

      {/* Composite preview */}
      <div className="flex-1 flex items-center justify-center mb-4">
        {isGenerating ? (
          <LoadingSpinner message={t("preview.generating")} />
        ) : compositeUrl ? (
          <div className="max-h-[60vh] rounded-2xl overflow-hidden shadow-lg">
            <img
              src={compositeUrl}
              alt="Composite preview"
              className="max-h-[60vh] w-auto"
            />
          </div>
        ) : error ? (
          <div className="text-error text-center">
            <p>{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="btn-outline mt-4"
            >
              {t("error.retry")}
            </button>
          </div>
        ) : null}
      </div>

      {/* Options */}
      {!isGenerating && compositeUrl && (
        <div className="space-y-4 mb-6">
          {/* Copy selector */}
          <div className="flex items-center justify-center gap-4">
            <CopySelector
              value={copies}
              onChange={setCopies}
              max={settings.maxCopies}
              label={t("preview.copies")}
            />
          </div>

          {/* Toggles */}
          <div className="flex items-center justify-center gap-6">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={includeDate}
                onChange={(e) => setIncludeDate(e.target.checked)}
                className="w-5 h-5 rounded accent-primary"
              />
              <span>{t("preview.includeDate")}</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={includeLogo}
                onChange={(e) => setIncludeLogo(e.target.checked)}
                className="w-5 h-5 rounded accent-primary"
              />
              <span>{t("preview.includeLogo")}</span>
            </label>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-4 justify-center">
        <button onClick={handleRetake} className="btn-outline">
          {t("preview.retakePhoto")}
        </button>

        <button
          onClick={handlePrint}
          disabled={isGenerating || !compositeUrl}
          className="btn-primary"
        >
          {t("preview.print")}
        </button>
      </div>
    </div>
  );
}
