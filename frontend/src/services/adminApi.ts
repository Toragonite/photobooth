/**
 * Admin API client for PhotoBooth backend
 */

const API_BASE = "/api/admin";

interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
  };
}

export interface AdminLoginResponse {
  token: string;
  expires_at: string;
}

export interface PrinterInfo {
  name: string;
  status: string;
  connected: boolean;
  is_ready: boolean;
  paper_status: string;
  ink_status: string;
  queue_length: number;
  error_message: string | null;
}

export interface SystemStatus {
  overall_health: string;
  timestamp: string;
  printer: {
    name: string;
    model: string;
    status: string;
    health: string;
    mock_mode: boolean;
    queue_count?: number;
  };
  printers: PrinterInfo[];
  storage: {
    total_bytes: number;
    used_bytes: number;
    free_bytes: number;
    percent_used: number;
    health: string;
  };
  activity: {
    date: string;
    sessions_started: number;
    prints_total: number;
    prints_completed: number;
    prints_failed: number;
    prints_cancelled: number;
  };
}

export interface PrintHistoryJob {
  id: string;
  session_id: string;
  status: string;
  copies: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error_code: string | null;
  error_message: string | null;
  duration_seconds?: number;
  composite_thumbnail_url?: string;
}

export interface PrintHistoryResponse {
  jobs: PrintHistoryJob[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
  };
  summary: {
    total: number;
    completed: number;
    failed: number;
    cancelled: number;
    success_rate: number;
  };
}

export interface AdminSettings {
  display: Record<string, unknown>;
  print: Record<string, unknown>;
  system: Record<string, unknown>;
  network: Record<string, unknown>;
}

export interface StorageDetails {
  total_bytes: number;
  used_bytes: number;
  free_bytes: number;
  percent_used: number;
  sessions_count: number;
  photos_count: number;
  composites_count: number;
}

export interface CleanupResult {
  sessions_removed: number;
  photos_removed: number;
  bytes_freed: number;
  dry_run: boolean;
}

export interface ServiceInfo {
  name: string;
  display_name: string;
  status: string;
  description: string;
  can_restart: boolean;
}

export interface TestPattern {
  id: string;
  name: string;
  description: string;
}

export interface LogEntry {
  timestamp: string;
  level: string;
  source: string;
  message: string;
}

class AdminApiClient {
  // Fallback memory storage when localStorage is unavailable
  private _memoryToken: string | null = null;

  private getToken(): string | null {
    if (typeof window === "undefined") return null;
    try {
      return localStorage.getItem("adminToken") || this._memoryToken;
    } catch {
      return this._memoryToken;
    }
  }

