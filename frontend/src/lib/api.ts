// FastAPI client for the LAOS backend.
// All endpoint paths are relative to API_BASE_URL.

import { API_BASE_URL } from "./api-config";
import type {
  AuditLogEntry,
  DashboardStatsResponse,
  DocumentListResponse,
  DocumentResponse,
  DocumentStatusResponse,
  ExtractedFieldResponse,
  FieldReviewRequest,
  TokenResponse,
  UserResponse,
} from "@/types/laos-api";

const ACCESS_KEY = "laos_access_token";
const REFRESH_KEY = "laos_refresh_token";

export const tokenStore = {
  get access() {
    return localStorage.getItem(ACCESS_KEY);
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY);
  },
  set(accessToken: string, refreshToken?: string) {
    localStorage.setItem(ACCESS_KEY, accessToken);
    localStorage.setItem(REFRESH_KEY, refreshToken ?? accessToken);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, message: string, body?: unknown) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

const normalizePath = (path: string) => {
  if (path.startsWith("/api/v1")) {
    return path.slice("/api/v1".length) || "/";
  }
  return path;
};

const buildQuery = (params?: Record<string, string | number | undefined>) => {
  const search = new URLSearchParams();
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && `${value}` !== "") {
      search.set(key, String(value));
    }
  });
  const query = search.toString();
  return query ? `?${query}` : "";
};

export async function request<T>(
  path: string,
  init: RequestInit = {},
  retry = true,
): Promise<T> {
  const headers = new Headers(init.headers ?? {});
  if (!headers.has("Accept")) headers.set("Accept", "application/json");
  const token = tokenStore.access;
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${API_BASE_URL}${normalizePath(path)}`, { ...init, headers });

  if (res.status === 401 && retry && tokenStore.refresh) {
    const refreshed = await tryRefresh();
    if (refreshed) return request<T>(path, init, false);
  }

  if (!res.ok) {
    let body: unknown = undefined;
    try {
      body = await res.json();
    } catch {
      /* ignore */
    }
    const message = (body as { detail?: string } | undefined)?.detail ?? `HTTP ${res.status}`;
    throw new ApiError(res.status, message, body);
  }

  if (res.status === 204) return undefined as T;
  const contentType = res.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) return (await res.json()) as T;
  return (await res.blob()) as unknown as T;
}

async function tryRefresh(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: tokenStore.refresh }),
    });
    if (!res.ok) return false;
    const data = (await res.json()) as TokenResponse;
    tokenStore.set(data.access_token, data.access_token);
    return true;
  } catch {
    return false;
  }
}

// ─── Auth ────────────────────────────────────────────────────────────────
export const authApi = {
  async login(username: string, password: string) {
    const form = new URLSearchParams();
    form.set("username", username);
    form.set("password", password);
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form.toString(),
    });
    if (!res.ok) {
      let detail = "Login failed";
      try {
        detail = ((await res.json()) as { detail?: string }).detail ?? detail;
      } catch {
        /* ignore */
      }
      throw new ApiError(res.status, detail);
    }
    const data = (await res.json()) as TokenResponse;
    tokenStore.set(data.access_token, data.access_token);
    return data;
  },
  register: (payload: { email: string; full_name: string; password: string }) =>
    request<UserResponse>("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  logout: async () => {
    tokenStore.clear();
  },
  me: () => request<UserResponse>("/auth/me"),
  refresh: () => request<{ access_token: string; token_type: string }>("/auth/refresh", { method: "POST" }),
};

// ─── Documents ───────────────────────────────────────────────────────────
export const documentsApi = {
  list: (params?: Record<string, string | number | undefined>) =>
    request<DocumentListResponse>(`/documents/${buildQuery(params)}`),
  upload: (file: File, onProgress?: (pct: number) => void, metadata?: Record<string, unknown>) =>
    new Promise<DocumentResponse>((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const formData = new FormData();
      formData.append("file", file);
      if (metadata && Object.keys(metadata).length > 0) {
        formData.append("metadata", JSON.stringify(metadata));
      }

      xhr.open("POST", `${API_BASE_URL}/documents/upload`);
      const token = tokenStore.access;
      if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable && onProgress) {
          onProgress((event.loaded / event.total) * 100);
        }
      };
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText) as DocumentResponse);
          } catch {
            reject(new ApiError(xhr.status, "Invalid response"));
          }
          return;
        }
        reject(new ApiError(xhr.status, xhr.statusText || "Upload failed"));
      };
      xhr.onerror = () => reject(new ApiError(0, "Network error"));
      xhr.send(formData);
    }),
  get: (id: string) => request<DocumentResponse>(`/documents/${id}`),
  status: (id: string) => request<DocumentStatusResponse>(`/documents/${id}/status`),
  fields: (id: string) => request<{ document_id: string; total_fields: number; fields: ExtractedFieldResponse[] }>(`/review/documents/${id}/fields`),
  reviewField: (fieldId: string, payload: FieldReviewRequest) =>
    request<{ status: string; field: ExtractedFieldResponse }>(`/review/fields/${fieldId}/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  generateActionPlan: (id: string) =>
    request<{ document_id: string; generated_count: number; action_items: Array<Record<string, unknown>> }>(`/review/documents/${id}/generate-action-plan`, {
      method: "POST",
    }),
};

// ─── Action plan ─────────────────────────────────────────────────────────
export const actionPlanApi = {
  generate: (documentId: string) => documentsApi.generateActionPlan(documentId),
  complete: (actionItemId: string) => request<Record<string, unknown>>(`/dashboard/actions/${actionItemId}/complete`, { method: "POST" }),
};

// ─── Dashboard ───────────────────────────────────────────────────────────
export const dashboardApi = {
  summary: () => request<DashboardStatsResponse>("/dashboard/summary"),
  actions: (params?: Record<string, string | number | undefined>) =>
    request<{ items: Array<Record<string, unknown>>; total: number; page: number; per_page: number; pages: number }>(`/dashboard/actions${buildQuery(params)}`),
  departments: () => request<Array<Record<string, unknown>>>("/dashboard/departments"),
  urgent: (limit = 20) => request<Array<Record<string, unknown>>>(`/dashboard/urgent?limit=${limit}`),
  search: (query: string) => request<Array<Record<string, unknown>>>(`/dashboard/search?search_query=${encodeURIComponent(query)}`),
  exportCsv: () => request<Blob>("/dashboard/export/csv"),
  exportPdfReport: () => request<Blob>("/dashboard/export/pdf-report"),
  completeAction: (actionItemId: string) => actionPlanApi.complete(actionItemId),
};

// ─── Admin ───────────────────────────────────────────────────────────────
export const adminApi = {
  auditLogs: (params?: Record<string, string | number | undefined>) =>
    request<{ items: AuditLogEntry[]; total: number; page: number; per_page: number; pages: number }>(`/admin/audit-logs${buildQuery(params)}`),
  users: () => request<Array<Record<string, unknown>>>("/admin/users"),
  departments: () => request<Array<Record<string, unknown>>>("/admin/departments"),
};
