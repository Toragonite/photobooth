import { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../contexts/LanguageContext";
import { adminApi } from "../services/adminApi";
import { api } from "../services/api";
import { LoadingSpinner, LayoutSelector, CopySelector } from "../components/common";
import { LayoutType, getPhotoCount } from "../types/layout";

// Frame type options (same as PreviewPage)
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

type Step = "layout" | "upload" | "frame" | "preview";

export function AdminUpload() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Step management
  const [currentStep, setCurrentStep] = useState<Step>("layout");

  // Layout selection
  const [layoutType, setLayoutType] = useState<LayoutType>("2x2");
  const requiredPhotos = getPhotoCount(layoutType);

  // Session & Photos
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [_uploadedPhotos, setUploadedPhotos] = useState<File[]>([]);
  const [photoThumbnails, setPhotoThumbnails] = useState<string[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  // Frame selection
  const [frameType, setFrameType] = useState<FrameType>("classic");
  const [includeDate, setIncludeDate] = useState(true);
  const [includeLogo, _setIncludeLogo] = useState(false);
  const [includeCustomText, setIncludeCustomText] = useState(true);

  // Preview & Print
  const [compositeUrl, setCompositeUrl] = useState<string | null>(null);
  const [framePreviewUrl, setFramePreviewUrl] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [copies, setCopies] = useState(1);
  const [isPrinting, setIsPrinting] = useState(false);
  const [printSuccess, setPrintSuccess] = useState(false);

  const [error, setError] = useState<string | null>(null);

  // Check auth on mount
  useEffect(() => {
    if (!adminApi.isAuthenticated()) {
      navigate("/admin");
    }
  }, [navigate]);

  // Create session when moving to upload step
  const handleLayoutConfirm = async () => {
    try {
      setError(null);
      const response = await adminApi.createUploadSession(layoutType);
      if (response.success && response.data) {
        setSessionId(response.data.session_id);
        setCurrentStep("upload");
      } else {
        setError("Failed to create session");
      }
    } catch (err) {
      console.error("Failed to create session:", err);
      setError("Failed to create session");
    }
  };

  // Handle file selection
  const handleFileSelect = useCallback(
    async (files: FileList | null) => {
      if (!files || !sessionId) return;

      const fileArray = Array.from(files).slice(0, requiredPhotos);
      if (fileArray.length < requiredPhotos) {
        setError(t("admin.upload.notEnoughPhotos").replace("{{count}}", String(requiredPhotos)));
        return;
      }

      setIsUploading(true);
      setError(null);

      try {
        const thumbnails: string[] = [];

        for (let i = 0; i < fileArray.length; i++) {
          const file = fileArray[i];

          // Create thumbnail preview
          const reader = new FileReader();
          const thumbnail = await new Promise<string>((resolve) => {
            reader.onload = (e) => resolve(e.target?.result as string);
            reader.readAsDataURL(file);
          });
          thumbnails.push(thumbnail);

          // Upload to server
          await adminApi.uploadPhoto(sessionId, i, file);
        }

        setUploadedPhotos(fileArray);
        setPhotoThumbnails(thumbnails);
        setCurrentStep("frame");
      } catch (err) {
        console.error("Upload failed:", err);
        setError("Failed to upload photos");
      } finally {
        setIsUploading(false);
      }
    },
    [sessionId, requiredPhotos, t]
  );

  // Handle drag & drop
  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      handleFileSelect(e.dataTransfer.files);
    },
    [handleFileSelect]
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  // Generate frame preview when in frame step and options change
  useEffect(() => {
    if (currentStep !== "frame" || !sessionId) return;

    const generatePreview = async () => {
      setIsGenerating(true);
      try {
        const response = await adminApi.generateUploadComposite(sessionId, {
          frame_type: frameType,
          include_date: includeDate,
          include_logo: includeLogo,
          include_custom_text: includeCustomText,
          layout_type: layoutType,
        });

        if (response.success && response.data) {
          setFramePreviewUrl(`${api.getCompositeUrl(sessionId)}?t=${Date.now()}`);
        }
      } catch (err) {
        console.error("Preview generation failed:", err);
      } finally {
        setIsGenerating(false);
      }
    };

    generatePreview();
  }, [currentStep, sessionId, frameType, includeDate, includeLogo, includeCustomText, layoutType]);

  // Move to preview step
  const handleFrameConfirm = async () => {
    if (!sessionId) return;

    // Use existing framePreviewUrl or wait for generation
    if (framePreviewUrl) {
      setCompositeUrl(framePreviewUrl);
      setCurrentStep("preview");
    } else {
      setIsGenerating(true);
      setError(null);

      try {
        const response = await adminApi.generateUploadComposite(sessionId, {
          frame_type: frameType,
          include_date: includeDate,
          include_logo: includeLogo,
          include_custom_text: includeCustomText,
          layout_type: layoutType,
        });

        if (response.success && response.data) {
          setCompositeUrl(`${api.getCompositeUrl(sessionId)}?t=${Date.now()}`);
          setCurrentStep("preview");
        } else {
          setError("Failed to generate composite");
        }
      } catch (err) {
        console.error("Composite generation failed:", err);
        setError("Failed to generate composite");
      } finally {
        setIsGenerating(false);
      }
    }
  };

  // Regenerate composite when options change (in preview step)
  useEffect(() => {
    if (currentStep !== "preview" || !sessionId) return;

    const regenerate = async () => {
      setIsGenerating(true);
      try {
        await adminApi.generateUploadComposite(sessionId, {
          frame_type: frameType,
          include_date: includeDate,
          include_logo: includeLogo,
          include_custom_text: includeCustomText,
          layout_type: layoutType,
        });
        setCompositeUrl(`${api.getCompositeUrl(sessionId)}?t=${Date.now()}`);
      } catch (err) {
        console.error("Regeneration failed:", err);
      } finally {
        setIsGenerating(false);
      }
    };

    regenerate();
  }, [currentStep, sessionId, frameType, includeDate, includeLogo, includeCustomText, layoutType]);

  // Handle print
  const handlePrint = async () => {
    if (!sessionId) return;

    setIsPrinting(true);
    setError(null);

    try {
      const response = await adminApi.printUploadSession(sessionId, copies);
      if (response.success) {
        setPrintSuccess(true);
      } else {
        setError("Failed to submit print job");
      }
    } catch (err) {
      console.error("Print failed:", err);
      setError("Failed to submit print job");
    } finally {
      setIsPrinting(false);
    }
  };

  // Reset and start over
  const handleReset = () => {
    setCurrentStep("layout");
    setSessionId(null);
    setUploadedPhotos([]);
    setPhotoThumbnails([]);
    setCompositeUrl(null);
    setFramePreviewUrl(null);
    setPrintSuccess(false);
    setError(null);
  };

  // Step indicators
  const steps: { key: Step; label: string }[] = [
    { key: "layout", label: t("admin.upload.step1") },
    { key: "upload", label: t("admin.upload.step2") },
    { key: "frame", label: t("admin.upload.step3") },
    { key: "preview", label: t("admin.upload.step4") },
  ];

  const currentStepIndex = steps.findIndex((s) => s.key === currentStep);

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-8">
      {/* Header */}
      <div className="max-w-4xl mx-auto mb-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-primary">
            {t("admin.upload.title")}
          </h1>
          <button
            onClick={() => navigate("/admin/dashboard")}
            className="btn-outline py-2 px-4"
          >
            {t("common.back")}
          </button>
        </div>

        {/* Step Indicator */}
        <div className="flex items-center justify-center gap-2 mt-6">
          {steps.map((step, index) => (
            <div key={step.key} className="flex items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  index <= currentStepIndex
                    ? "bg-primary text-white"
                    : "bg-gray-200 text-gray-500"
                }`}
              >
                {index + 1}
              </div>
              <span
                className={`ml-2 text-sm hidden sm:inline ${
                  index <= currentStepIndex ? "text-primary font-medium" : "text-gray-400"
                }`}
              >
                {step.label}
              </span>
              {index < steps.length - 1 && (
                <div
                  className={`w-8 h-0.5 mx-2 ${
                    index < currentStepIndex ? "bg-primary" : "bg-gray-200"
                  }`}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="max-w-4xl mx-auto mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-4xl mx-auto bg-white rounded-xl shadow-lg p-6">
        {/* Step 1: Layout Selection */}
        {currentStep === "layout" && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-center">
              {t("admin.upload.selectLayout")}
            </h2>
            <LayoutSelector value={layoutType} onChange={setLayoutType} />
            <p className="text-center text-text-muted">
              {t("admin.upload.requiredPhotos").replace("{{count}}", String(requiredPhotos))}
            </p>
            <div className="flex justify-center">
              <button onClick={handleLayoutConfirm} className="btn-primary py-3 px-8">
                {t("common.next")}
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Photo Upload */}
        {currentStep === "upload" && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-center">
              {t("admin.upload.uploadPhotos")}
            </h2>

            {/* Dropzone */}
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center cursor-pointer hover:border-primary transition-colors"
            >
              {isUploading ? (
                <LoadingSpinner message={t("admin.upload.uploading")} />
              ) : (
                <>
                  <div className="text-6xl mb-4">📸</div>
                  <p className="text-lg text-text-muted">
                    {t("admin.upload.dropzone")}
                  </p>
                  <p className="text-sm text-gray-400 mt-2">
                    {t("admin.upload.requiredPhotos").replace("{{count}}", String(requiredPhotos))}
                  </p>
                </>
              )}
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png"
              multiple
              onChange={(e) => handleFileSelect(e.target.files)}
              className="hidden"
            />

            <div className="flex justify-between">
              <button
                onClick={() => setCurrentStep("layout")}
                className="btn-outline py-2 px-6"
              >
                {t("common.back")}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Frame Selection */}
        {currentStep === "frame" && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-center">
              {t("admin.upload.selectFrame")}
            </h2>

            {/* Frame preview */}
            <div className="flex justify-center">
              {isGenerating ? (
                <div className="w-48 h-72 bg-gray-100 rounded-lg flex items-center justify-center">
                  <LoadingSpinner />
                </div>
              ) : framePreviewUrl ? (
                <img
                  src={framePreviewUrl}
                  alt="Frame preview"
                  className="max-h-[250px] rounded-lg shadow-md border"
                />
              ) : (
                <div className="flex justify-center gap-2 flex-wrap">
                  {photoThumbnails.map((thumb, i) => (
                    <img
                      key={i}
                      src={thumb}
                      alt={`Photo ${i + 1}`}
                      className="w-20 h-20 object-cover rounded-lg border"
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Frame options */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
              {FRAME_OPTIONS.map((frame) => (
                <button
                  key={frame.id}
                  onClick={() => setFrameType(frame.id)}
                  className={`p-3 rounded-lg border-2 transition-all ${
                    frameType === frame.id
                      ? "border-primary bg-primary/5"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <div className="text-2xl mb-1">{frame.icon}</div>
                  <div className="text-xs">{t(frame.labelKey)}</div>
                </button>
              ))}
            </div>

            {/* Options toggles */}
            <div className="flex flex-wrap justify-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeDate}
                  onChange={(e) => setIncludeDate(e.target.checked)}
                  className="w-5 h-5 rounded"
                />
                <span>{t("preview.includeDate")}</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeCustomText}
                  onChange={(e) => setIncludeCustomText(e.target.checked)}
                  className="w-5 h-5 rounded"
                />
                <span>{t("preview.includeText")}</span>
              </label>
            </div>

            <div className="flex justify-between">
              <button
                onClick={() => setCurrentStep("upload")}
                className="btn-outline py-2 px-6"
              >
                {t("common.back")}
              </button>
              <button
                onClick={handleFrameConfirm}
                disabled={isGenerating}
                className="btn-primary py-2 px-6"
              >
                {isGenerating ? t("common.loading") : t("common.next")}
              </button>
            </div>
          </div>
        )}

        {/* Step 4: Preview & Print */}
        {currentStep === "preview" && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-center">
              {t("admin.upload.previewAndPrint")}
            </h2>

            {/* Composite preview */}
            <div className="flex justify-center">
              {isGenerating ? (
                <div className="w-64 h-96 bg-gray-100 rounded-lg flex items-center justify-center">
                  <LoadingSpinner />
                </div>
              ) : compositeUrl ? (
                <img
                  src={compositeUrl}
                  alt="Composite preview"
                  className="max-h-[400px] rounded-lg shadow-lg"
                />
              ) : null}
            </div>

            {/* Frame selection (can still change) */}
            <div className="flex flex-wrap justify-center gap-2">
              {FRAME_OPTIONS.slice(0, 5).map((frame) => (
                <button
                  key={frame.id}
                  onClick={() => setFrameType(frame.id)}
                  className={`p-2 rounded-lg border transition-all ${
                    frameType === frame.id
                      ? "border-primary bg-primary/5"
                      : "border-gray-200"
                  }`}
                >
                  <span className="text-xl">{frame.icon}</span>
                </button>
              ))}
            </div>

            {/* Print success message */}
            {printSuccess ? (
              <div className="text-center space-y-4">
                <div className="text-6xl">✅</div>
                <p className="text-lg text-secondary font-medium">
                  {t("printing.success")}
                </p>
                <button onClick={handleReset} className="btn-primary py-3 px-8">
                  {t("admin.upload.newUpload")}
                </button>
              </div>
            ) : (
              <>
                {/* Copy selector */}
                <div className="flex justify-center">
                  <CopySelector value={copies} onChange={setCopies} max={10} />
                </div>

                {/* Action buttons */}
                <div className="flex justify-between">
                  <button
                    onClick={() => setCurrentStep("frame")}
                    className="btn-outline py-2 px-6"
                  >
                    {t("common.back")}
                  </button>
                  <button
                    onClick={handlePrint}
                    disabled={isPrinting || isGenerating}
                    className="btn-primary py-3 px-8"
                  >
                    {isPrinting ? t("printing.inProgress") : t("preview.print")}
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
