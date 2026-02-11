import { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../contexts/LanguageContext";
import { LoadingSpinner } from "../components/common";
import {
  adminApi,
  SystemStatus,
  PrinterInfo,
  PrintQueueStatus,
  PrintQueueMetrics,
  PrintQueueEvent,
} from "../services/adminApi";

function PrinterStatusBadge({ status }: { status: string }) {
  const colorMap: Record<string, string> = {
    ready: "bg-secondary text-white",
    processing: "bg-primary text-white",
    printing: "bg-primary text-white",
    error: "bg-error text-white",
    offline: "bg-gray-400 text-white",
  };
  const cls = colorMap[status] || "bg-gray-300 text-text";
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${cls}`}>
      {status}
    </span>
  );
}

function PrinterCard({
  printer,
  onTestPrint,
}: {
  printer: PrinterInfo;
  onTestPrint: (name: string) => Promise<void>;
}) {
  return (
    <div className="border rounded-lg p-4 space-y-2">
      <div className="flex items-center justify-between">
        <span className="font-medium">{printer.name}</span>
        <PrinterStatusBadge status={printer.status} />
      </div>
      <div className="text-sm text-text-muted space-y-1">
        <p>
          Connected: {printer.connected ? "Yes" : "No"} | Queue:{" "}
          {printer.queue_length}
        </p>
        <p>
          Paper: {printer.paper_status} | Ink: {printer.ink_status}
        </p>
        {printer.error_message && (
          <p className="text-error text-xs">{printer.error_message}</p>
        )}
      </div>
      <button
        onClick={() => onTestPrint(printer.name)}
        disabled={!printer.connected}
        className="btn-outline py-1 px-3 min-h-0 text-sm disabled:opacity-50"
      >
        Test Print
      </button>
    </div>
  );
}

function CopyStatusBadge({ status }: { status: string }) {
  const colorMap: Record<string, string> = {
    queued: "bg-gray-400 text-white",
    printing: "bg-primary text-white",
    completed: "bg-secondary text-white",
    failed: "bg-error text-white",
  };
  const cls = colorMap[status] || "bg-gray-300 text-text";
  return (
    <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${cls}`}>
      {status}
    </span>
  );
}

