import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../contexts/LanguageContext";
import { useSettings } from "../contexts/SettingsContext";
import { api } from "../services/api";
import { LoadingSpinner, CopySelector } from "../components/common";

// Frame type options
type FrameType = "classic" | "film_strip" | "polaroid" | "minimal" | "rounded";

interface FrameOption {
  id: FrameType;
  labelKey: string;
  icon: string;
}

const FRAME_OPTIONS: FrameOption[] = [
  { id: "classic", labelKey: "preview.frames.classic", icon: "🖼️" },
  { id: "film_strip", labelKey: "preview.frames.filmStrip", icon: "🎬" },
  { id: "polaroid", labelKey: "preview.frames.polaroid", icon: "📷" },
  { id: "minimal", labelKey: "preview.frames.minimal", icon: "⬜" },
  { id: "rounded", labelKey: "preview.frames.rounded", icon: "🔲" },
];

export function PreviewPage() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const { settings } = useSettings();

  const [compositeUrl, setCompositeUrl] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(true);
  const [copies, setCopies] = useState(1);
  const [includeDate, setIncludeDate] = useState(true);
  const [includeLogo, setIncludeLogo] = useState(settings.logoEnabled);
  const [frameType, setFrameType] = useState<FrameType>("classic");
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
          frameType,
        );

        if (response.success && response.data) {
          // Add timestamp to bust cache when regenerating
          setCompositeUrl(`${api.getCompositeUrl(sessionId)}?t=${Date.now()}`);
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
  }, [sessionId, includeDate, includeLogo, frameType]);

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

  const showOptions = !isGenerating && compositeUrl;

  return (
    <div className="flex flex-col h-full">
      {/* Title - fixed height */}
      <div className="section-fixed h-14 text-center flex flex-col justify-center">
        <h1 className="text-2xl font-bold text-primary">
          {t("preview.title")}
        </h1>
        <p className="text-text-muted text-sm">{t("preview.instruction")}</p>
      </div>

      {/* Composite preview - grows to fill space */}
      <div className="section-grow flex items-center justify-center py-2">
        {isGenerating ? (
          <LoadingSpinner message={t("preview.generating")} />
        ) : compositeUrl ? (
          <div className="h-full flex items-center justify-center">
            <img
              src={compositeUrl}
              alt="Composite preview"
              className="max-h-full max-w-full object-contain rounded-2xl shadow-lg"
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

      {/* Options - fixed height container */}
      <div className="section-fixed h-36 flex flex-col justify-center gap-2">
        {/* Frame selector */}
        <div
          className={`flex flex-wrap justify-center gap-1.5 transition-opacity duration-200 ${
            showOptions ? "opacity-100" : "opacity-0 pointer-events-none"
          }`}
        >
          {FRAME_OPTIONS.map((option) => (
            <button
              key={option.id}
              onClick={() => setFrameType(option.id)}
              className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg border-2 transition-all text-sm ${
                frameType === option.id
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-gray-200 hover:border-primary/50"
              }`}
            >
              <span>{option.icon}</span>
              <span className="text-xs">{t(option.labelKey)}</span>
            </button>
          ))}
        </div>

        {/* Copy selector & Toggles row */}
        <div
          className={`flex items-center justify-center gap-4 transition-opacity duration-200 ${
            showOptions ? "opacity-100" : "opacity-0 pointer-events-none"
          }`}
        >
          <CopySelector
            value={copies}
            onChange={setCopies}
            max={settings.maxCopies}
            label={t("preview.copies")}
          />

          <label className="flex items-center gap-1.5 cursor-pointer text-sm">
            <input
              type="checkbox"
              checked={includeDate}
              onChange={(e) => setIncludeDate(e.target.checked)}
              className="w-4 h-4 rounded accent-primary"
            />
            <span>{t("preview.includeDate")}</span>
          </label>

          <label className="flex items-center gap-1.5 cursor-pointer text-sm">
            <input
              type="checkbox"
              checked={includeLogo}
              onChange={(e) => setIncludeLogo(e.target.checked)}
              className="w-4 h-4 rounded accent-primary"
            />
            <span>{t("preview.includeLogo")}</span>
          </label>
        </div>
      </div>

      {/* Actions - fixed height */}
      <div className="section-fixed h-16 flex gap-4 justify-center items-center">
        <button onClick={handleRetake} className="btn-outline py-3 px-6 min-h-0">
          {t("preview.retakePhoto")}
        </button>

        <button
          onClick={handlePrint}
          disabled={isGenerating || !compositeUrl}
          className="btn-primary py-3 px-6 min-h-0"
        >
          {t("preview.print")}
        </button>
      </div>
    </div>
  );
}
