import { useState, useCallback, useRef, useEffect } from "react";
import { api, PrintJob } from "../services/api";

type PrintJobStatus =
  | "pending"
  | "processing"
  | "printing"
  | "completed"
  | "failed"
  | "cancelled"
  | "retry_pending";

interface PrintJobState {
  jobId: string | null;
  status: PrintJobStatus;
  progress: number;
  error: { code: string; message: string } | null;
  isPolling: boolean;
  job: PrintJob | null;
}

interface UsePrintJobOptions {
  pollingInterval?: number;
  onComplete?: (job: PrintJob) => void;
  onFailed?: (error: { code: string; message: string }) => void;
  onCancelled?: () => void;
  onStatusChange?: (status: PrintJobStatus) => void;
}

interface UsePrintJobReturn extends PrintJobState {
  startPolling: (jobId: string) => void;
  stopPolling: () => void;
  retry: () => Promise<boolean>;
  cancel: () => Promise<boolean>;
}

const initialState: PrintJobState = {
  jobId: null,
  status: "pending",
  progress: 0,
  error: null,
  isPolling: false,
  job: null,
};

export function usePrintJob(options: UsePrintJobOptions = {}): UsePrintJobReturn {
  const {
    pollingInterval = 1000,
    onComplete,
    onFailed,
    onCancelled,
    onStatusChange,
  } = options;

  const [state, setState] = useState<PrintJobState>(initialState);
  const intervalRef = useRef<number | null>(null);
  const mountedRef = useRef(true);
  const previousStatusRef = useRef<PrintJobStatus | null>(null);

  // Keep callback refs updated
  const onCompleteRef = useRef(onComplete);
  const onFailedRef = useRef(onFailed);
  const onCancelledRef = useRef(onCancelled);
  const onStatusChangeRef = useRef(onStatusChange);

  onCompleteRef.current = onComplete;
  onFailedRef.current = onFailed;
  onCancelledRef.current = onCancelled;
  onStatusChangeRef.current = onStatusChange;

  const clearPolling = useCallback(() => {
    if (intervalRef.current !== null) {
      window.clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const pollStatus = useCallback(async (jobId: string) => {
    try {
      const response = await api.getPrintJob(jobId);

      if (!mountedRef.current) return;

      if (response.success && response.data) {
        const job = response.data;
        const status = job.status as PrintJobStatus;

        setState((prev) => ({
          ...prev,
          status,
          progress: job.progress,
          error: job.error,
          job,
        }));

        // Trigger status change callback
        if (status !== previousStatusRef.current) {
          previousStatusRef.current = status;
          onStatusChangeRef.current?.(status);
        }

        // Handle terminal states
        if (status === "completed") {
          clearPolling();
          setState((prev) => ({ ...prev, isPolling: false }));
          onCompleteRef.current?.(job);
        } else if (status === "failed") {
          clearPolling();
          setState((prev) => ({ ...prev, isPolling: false }));
          if (job.error) {
            onFailedRef.current?.(job.error);
          }
        } else if (status === "cancelled") {
          clearPolling();
          setState((prev) => ({ ...prev, isPolling: false }));
          onCancelledRef.current?.();
        }
      }
    } catch (error) {
      console.error("Error polling print job status:", error);
    }
  }, [clearPolling]);

  const startPolling = useCallback(
    (jobId: string) => {
      clearPolling();
      previousStatusRef.current = null;

      setState({
        jobId,
        status: "pending",
        progress: 0,
        error: null,
        isPolling: true,
        job: null,
      });

      // Initial poll
      pollStatus(jobId);

      // Start polling interval
      intervalRef.current = window.setInterval(() => {
        pollStatus(jobId);
      }, pollingInterval);
    },
    [clearPolling, pollStatus, pollingInterval],
  );

  const stopPolling = useCallback(() => {
    clearPolling();
    setState((prev) => ({ ...prev, isPolling: false }));
  }, [clearPolling]);

  const retry = useCallback(async (): Promise<boolean> => {
    if (!state.jobId) return false;

    try {
      const response = await api.retryPrintJob(state.jobId);

      if (response.success && response.data) {
        // Restart polling
        startPolling(state.jobId);
        return true;
      }

      return false;
    } catch (error) {
      console.error("Error retrying print job:", error);
      return false;
    }
  }, [state.jobId, startPolling]);

  const cancel = useCallback(async (): Promise<boolean> => {
    if (!state.jobId) return false;

    try {
      const response = await api.cancelPrintJob(state.jobId);

      if (response.success) {
        clearPolling();
        setState((prev) => ({
          ...prev,
          status: "cancelled",
          isPolling: false,
        }));
        return true;
      }

      return false;
    } catch (error) {
      console.error("Error cancelling print job:", error);
      return false;
    }
  }, [state.jobId, clearPolling]);

  // Cleanup on unmount
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      clearPolling();
    };
  }, [clearPolling]);

  return {
    ...state,
    startPolling,
    stopPolling,
    retry,
    cancel,
  };
}
