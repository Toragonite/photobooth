/**
 * API client for PhotoBooth backend
 */

const API_BASE = "/api";

interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
  };
}

interface ErrorInterceptor {
  onError?: (error: Error, response?: Response) => void;
  onAuthError?: () => void;
  onServerError?: () => void;
}

interface Session {
  session_id: string;
  language: string;
  status: string;
  created_at: string;
  completed_at: string | null;
  photos: Photo[];
  photo_count: number;
  max_photos: number;
  composite_url: string | null;
}

interface Photo {
  id: string;
  index: number;
  thumbnail_url: string;
  captured_at: string;
}

interface PrintJob {
  job_id: string;
  session_id: string;
  status: string;
  copies: number;
  progress: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error: {
    code: string;
    message: string;
  } | null;
  retry_count: number;
}

interface PublicSettings {
  default_language: string;
  countdown_options: number[];
  default_countdown: number;
  sound_enabled: boolean;
  max_copies: number;
  logo_enabled: boolean;
  date_format: string;
}

interface CompositeResult {
  composite_id: string;
  composite_url: string;
  thumbnail_url: string;
  dimensions: {
    width: number;
    height: number;
    dpi: number;
  };
}

class ApiClient {
  private interceptor: ErrorInterceptor | null = null;

  setInterceptor(interceptor: ErrorInterceptor): void {
    this.interceptor = interceptor;
  }

  clearInterceptor(): void {
    this.interceptor = null;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
  ): Promise<ApiResponse<T>> {
    const url = `${API_BASE}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      const error = new Error(data.error?.message || `HTTP ${response.status}`);

      // Intercept specific errors
      if (response.status === 401) {
        this.interceptor?.onAuthError?.();
      } else if (response.status >= 500) {
        this.interceptor?.onServerError?.();
      }

      this.interceptor?.onError?.(error, response);
      throw error;
    }

    return data;
  }

  // Session endpoints
  async createSession(language: string = "ko"): Promise<ApiResponse<Session>> {
    return this.request("/session", {
      method: "POST",
      body: JSON.stringify({ language }),
    });
  }

  async getSession(sessionId: string): Promise<ApiResponse<Session>> {
    return this.request(`/session/${sessionId}`);
  }

  async updateSessionLanguage(
    sessionId: string,
    language: string,
  ): Promise<ApiResponse<{ session_id: string; language: string }>> {
    return this.request(`/session/${sessionId}/language`, {
      method: "PATCH",
      body: JSON.stringify({ language }),
    });
  }

  async abandonSession(
    sessionId: string,
  ): Promise<ApiResponse<{ session_id: string; status: string }>> {
    return this.request(`/session/${sessionId}`, {
      method: "DELETE",
    });
  }

  // Photo endpoints
  async uploadPhoto(
    sessionId: string,
    index: number,
    photoBlob: Blob,
  ): Promise<
    ApiResponse<{ photo_id: string; index: number; thumbnail_url: string }>
  > {
    const formData = new FormData();
    formData.append("photo", photoBlob, "photo.jpg");
    formData.append("index", String(index));

    const response = await fetch(`${API_BASE}/session/${sessionId}/photos`, {
      method: "POST",
      body: formData,
    });

    return response.json();
  }

  async replacePhoto(
    sessionId: string,
    index: number,
    photoBlob: Blob,
  ): Promise<
    ApiResponse<{ photo_id: string; index: number; thumbnail_url: string }>
  > {
    const formData = new FormData();
    formData.append("photo", photoBlob, "photo.jpg");

    const response = await fetch(
      `${API_BASE}/session/${sessionId}/photos/${index}`,
      {
        method: "PUT",
        body: formData,
      },
    );

    return response.json();
  }

  getPhotoThumbnailUrl(photoId: string): string {
    return `${API_BASE}/photos/${photoId}/thumbnail`;
  }

  getPhotoFullUrl(photoId: string): string {
    return `${API_BASE}/photos/${photoId}/full`;
  }

  // Composite endpoints
  async generateComposite(
    sessionId: string,
    includeDate: boolean = true,
    includeLogo: boolean = false,
    frameType: string = "classic",
    layoutType: string = "2x2",
    includeCustomText: boolean = true,
    customText: string = "2026 Somang Youth\nRwanda missionary",
  ): Promise<ApiResponse<CompositeResult>> {
    return this.request(`/session/${sessionId}/composite`, {
      method: "POST",
      body: JSON.stringify({
        include_date: includeDate,
        include_logo: includeLogo,
        include_custom_text: includeCustomText,
        custom_text: customText,
        frame_type: frameType,
        layout_type: layoutType,
      }),
    });
  }

  getCompositeUrl(sessionId: string): string {
    return `${API_BASE}/composite/${sessionId}`;
  }

  getCompositeThumbnailUrl(sessionId: string): string {
    return `${API_BASE}/composite/${sessionId}/thumbnail`;
  }

  // Print endpoints
  async createPrintJob(
    sessionId: string,
    copies: number = 1,
  ): Promise<ApiResponse<PrintJob>> {
    return this.request("/print", {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId, copies }),
    });
  }

  async getPrintJob(jobId: string): Promise<ApiResponse<PrintJob>> {
    return this.request(`/print/${jobId}`);
  }

  async retryPrintJob(jobId: string): Promise<ApiResponse<PrintJob>> {
    return this.request(`/print/${jobId}/retry`, {
      method: "POST",
    });
  }

  async cancelPrintJob(
    jobId: string,
  ): Promise<ApiResponse<{ job_id: string; status: string }>> {
    return this.request(`/print/${jobId}/cancel`, {
      method: "POST",
    });
  }

  // Settings endpoints
  async getPublicSettings(): Promise<ApiResponse<PublicSettings>> {
    return this.request("/settings/public");
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await fetch(`${API_BASE}/health`);
    return response.json();
  }
}

export const api = new ApiClient();

export type {
  Session,
  Photo,
  PrintJob,
  PublicSettings,
  CompositeResult,
  ApiResponse,
};