  private getAuthHeaders(): HeadersInit {
    const token = this.getToken();
    return token
      ? {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        }
      : {
          "Content-Type": "application/json",
        };
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
  ): Promise<ApiResponse<T>> {
    const url = `${API_BASE}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        ...this.getAuthHeaders(),
        ...options.headers,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      // Handle auth errors
      if (response.status === 401) {
        this.clearToken();
      }
      throw new Error(data.error?.message || `HTTP ${response.status}`);
    }

    return data;
  }

  private clearToken(): void {
    this._memoryToken = null;
    if (typeof window === "undefined") return;
    try {
      localStorage.removeItem("adminToken");
      localStorage.removeItem("adminTokenExpires");
    } catch {
      // localStorage unavailable
    }
  }

  // Check if token is valid
  // Backend sends expires_at in UTC (ISO format with timezone)
  isAuthenticated(): boolean {
    const token = this.getToken();
    if (!token) return false;

    let expires: string | null = null;
    try {
      expires = localStorage.getItem("adminTokenExpires");
    } catch {
      // localStorage unavailable, assume valid if token exists
      return true;
    }

    if (expires) {
      // Parse the expiration time (backend sends UTC ISO string)
      // JavaScript Date automatically handles timezone conversion
      const expiresTime = new Date(expires).getTime();
      const nowTime = Date.now();
      if (expiresTime < nowTime) {
        this.clearToken();
        return false;
      }
    }

    return true;
  }

  // Authentication
  async login(pin: string): Promise<ApiResponse<AdminLoginResponse>> {
    const response = await fetch(`${API_BASE}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pin }),
    });

    const data = await response.json();

    if (data.success && data.data?.token) {
      try {
        localStorage.setItem("adminToken", data.data.token);
        localStorage.setItem("adminTokenExpires", data.data.expires_at);
        // Also store in memory as backup
        this._memoryToken = data.data.token;
        console.log("Token saved to localStorage and memory");
      } catch (e) {
        // localStorage may be blocked (e.g., Safari private mode)
        // Store in memory as fallback
        console.warn("localStorage unavailable, using memory storage", e);
        this._memoryToken = data.data.token;
      }
    }

    return data;
  }

  async logout(): Promise<ApiResponse<void>> {
    try {
      const response = await this.request<void>("/logout", {
        method: "POST",
      });
      return response;
    } finally {
      this.clearToken();
    }
  }

  // System status
  async getStatus(): Promise<ApiResponse<SystemStatus>> {
    return this.request("/status");
  }

  // Print history
  async getPrintHistory(params?: {
    page?: number;
    limit?: number;
    status?: string;
    from_date?: string;
    to_date?: string;
  }): Promise<ApiResponse<PrintHistoryResponse>> {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set("page", String(params.page));
    if (params?.limit) searchParams.set("limit", String(params.limit));
    if (params?.status) searchParams.set("status", params.status);
    if (params?.from_date) searchParams.set("from_date", params.from_date);
    if (params?.to_date) searchParams.set("to_date", params.to_date);

    const query = searchParams.toString();
    return this.request(`/print-history${query ? `?${query}` : ""}`);
  }

  // Settings
  async getSettings(): Promise<ApiResponse<AdminSettings>> {
    return this.request("/settings");
  }

  async updateSettings(
    settings: Partial<AdminSettings>,
  ): Promise<ApiResponse<{ updated_fields: string[] }>> {
    return this.request("/settings", {
      method: "PATCH",
      body: JSON.stringify(settings),
    });
  }

  // Storage
  async getStorageDetails(): Promise<ApiResponse<StorageDetails>> {
    return this.request("/storage");
  }

  async cleanupStorage(
    olderThanDays: number,
    dryRun: boolean = true,
  ): Promise<ApiResponse<CleanupResult>> {
    return this.request("/cleanup", {
      method: "POST",
      body: JSON.stringify({
        older_than_days: olderThanDays,
        dry_run: dryRun,
      }),
    });
  }

  async getCleanupPreview(
    olderThanDays: number,
  ): Promise<ApiResponse<CleanupResult>> {
    return this.request(`/cleanup/preview?older_than_days=${olderThanDays}`);
  }

  // Service management
  async getServices(): Promise<ApiResponse<ServiceInfo[]>> {
    return this.request("/services");
  }

  async restartService(
    serviceName: string,
  ): Promise<ApiResponse<{ status: string; message: string }>> {
    return this.request(`/service/${serviceName}/restart`, {
      method: "POST",
    });
  }

  // System control
  async reboot(options?: {
    delay?: number;
    force?: boolean;
  }): Promise<ApiResponse<{ message: string; scheduled_at: string }>> {
    return this.request("/system/reboot", {
      method: "POST",
      body: JSON.stringify({
        delay: options?.delay,
        force: options?.force ?? false,
      }),
    });
  }

  async cancelReboot(): Promise<ApiResponse<{ message: string }>> {
    return this.request("/system/reboot/cancel", {
      method: "POST",
    });
  }

  async getRebootStatus(): Promise<
    ApiResponse<{
      scheduled: boolean;
      scheduled_at?: string;
      delay_seconds?: number;
    }>
  > {
    return this.request("/system/reboot/status");
  }

  async shutdown(
    force: boolean = false,
  ): Promise<ApiResponse<{ message: string }>> {
    return this.request("/system/shutdown", {
      method: "POST",
      body: JSON.stringify({ force }),
    });
  }

  // Test print
  async getTestPatterns(): Promise<ApiResponse<TestPattern[]>> {
    return this.request("/test-print/patterns");
  }

  async sendTestPrint(
    patternType: string = "color_bars",
    printerName?: string,
  ): Promise<ApiResponse<{ job_id: string; printer_name?: string; message: string }>> {
    const body: Record<string, string> = { pattern_type: patternType };
    if (printerName) body.printer_name = printerName;
    return this.request("/test-print", {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  // Logs
  async getLogSources(): Promise<ApiResponse<string[]>> {
    return this.request("/logs/sources");
  }

  async getLogs(params?: {
    source?: string;
    level?: string;
    limit?: number;
    since?: string;
  }): Promise<ApiResponse<LogEntry[]>> {
    const searchParams = new URLSearchParams();
    if (params?.source) searchParams.set("source", params.source);
    if (params?.level) searchParams.set("level", params.level);
    if (params?.limit) searchParams.set("limit", String(params.limit));
    if (params?.since) searchParams.set("since", params.since);

    const query = searchParams.toString();
    return this.request(`/logs${query ? `?${query}` : ""}`);
  }

  getLogDownloadUrl(params?: { source?: string; since?: string }): string {
    const searchParams = new URLSearchParams();
    if (params?.source) searchParams.set("source", params.source);
    if (params?.since) searchParams.set("since", params.since);

    const query = searchParams.toString();
    return `${API_BASE}/logs/download${query ? `?${query}` : ""}`;
  }

  // Photo export
  async getExportableSessions(params?: {
    page?: number;
    limit?: number;
    status?: string;
  }): Promise<
    ApiResponse<{
      sessions: Array<{
        id: string;
        created_at: string;
        status: string;
        language: string;
        has_composite: boolean;
      }>;
      pagination: {
        page: number;
        limit: number;
        total: number;
        total_pages: number;
      };
    }>
  > {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set("page", String(params.page));
    if (params?.limit) searchParams.set("limit", String(params.limit));
    if (params?.status) searchParams.set("status", params.status);
    const query = searchParams.toString();
    return this.request(`/photos${query ? `?${query}` : ""}`);
  }

  async getSessionPhotos(sessionId: string): Promise<
    ApiResponse<{
      session_id: string;
      photos: Array<{ id: string; index: number; url: string }>;
      composite_url?: string;
    }>
  > {
    return this.request(`/photos/${sessionId}`);
  }

  getSessionDownloadUrl(sessionId: string): string {
    return `${API_BASE}/photos/${sessionId}/download`;
  }

  async downloadSessionPhotos(sessionId: string): Promise<void> {
    const url = `${API_BASE}/photos/${sessionId}/download`;
    const response = await fetch(url, {
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      if (response.status === 401) {
        this.clearToken();
      }
      throw new Error(`Download failed: HTTP ${response.status}`);
    }

    // Get filename from Content-Disposition header or use default
    const contentDisposition = response.headers.get("Content-Disposition");
    let filename = `session_${sessionId.slice(0, 8)}.zip`;
    if (contentDisposition) {
      const match = contentDisposition.match(/filename="?([^";\n]+)"?/);
      if (match) {
        filename = match[1];
      }
    }

    // Create blob and download
    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = downloadUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(downloadUrl);
  }

  async createBulkExport(sessionIds: string[]): Promise<
    ApiResponse<{
      job_id: string;
      sessions_count: number;
    }>
  > {
    return this.request("/export", {
      method: "POST",
      body: JSON.stringify({ session_ids: sessionIds }),
    });
  }

  async getExportStatus(jobId: string): Promise<
    ApiResponse<{
      job_id: string;
      status: string;
      progress: number;
      download_url?: string;
    }>
  > {
    return this.request(`/export/${jobId}/status`);
  }

  getExportDownloadUrl(jobId: string): string {
    return `${API_BASE}/export/${jobId}/download`;
  }

  // =============================================================================
  // Mobile Upload Methods
  // =============================================================================

  async createUploadSession(
    layoutType: string,
    language: string = "ko"
  ): Promise<
    ApiResponse<{
      session_id: string;
      layout_type: string;
      required_photos: number;
    }>
  > {
    return this.request("/upload/session", {
      method: "POST",
      body: JSON.stringify({ layout_type: layoutType, language }),
    });
  }

  async uploadPhoto(
    sessionId: string,
    index: number,
    file: File
  ): Promise<
    ApiResponse<{
      photo_id: string;
      index: number;
      thumbnail_url: string;
    }>
  > {
    const formData = new FormData();
    formData.append("photo", file);
    formData.append("index", String(index));

    const token = this.getToken();
    const response = await fetch(`${API_BASE}/upload/session/${sessionId}/photos`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });

    if (!response.ok) {
      if (response.status === 401) {
        this.clearToken();
      }
      const errorData = await response.json().catch(() => ({}));
      return {
        success: false,
        error: {
          code: "UPLOAD_FAILED",
          message: errorData.detail || `HTTP ${response.status}`,
        },
      };
    }

    return response.json();
  }

  async generateUploadComposite(
    sessionId: string,
    options: {
      frame_type: string;
      include_date: boolean;
      include_logo: boolean;
      include_custom_text: boolean;
      custom_text?: string;
      layout_type: string;
    }
  ): Promise<
    ApiResponse<{
      composite_path: string;
      composite_url: string;
    }>
  > {
    const { layout_type, ...bodyOptions } = options;
    return this.request(
      `/upload/session/${sessionId}/composite?layout_type=${layout_type}`,
      {
        method: "POST",
        body: JSON.stringify(bodyOptions),
      }
    );
  }

  async printUploadSession(
    sessionId: string,
    copies: number = 1
  ): Promise<
    ApiResponse<{
      job_id: string;
      status: string;
      copies: number;
    }>
  > {
    return this.request(`/upload/session/${sessionId}/print`, {
      method: "POST",
      body: JSON.stringify({ copies }),
    });
  }
}

export const adminApi = new AdminApiClient();
