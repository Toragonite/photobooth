import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../contexts/LanguageContext";
import { useSettings } from "../contexts/SettingsContext";
import { useSession } from "../contexts/SessionContext";
import { api } from "../services/api";
import { LoadingSpinner, CopySelector } from "../components/common";

// Frame type options
type FrameType =
  | "classic"
  | "film_strip"
  | "polaroid"
  | "minimal"
  | "rounded"
  | "rwanda_diagonal"
  | "rwanda_grid_1x4"
  | "rwanda_mission_1"
  | "rwanda_mission_2"
  | "rwanda_mission_3";

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
  { id: "rwanda_diagonal", labelKey: "preview.frames.rwandaDiagonal", icon: "🇷🇼" },
  { id: "rwanda_grid_1x4", labelKey: "preview.frames.rwandaGrid1x4", icon: "🎨" },
  { id: "rwanda_mission_1", labelKey: "preview.frames.rwandaMission1", icon: "🌍" },
  { id: "rwanda_mission_2", labelKey: "preview.frames.rwandaMission2", icon: "🌊" },
  { id: "rwanda_mission_3", labelKey: "preview.frames.rwandaMission3", icon: "✝️" },
];

export function PreviewPage() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const { settings } = useSettings();
  const { sessionId, layoutType } = useSession();

  const [compositeUrl, setCompositeUrl] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(true);
  const [copies, setCopies] = useState(1);
  const [includeDate, setIncludeDate] = useState(true);
  const includeLogo = true;
  const [includeCustomText, setIncludeCustomText] = useState(true);
  const [frameType, setFrameType] = useState<FrameType>("classic");
  const [error, setError] = useState<string | null>(null);
  const [showOptionsModal, setShowOptionsModal] = useState(false);

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
          layoutType,
          includeCustomText,
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
  }, [sessionId, includeDate, includeLogo, includeCustomText, frameType, layoutType]);

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

      {/* Options - tablet+ inline, hidden on mobile (moved to modal) */}
      <div className="section-fixed hidden sm:flex h-36 flex-col justify-center gap-2">
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
              checked={includeCustomText}
              onChange={(e) => setIncludeCustomText(e.target.checked)}
              className="w-4 h-4 rounded accent-primary"
            />
            <span>{t("preview.includeCustomText")}</span>
          </label>
        </div>
      </div>

      {/* Actions - fixed height */}
      <div className="section-fixed h-16 flex gap-3 sm:gap-4 justify-center items-center">
        <button onClick={handleRetake} className="btn-outline py-2 sm:py-3 px-4 sm:px-6 min-h-0 text-sm sm:text-base">
          {t("preview.retakePhoto")}
        </button>

        {/* Mobile: Options button */}
        {showOptions && (
          <button
            onClick={() => setShowOptionsModal(true)}
            className="sm:hidden btn-outline py-2 px-4 min-h-0 text-sm"
          >
            <svg className="w-4 h-4 mr-1 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            {t("preview.options")}
          </button>
        )}

        <button
          onClick={handlePrint}
          disabled={isGenerating || !compositeUrl}
          className="btn-primary py-2 sm:py-3 px-4 sm:px-6 min-h-0 text-sm sm:text-base"
        >
          {t("preview.print")}
        </button>
      </div>

      {/* Mobile Options Modal */}
      {showOptionsModal && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50" onClick={() => setShowOptionsModal(false)}>
          <div className="bg-white rounded-t-2xl sm:rounded-2xl w-full sm:max-w-md max-h-[80vh] overflow-y-auto safe-bottom" onClick={(e) => e.stopPropagation()}>
            {/* Modal header */}
            <div className="sticky top-0 bg-white border-b p-4 flex justify-between items-center">
              <h2 className="text-lg font-bold">{t("preview.options")}</h2>
              <button onClick={() => setShowOptionsModal(false)} className="p-2 hover:bg-gray-100 rounded-full">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-4 space-y-6">
              {/* Frame selector */}
              <div>
                <label className="block text-sm font-semibold mb-3">{t("preview.selectFrame")}</label>
                <div className="grid grid-cols-2 gap-2">
                  {FRAME_OPTIONS.map((option) => (
                    <button
                      key={option.id}
                      onClick={() => setFrameType(option.id)}
                      className={`flex items-center gap-2 px-3 py-2.5 rounded-lg border-2 transition-all ${
                        frameType === option.id
                          ? "border-primary bg-primary/10 text-primary"
                          : "border-gray-200 hover:border-primary/50"
                      }`}
                    >
                      <span className="text-lg">{option.icon}</span>
                      <span className="text-sm font-medium">{t(option.labelKey)}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Copy selector */}
              <div>
                <label className="block text-sm font-semibold mb-3">{t("preview.copies")}</label>
                <div className="flex justify-center">
                  <CopySelector
                    value={copies}
                    onChange={setCopies}
                    max={settings.maxCopies}
                  />
                </div>
              </div>
            </div>

            {/* Done button */}
            <div className="p-4 border-t">
              <button onClick={() => setShowOptionsModal(false)} className="btn-primary w-full">
                {t("common.confirm")}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
