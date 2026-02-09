/**
 * Admin Photo Gallery page
 * View, download, and reprint previous session photos
 */
import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../contexts/LanguageContext";
import { LoadingSpinner } from "../components/common";
import { SessionCard, SessionInfo } from "../components/admin";
import { adminApi } from "../services/adminApi";

interface Pagination {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
}

interface Filters {
  status: string;
}

export function AdminGallery() {
  const navigate = useNavigate();
  const { t } = useLanguage();

  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [pagination, setPagination] = useState<Pagination | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [filters, setFilters] = useState<Filters>({ status: "all" });

  const fetchSessions = useCallback(
    async (page = 1, append = false) => {
      try {
        if (page === 1) {
          setIsLoading(true);
        } else {
          setIsLoadingMore(true);
        }
        setError(null);

        const response = await adminApi.getExportableSessions({
          page,
          limit: 20,
          status: filters.status !== "all" ? filters.status : undefined,
        });

        if (response.success && response.data) {
          const data = response.data as {
            sessions: SessionInfo[];
            pagination: Pagination;
          };

          if (append) {
            setSessions((prev) => [...prev, ...data.sessions]);
          } else {
            setSessions(data.sessions);
          }
          setPagination(data.pagination);
        } else {
          setError(t("admin.gallery.loadError") || "Failed to load sessions");
        }
      } catch (err) {
        console.error("Failed to fetch sessions:", err);
        setError(t("admin.gallery.loadError") || "Failed to load sessions");
      } finally {
        setIsLoading(false);
        setIsLoadingMore(false);
      }
    },
    [filters.status, t]
  );

  useEffect(() => {
    if (!adminApi.isAuthenticated()) {
      navigate("/admin");
      return;
    }
    fetchSessions();
  }, [navigate, fetchSessions]);

  const handleLogout = async () => {
    try {
      await adminApi.logout();
    } catch (err) {
      console.error("Logout failed:", err);
    }
    navigate("/admin");
  };

  const handleSessionClick = (sessionId: string) => {
    navigate(`/admin/gallery/${sessionId}`);
  };

  const handleSelect = (id: string, selected: boolean) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (selected) {
        next.add(id);
      } else {
        next.delete(id);
      }
      return next;
    });
  };

  const handleClearSelection = () => {
    setSelectedIds(new Set());
  };

  const handleLoadMore = () => {
    if (pagination && pagination.page < pagination.total_pages) {
      fetchSessions(pagination.page + 1, true);
    }
  };

  const handleFilterChange = (newStatus: string) => {
    setFilters({ status: newStatus });
    setSelectedIds(new Set());
  };

  const handleBulkDownload = async () => {
    if (selectedIds.size === 0) return;

    try {
      const response = await adminApi.createBulkExport(Array.from(selectedIds));
      if (response.success && response.data) {
        alert(
          t("admin.gallery.bulk.exportStarted") ||
            `Export started for ${selectedIds.size} sessions`
        );
        // TODO: Navigate to export status or show progress
      }
    } catch (err) {
      console.error("Bulk export failed:", err);
      alert(t("admin.gallery.bulk.exportFailed") || "Export failed");
    }
  };

  const selectionMode = selectedIds.size > 0;
  const hasMore = pagination
    ? pagination.page < pagination.total_pages
    : false;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <LoadingSpinner message={t("admin.gallery.loading") || "Loading..."} />
      </div>
    );
  }

  return (
    <div className="h-screen overflow-y-auto bg-background">
      {/* Header */}
      <header className="sticky top-0 z-20 bg-background border-b border-gray-200 p-4 md:px-8">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate("/admin/dashboard")}
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
              {t("admin.gallery.detail.backToDashboard") || "Dashboard"}
            </button>
            <h1 className="text-2xl font-bold text-primary">
              {t("admin.gallery.title") || "Photo Gallery"}
            </h1>
          </div>
          <button
            onClick={handleLogout}
            className="btn-outline py-2 px-4 min-h-0 text-error border-error hover:bg-error hover:text-white"
          >
            {t("admin.dashboard.logout") || "Logout"}
          </button>
        </div>

        {/* Filters */}
        <div className="mt-4 flex flex-wrap gap-2">
          {["all", "COMPLETE", "PRINTED"].map((status) => (
            <button
              key={status}
              onClick={() => handleFilterChange(status)}
              className={`
                px-4 py-2 rounded-full text-sm font-medium transition-colors
                ${
                  filters.status === status
                    ? "bg-primary text-white"
                    : "bg-gray-100 text-text hover:bg-gray-200"
                }
              `}
            >
              {status === "all"
                ? t("admin.gallery.filters.all") || "All"
                : status === "COMPLETE"
                  ? t("admin.gallery.filters.complete") || "Complete"
                  : t("admin.gallery.filters.printed") || "Printed"}
            </button>
          ))}

          {pagination && (
            <span className="ml-auto text-sm text-text-muted self-center">
              {pagination.total}{" "}
              {t("admin.gallery.sessionsCount") || "sessions"}
            </span>
          )}
        </div>
      </header>

      {/* Content */}
      <main className="p-4 md:p-8 pb-24">
        {error ? (
          <div className="text-center py-12">
            <p className="text-error mb-4">{error}</p>
            <button onClick={() => fetchSessions()} className="btn-primary">
              {t("error.retry") || "Retry"}
            </button>
          </div>
        ) : sessions.length === 0 ? (
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
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <p className="text-lg">
              {t("admin.gallery.noSessions") || "No sessions found"}
            </p>
          </div>
        ) : (
          <>
            {/* Sessions Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
              {sessions.map((session) => (
                <SessionCard
                  key={session.id}
                  session={session}
                  isSelected={selectedIds.has(session.id)}
                  onSelect={handleSelect}
                  onClick={handleSessionClick}
                  selectionMode={selectionMode}
                />
              ))}
            </div>

            {/* Load More */}
            {hasMore && (
              <div className="text-center mt-8">
                <button
                  onClick={handleLoadMore}
                  disabled={isLoadingMore}
                  className="btn-outline py-2 px-6 min-h-0"
                >
                  {isLoadingMore
                    ? t("common.loading") || "Loading..."
                    : t("admin.gallery.loadMore") || "Load More"}
                </button>
              </div>
            )}
          </>
        )}
      </main>

      {/* Bulk Actions Bar */}
      {selectionMode && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg p-4 z-30">
          <div className="max-w-screen-xl mx-auto flex items-center justify-between gap-4">
            <span className="text-sm font-medium">
              {t("admin.gallery.bulk.selected")?.replace(
                "{{count}}",
                String(selectedIds.size)
              ) || `${selectedIds.size} selected`}
            </span>
            <div className="flex gap-3">
              <button
                onClick={handleClearSelection}
                className="btn-outline py-2 px-4 min-h-0 text-sm"
              >
                {t("admin.gallery.bulk.clear") || "Clear"}
              </button>
              <button
                onClick={handleBulkDownload}
                className="btn-primary py-2 px-4 min-h-0 text-sm"
              >
                {t("admin.gallery.bulk.download") || "Download Selected"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
