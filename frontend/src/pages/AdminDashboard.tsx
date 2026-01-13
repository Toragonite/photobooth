import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../contexts/LanguageContext";
import { LoadingSpinner } from "../components/common";
import { adminApi, SystemStatus } from "../services/adminApi";

export function AdminDashboard() {
  const navigate = useNavigate();
  const { t } = useLanguage();

  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await adminApi.getStatus();

      if (response.success && response.data) {
        setStatus(response.data);
      } else {
        setError("Failed to load status");
      }
    } catch (err) {
      console.error("Status fetch failed:", err);
      setError("Failed to load status");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // Check auth using adminApi helper
    if (!adminApi.isAuthenticated()) {
      navigate("/admin");
      return;
    }

    fetchStatus();
  }, [navigate, fetchStatus]);

  const handleLogout = async () => {
    try {
      await adminApi.logout();
    } catch (err) {
      console.error("Logout failed:", err);
    }
    navigate("/admin");
  };

  const handleTestPrint = async () => {
    try {
      const response = await adminApi.sendTestPrint("color_bars");
      if (response.success) {
        alert("Test print sent successfully!");
      } else {
        alert("Failed to send test print");
      }
    } catch (err) {
      console.error("Test print failed:", err);
      alert("Failed to send test print");
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <LoadingSpinner message={t("common.loading")} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-4 md:p-8">
      {/* Header */}
      <header className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-primary">
          {t("admin.dashboard.title")}
        </h1>
        <div className="flex gap-4">
          <button
            onClick={() => navigate("/")}
            className="btn-outline py-2 px-4 min-h-0"
          >
            {t("common.home")}
          </button>
          <button
            onClick={handleLogout}
            className="btn-outline py-2 px-4 min-h-0 text-error border-error hover:bg-error hover:text-white"
          >
            {t("admin.dashboard.logout")}
          </button>
        </div>
      </header>

      {error ? (
        <div className="text-center text-error">
          <p>{error}</p>
          <button onClick={fetchStatus} className="btn-primary mt-4">
            {t("error.retry")}
          </button>
        </div>
      ) : status ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* System Status */}
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">
              {t("admin.dashboard.status")}
            </h2>
            <div className="flex items-center gap-3">
              <div
                className={`w-4 h-4 rounded-full ${
                  status.overall_health === "healthy"
                    ? "bg-secondary"
                    : "bg-error"
                }`}
              />
              <span className="text-lg capitalize">
                {status.overall_health}
              </span>
            </div>
          </div>

          {/* Printer Status */}
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">
              {t("admin.dashboard.printer")}
            </h2>
            <div className="space-y-2">
              <p>
                <span className="text-text-muted">Name:</span>{" "}
                {status.printer.name}
              </p>
              <p>
                <span className="text-text-muted">Status:</span>{" "}
                {status.printer.status}
              </p>
              {status.printer.mock_mode && (
                <p className="text-warning text-sm">Mock Mode Enabled</p>
              )}
            </div>
          </div>

          {/* Storage Status */}
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">
              {t("admin.dashboard.storage")}
            </h2>
            <div className="space-y-3">
              <div className="w-full h-4 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all ${
                    status.storage.percent_used > 90
                      ? "bg-error"
                      : status.storage.percent_used > 70
                        ? "bg-warning"
                        : "bg-secondary"
                  }`}
                  style={{ width: `${status.storage.percent_used}%` }}
                />
              </div>
              <p className="text-text-muted">
                {status.storage.percent_used.toFixed(1)}% used •
                {(status.storage.free_bytes / 1024 ** 3).toFixed(1)} GB free
              </p>
            </div>
          </div>

          {/* Today's Activity */}
          <div className="card md:col-span-2 lg:col-span-1">
            <h2 className="text-xl font-semibold mb-4">
              {t("admin.dashboard.activity")}
            </h2>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-3xl font-bold text-primary">
                  {status.activity.prints_total}
                </p>
                <p className="text-sm text-text-muted">Total</p>
              </div>
              <div>
                <p className="text-3xl font-bold text-secondary">
                  {status.activity.prints_completed}
                </p>
                <p className="text-sm text-text-muted">Completed</p>
              </div>
              <div>
                <p className="text-3xl font-bold text-error">
                  {status.activity.prints_failed}
                </p>
                <p className="text-sm text-text-muted">Failed</p>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="card lg:col-span-2">
            <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
            <div className="flex flex-wrap gap-4">
              <button
                onClick={fetchStatus}
                className="btn-outline py-2 px-4 min-h-0"
              >
                Refresh Status
              </button>
              <button
                onClick={handleTestPrint}
                className="btn-outline py-2 px-4 min-h-0"
              >
                Test Print
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