function PrintQueueCard({
  queue,
  metrics,
  logs,
  isLoading,
}: {
  queue: PrintQueueStatus | null;
  metrics: PrintQueueMetrics | null;
  logs: PrintQueueEvent[];
  isLoading: boolean;
}) {
  const [showLogs, setShowLogs] = useState(false);

  if (isLoading && !queue) {
    return (
      <div className="card md:col-span-2">
        <h2 className="text-xl font-semibold mb-4">Print Queue</h2>
        <div className="flex items-center justify-center py-8">
          <LoadingSpinner message="Loading queue status..." />
        </div>
      </div>
    );
  }

  return (
    <div className="card md:col-span-2">
      <div className="flex items-center justify-between mb-4 gap-2">
        <h2 className="text-lg sm:text-xl font-semibold">Print Queue</h2>
        <div className="flex items-center gap-2 text-xs sm:text-sm text-text-muted flex-shrink-0">
          <span className={`w-2 h-2 rounded-full ${isLoading ? "bg-primary animate-pulse" : "bg-secondary"}`} />
          Auto-refresh (5s)
        </div>
      </div>

      {/* Queue Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <p className="text-2xl font-bold text-primary">
            {queue?.queue_length ?? 0}
          </p>
          <p className="text-xs text-text-muted">Queued</p>
        </div>
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <p className="text-2xl font-bold text-primary">
            {queue?.active_jobs ?? 0}
          </p>
          <p className="text-xs text-text-muted">Active Jobs</p>
        </div>
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <p className="text-2xl font-bold text-secondary">
            {metrics?.today?.completed_copies ?? 0}
          </p>
          <p className="text-xs text-text-muted">Completed Today</p>
        </div>
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <p className="text-2xl font-bold text-error">
            {metrics?.today?.failed_copies ?? 0}
          </p>
          <p className="text-xs text-text-muted">Failed Today</p>
        </div>
      </div>

      {/* Worker Status */}
      {queue?.workers && queue.workers.length > 0 && (
        <div className="mb-4">
          <h3 className="text-sm font-medium text-text-muted mb-2">Printer Workers</h3>
          <div className="grid gap-2 sm:grid-cols-2">
            {queue.workers.map((worker) => (
              <div
                key={worker.printer}
                className={`p-3 rounded-lg border ${
                  worker.is_busy ? "border-primary bg-primary/5" : "border-gray-200"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-sm">{worker.printer}</span>
                  <span
                    className={`px-2 py-0.5 rounded text-xs ${
                      worker.is_busy
                        ? "bg-primary text-white"
                        : "bg-gray-200 text-text-muted"
                    }`}
                  >
                    {worker.is_busy ? "Printing" : "Idle"}
                  </span>
                </div>
                {worker.current_task && (
                  <div className="mt-2 text-xs text-text-muted">
                    Job: {worker.current_task.job_id.slice(0, 8)}... •
                    Copy {worker.current_task.copy}
                  </div>
                )}
                <div className="mt-1 text-xs text-text-muted">
                  Today: {worker.completed_today} ✓ / {worker.failed_today} ✗
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Queued Tasks */}
      {queue?.queued_tasks && queue.queued_tasks.length > 0 && (
        <div className="mb-4">
          <h3 className="text-sm font-medium text-text-muted mb-2">
            Pending Tasks ({queue.queued_tasks.length})
          </h3>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {queue.queued_tasks.slice(0, 10).map((task, idx) => (
              <div
                key={`${task.job_id}-${idx}`}
                className="flex items-center justify-between text-sm p-2 bg-gray-50 rounded"
              >
                <span className="font-mono text-xs">
                  {task.job_id.slice(0, 8)}...
                </span>
                <span className="text-text-muted">Copy {task.copy}</span>
                <CopyStatusBadge status="queued" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Activity Logs Toggle */}
      <div className="border-t pt-3">
        <button
          onClick={() => setShowLogs(!showLogs)}
          className="text-sm text-primary hover:underline"
        >
          {showLogs ? "Hide" : "Show"} Recent Activity ({logs.length} events)
        </button>
        {showLogs && logs.length > 0 && (
          <div className="mt-2 space-y-1 max-h-48 overflow-y-auto">
            {logs.slice(0, 20).map((event, idx) => (
              <div
                key={`${event.job_id}-${event.timestamp}-${idx}`}
                className="flex items-start gap-2 text-xs p-2 bg-gray-50 rounded"
              >
                <span className="text-text-muted whitespace-nowrap">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </span>
                <CopyStatusBadge
                  status={
                    event.event_type.includes("completed")
                      ? "completed"
                      : event.event_type.includes("failed")
                        ? "failed"
                        : event.event_type.includes("started")
                          ? "printing"
                          : "queued"
                  }
                />
                <span className="flex-1">{event.message}</span>
                {event.printer && (
                  <span className="text-text-muted">[{event.printer}]</span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export function AdminDashboard() {
  const navigate = useNavigate();
  const { t } = useLanguage();

  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Print queue state
  const [queueStatus, setQueueStatus] = useState<PrintQueueStatus | null>(null);
  const [queueMetrics, setQueueMetrics] = useState<PrintQueueMetrics | null>(null);
  const [queueLogs, setQueueLogs] = useState<PrintQueueEvent[]>([]);
  const [isQueueLoading, setIsQueueLoading] = useState(false);
  const queueIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

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

  // Fetch print queue data
  const fetchQueueData = useCallback(async () => {
    try {
      setIsQueueLoading(true);
      const [queueRes, metricsRes, logsRes] = await Promise.all([
        adminApi.getPrintQueue(),
        adminApi.getPrintQueueMetrics(),
        adminApi.getPrintQueueLogs(50),
      ]);

      if (queueRes.success && queueRes.data) {
        setQueueStatus(queueRes.data);
      }
      if (metricsRes.success && metricsRes.data) {
        setQueueMetrics(metricsRes.data);
      }
      if (logsRes.success && logsRes.data) {
        setQueueLogs(logsRes.data.logs || []);
      }
    } catch (err) {
      console.error("Queue fetch failed:", err);
    } finally {
      setIsQueueLoading(false);
    }
  }, []);

  useEffect(() => {
    // Check auth using adminApi helper
    if (!adminApi.isAuthenticated()) {
      navigate("/admin");
      return;
    }

    fetchStatus();
    fetchQueueData();

    // Set up 5-second polling for queue data
    queueIntervalRef.current = setInterval(fetchQueueData, 5000);

    return () => {
      if (queueIntervalRef.current) {
        clearInterval(queueIntervalRef.current);
      }
    };
  }, [navigate, fetchStatus, fetchQueueData]);

  const handleLogout = async () => {
    try {
      await adminApi.logout();
    } catch (err) {
      console.error("Logout failed:", err);
    }
    navigate("/admin");
  };

  const handleTestPrint = async (printerName?: string) => {
    try {
      const response = await adminApi.sendTestPrint("color_bars", printerName);
      if (response.success) {
        const target = response.data?.printer_name || printerName || "default";
        alert(`Test print sent to '${target}'!`);
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

  const printers = status?.printers || [];
  const hasManyPrinters = printers.length > 1;

  return (
    <div className="h-screen overflow-y-auto bg-background">
      {/* Header */}
      <header className="sticky top-0 z-20 bg-background border-b border-gray-200 p-4 md:px-8 safe-top">
        <div className="flex justify-between items-center gap-2">
          <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-primary truncate">
            {t("admin.dashboard.title")}
          </h1>
          <div className="flex gap-2 sm:gap-4 flex-shrink-0">
            <button
              onClick={() => navigate("/")}
              className="btn-outline py-2 px-3 sm:px-4 min-h-0 text-sm sm:text-base"
            >
              {t("common.home")}
            </button>
            <button
              onClick={handleLogout}
              className="btn-outline py-2 px-3 sm:px-4 min-h-0 text-sm sm:text-base text-error border-error hover:bg-error hover:text-white"
            >
              {t("admin.dashboard.logout")}
            </button>
          </div>
        </div>
      </header>

      <div className="p-4 md:p-8 pb-12">
      {error ? (
        <div className="text-center text-error">
          <p>{error}</p>
          <button onClick={fetchStatus} className="btn-primary mt-4">
            {t("error.retry")}
          </button>
        </div>
      ) : status ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
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
                    : status.overall_health === "degraded"
                      ? "bg-warning"
                      : "bg-error"
                }`}
              />
              <span className="text-lg capitalize">
                {status.overall_health}
              </span>
            </div>
          </div>

          {/* Printer Status - Multi-printer or single */}
          <div className={`card ${hasManyPrinters ? "md:col-span-2" : ""}`}>
            <h2 className="text-xl font-semibold mb-4">
              {t("admin.dashboard.printer")}
              {hasManyPrinters && (
                <span className="text-sm font-normal text-text-muted ml-2">
                  ({printers.length} printers)
                </span>
              )}
            </h2>
            {printers.length > 0 ? (
              <div className={`grid gap-3 ${hasManyPrinters ? "grid-cols-1 sm:grid-cols-2" : "grid-cols-1"}`}>
                {printers.map((p) => (
                  <PrinterCard
                    key={p.name}
                    printer={p}
                    onTestPrint={handleTestPrint}
                  />
                ))}
              </div>
            ) : (
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
            )}
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
                <p className="text-2xl sm:text-3xl font-bold text-primary">
                  {status.activity.prints_total}
                </p>
                <p className="text-sm text-text-muted">Total</p>
              </div>
              <div>
                <p className="text-2xl sm:text-3xl font-bold text-secondary">
                  {status.activity.prints_completed}
                </p>
                <p className="text-sm text-text-muted">Completed</p>
              </div>
              <div>
                <p className="text-2xl sm:text-3xl font-bold text-error">
                  {status.activity.prints_failed}
                </p>
                <p className="text-sm text-text-muted">Failed</p>
              </div>
            </div>
          </div>

          {/* Print Queue Monitor */}
          <PrintQueueCard
            queue={queueStatus}
            metrics={queueMetrics}
            logs={queueLogs}
            isLoading={isQueueLoading}
          />

          {/* Quick Actions */}
          <div className="card lg:col-span-2">
            <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
            <div className="flex flex-wrap gap-2 sm:gap-4">
              <button
                onClick={fetchStatus}
                className="btn-outline py-2 px-3 sm:px-4 min-h-0 text-sm sm:text-base"
              >
                Refresh Status
              </button>
              {!hasManyPrinters && (
                <button
                  onClick={() => handleTestPrint()}
                  className="btn-outline py-2 px-3 sm:px-4 min-h-0 text-sm sm:text-base"
                >
                  Test Print
                </button>
              )}
              <button
                onClick={() => navigate("/admin/gallery")}
                className="btn-primary py-2 px-3 sm:px-4 min-h-0 text-sm sm:text-base"
              >
                {t("admin.gallery.title") || "Photo Gallery"}
              </button>
              <button
                onClick={() => navigate("/admin/upload")}
                className="btn-primary py-2 px-3 sm:px-4 min-h-0 text-sm sm:text-base"
              >
                {t("admin.upload.title") || "Mobile Upload"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
      </div>
    </div>
  );
}
