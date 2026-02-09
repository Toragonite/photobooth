/**
 * Admin Session Detail page
 * View session photos and reprint with frame/date/logo options
 */
import { useState, useEffect, useCallback } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useLanguage } from "../contexts/LanguageContext";
import { LoadingSpinner } from "../components/common";
import { adminApi } from "../services/adminApi";
import { api } from "../services/api";

interface PhotoInfo {
  id: string;
  index: number;
  file_exists: boolean;
  file_size: number;
  thumbnail_path: string;
  captured_at: string;
}

interface SessionData {
  session: {
    id: string;
    created_at: string;
    status: string;
    language: string;
    has_composite: boolean;
    files_cleaned: boolean;
  };
  photos: PhotoInfo[];
}

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

export function AdminSessionDetail() {
  const navigate = useNavigate();
  const { sessionId } = useParams<{ sessionId: string }>();
  const { t } = useLanguage();

  const [sessionData, setSessionData] = useState<SessionData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Reprint modal state
  const [showReprintModal, setShowReprintModal] = useState(false);
  const [copies, setCopies] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Reprint options
  const [frameType, setFrameType] = useState<FrameType>("classic");
  const [includeDate, setIncludeDate] = useState(true);
  const [includeLogo, setIncludeLogo] = useState(true);
  const [includeCustomText, setIncludeCustomText] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const [isDownloading, setIsDownloading] = useState(false);

  const fetchSessionData = useCallback(async () => {
    if (!sessionId) return;

    try {
      setIsLoading(true);
      setError(null);

      const response = await adminApi.getSessionPhotos(sessionId);

      if (response.success && response.data) {
        setSessionData(response.data as unknown as SessionData);
      } else {
        setError("Failed to load session");
      }
    } catch (err) {
      console.error("Failed to fetch session:", err);
      setError("Failed to load session");
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    if (!adminApi.isAuthenticated()) {
      navigate("/admin");
      return;
    }

    if (!sessionId) {
      navigate("/admin/gallery");
      return;
    }

    fetchSessionData();
  }, [navigate, sessionId, fetchSessionData]);

  // Generate preview when options change in modal
  const generatePreview = useCallback(async () => {
    if (!sessionId || !showReprintModal) return;

    try {
      setIsGenerating(true);
      const response = await api.generateComposite(
        sessionId,
        includeDate,
        includeLogo,
        frameType,
        "grid", // default layout
        includeCustomText
      );

      if (response.success && response.data) {
        setPreviewUrl(`${api.getCompositeUrl(sessionId)}?t=${Date.now()}`);
      }
    } catch (err) {
      console.error("Preview generation failed:", err);
    } finally {
      setIsGenerating(false);
    }
  }, [sessionId, showReprintModal, includeDate, includeLogo, frameType, includeCustomText]);

  // Regenerate preview when options change
  useEffect(() => {
    if (showReprintModal) {
      generatePreview();
    }
  }, [showReprintModal, generatePreview]);

  const handleDownload = async () => {
    if (!sessionId) return;

    try {
      setIsDownloading(true);
      await adminApi.downloadSessionPhotos(sessionId);
    } catch (err) {
      console.error("Download failed:", err);
      alert(t("admin.gallery.bulk.exportFailed") || "Download failed");
    } finally {
      setIsDownloading(false);
    }
  };

  const openReprintModal = () => {
    setShowReprintModal(true);
    setPreviewUrl(null); // Reset preview, will regenerate
  };

  const closeReprintModal = () => {
    setShowReprintModal(false);
    setPreviewUrl(null);
  };

  const handleReprint = async () => {
    if (!sessionId) return;

    try {
      setIsSubmitting(true);
      const response = await api.createPrintJob(sessionId, copies);

      if (response.success && response.data) {
        sessionStorage.setItem("jobId", response.data.job_id);
        navigate("/printing");
      } else {
        alert(response.error?.message || "Failed to create print job");
      }
    } catch (err) {
      console.error("Reprint failed:", err);
      alert("Failed to create print job");
    } finally {
      setIsSubmitting(false);
      closeReprintModal();
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <LoadingSpinner message={t("common.loading") || "Loading..."} />
      </div>
    );
  }

  if (error || !sessionData) {
    return (
      <div className="min-h-screen bg-background p-8">
        <div className="text-center py-12">
          <p className="text-error mb-4">{error || "Session not found"}</p>
          <button
            onClick={() => navigate("/admin/gallery")}
            className="btn-primary"
          >
            {t("admin.gallery.detail.backToGallery") || "Back to Gallery"}
          </button>
        </div>
      </div>
    );
  }

  const { session, photos } = sessionData;
  const date = new Date(session.created_at);
  const dateStr = date.toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  const timeStr = date.toLocaleTimeString("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div className="h-screen overflow-y-auto bg-background">
      {/* Header */}
      <header className="sticky top-0 z-20 bg-background border-b border-gray-200 p-4 md:px-8">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate("/admin/gallery")}
              className="btn-outline py-2 px-3 min-h-0 text-sm"
            >
              <svg
                className="w-4 h-4 mr-1 inline"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
              {t("admin.gallery.detail.backToGallery") || "Gallery"}
            </button>
            <div>
              <h1 className="text-xl font-bold text-text">
                {dateStr} {timeStr}
              </h1>
              <p className="text-sm text-text-muted">
                {session.status} · {session.language.toUpperCase()}
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="p-4 md:p-8 max-w-4xl mx-auto">
        {session.files_cleaned ? (
          <div className="text-center py-12 text-text-muted">
            <svg
              className="w-16 h-16 mx-auto mb-4 text-gray-300"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
            <p className="text-lg">
              {t("admin.gallery.detail.filesCleaned") ||
                "Files have been cleaned up"}
            </p>
          </div>
        ) : (
          <>
            {/* Photos Grid */}
            <section className="mb-8">
              <h2 className="text-lg font-semibold mb-4">
                {t("admin.gallery.detail.photos") || "Photos"} ({photos.length})
              </h2>
              <div className="grid grid-cols-2 gap-4">
                {photos.map((photo) => (
                  <div
                    key={photo.id}
                    className="aspect-[4/3] bg-gray-100 rounded-lg overflow-hidden"
                  >
                    {photo.file_exists ? (
                      <img
                        src={`/api/photos/${sessionId}/${photo.index}/thumbnail`}
                        alt={`Photo ${photo.index + 1}`}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-gray-400">
                        <span>Not available</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </section>

            {/* Composite */}
            {session.has_composite && (
              <section className="mb-8">
                <h2 className="text-lg font-semibold mb-4">
                  {t("admin.gallery.detail.composite") || "Composite"}
                </h2>
                <div className="bg-gray-100 rounded-lg overflow-hidden">
                  <img
                    src={`/api/composite/${sessionId}`}
                    alt="Composite"
                    className="w-full h-auto"
                  />
                </div>
              </section>
            )}

            {/* Actions */}
            <section className="flex gap-4 justify-center">
              <button
                onClick={handleDownload}
                disabled={isDownloading}
                className="btn-outline px-6 disabled:opacity-50"
              >
                <svg
                  className="w-5 h-5 mr-2 inline"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                  />
                </svg>
                {isDownloading
                  ? t("common.loading") || "Downloading..."
                  : t("admin.gallery.session.downloadAll") || "Download"}
              </button>
              {photos.length >= 4 && (
                <button
                  onClick={openReprintModal}
                  className="btn-primary px-6"
                >
                  <svg
                    className="w-5 h-5 mr-2 inline"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"
                    />
                  </svg>
                  {t("admin.gallery.session.reprint") || "Reprint"}
                </button>
              )}
            </section>
          </>
        )}
      </main>

      {/* Reprint Modal with Options */}
      {showReprintModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-xl">
            {/* Modal Header */}
            <div className="sticky top-0 bg-white border-b p-4 flex justify-between items-center">
              <h2 className="text-xl font-bold">
                {t("admin.gallery.reprint.title") || "Reprint Photo"}
              </h2>
              <button
                onClick={closeReprintModal}
                className="p-2 hover:bg-gray-100 rounded-full"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-6">
              {/* Composite Preview - smaller */}
              <div className="mb-8 rounded-lg overflow-hidden bg-gray-100 flex items-center justify-center min-h-[150px]">
                {isGenerating ? (
                  <LoadingSpinner message={t("preview.generating") || "Generating..."} />
                ) : previewUrl ? (
                  <img
                    src={previewUrl}
                    alt="Composite preview"
                    className="max-w-full max-h-[200px] object-contain"
                  />
                ) : (
                  <div className="text-gray-400 text-lg">Loading preview...</div>
                )}
              </div>

              {/* Frame Selector */}
              <div className="mb-8">
                <label className="block text-lg font-semibold mb-3">
                  {t("preview.selectFrame") || "Select Frame"}
                </label>
                <div className="flex flex-wrap gap-3">
                  {FRAME_OPTIONS.map((option) => (
                    <button
                      key={option.id}
                      onClick={() => setFrameType(option.id)}
                      disabled={isGenerating}
                      className={`
                        flex items-center gap-2 px-4 py-3 rounded-lg border-2 transition-all
                        ${
                          frameType === option.id
                            ? "border-primary bg-primary/10 text-primary"
                            : "border-gray-200 hover:border-primary/50"
                        }
                        ${isGenerating ? "opacity-50 cursor-not-allowed" : ""}
                      `}
                    >
                      <span className="text-xl">{option.icon}</span>
                      <span className="text-base font-medium">{t(option.labelKey)}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Options */}
              <div className="mb-8 flex flex-wrap gap-6">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeDate}
                    onChange={(e) => setIncludeDate(e.target.checked)}
                    disabled={isGenerating}
                    className="w-6 h-6 rounded accent-primary"
                  />
                  <span className="text-lg">{t("preview.includeDate") || "Show Date"}</span>
                </label>

                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeLogo}
                    onChange={(e) => setIncludeLogo(e.target.checked)}
                    disabled={isGenerating}
                    className="w-6 h-6 rounded accent-primary"
                  />
                  <span className="text-lg">{t("preview.includeLogo") || "Show Logo"}</span>
                </label>

                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeCustomText}
                    onChange={(e) => setIncludeCustomText(e.target.checked)}
                    disabled={isGenerating}
                    className="w-6 h-6 rounded accent-primary"
                  />
                  <span className="text-lg">{t("preview.includeCustomText") || "Custom Text"}</span>
                </label>
              </div>

              {/* Copy Selector */}
              <div className="mb-8">
                <label className="block text-lg font-semibold mb-3">
                  {t("admin.gallery.reprint.copies") || "Number of Copies"}
                </label>
                <div className="flex gap-4 justify-center">
                  {[1, 2, 3].map((num) => (
                    <button
                      key={num}
                      onClick={() => setCopies(num)}
                      className={`
                        w-16 h-16 rounded-lg text-2xl font-bold transition-colors
                        ${
                          copies === num
                            ? "bg-primary text-white"
                            : "bg-gray-100 text-text hover:bg-gray-200"
                        }
                      `}
                    >
                      {num}
                    </button>
                  ))}
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-4">
                <button
                  onClick={closeReprintModal}
                  className="flex-1 btn-outline text-lg py-4"
                  disabled={isSubmitting}
                >
                  {t("admin.gallery.reprint.cancel") || "Cancel"}
                </button>
                <button
                  onClick={handleReprint}
                  className="flex-1 btn-primary text-lg py-4"
                  disabled={isSubmitting || isGenerating}
                >
                  {isSubmitting
                    ? t("admin.gallery.reprint.submitting") || "Sending..."
                    : t("admin.gallery.reprint.confirm") || "Print"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
