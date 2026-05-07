// FastAPI client for LAOS backend.
// All endpoint paths are relative to API_BASE_URL (default http://localhost:8000/api/v1).

import { API_BASE_URL } from "./api-config";
import type {
  ActionPlanItemResponse,
  ActionPlanReviewRequest,
  AuditLogEntry,
  DashboardActionItem,
  DashboardStatsResponse,
  DepartmentSummary,
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
  set(tokens: TokenResponse) {
    localStorage.setItem(ACCESS_KEY, tokens.access_token);
    localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
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

async function request<T>(
  path: string,
  init: RequestInit = {},
  retry = true
): Promise<T> {
  const headers = new Headers(init.headers ?? {});
  if (!headers.has("Accept")) headers.set("Accept", "application/json");
  const token = tokenStore.access;
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });

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
    const msg =
      (body as { detail?: string } | undefined)?.detail ?? `HTTP ${res.status}`;
    throw new ApiError(res.status, msg, body);
  }

  if (res.status === 204) return undefined as T;
  const ct = res.headers.get("content-type") ?? "";
  if (ct.includes("application/json")) return (await res.json()) as T;
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
    const tokens = (await res.json()) as TokenResponse;
    tokenStore.set(tokens);
    return true;
  } catch {
    return false;
  }
}

// ─── Auth ────────────────────────────────────────────────────────────────
export const authApi = {
  async login(username: string, password: string) {
    // OAuth2 password flow expects x-www-form-urlencoded
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
    const tokens = (await res.json()) as TokenResponse;
    tokenStore.set(tokens);
    return tokens;
  },
  async logout() {
    try {
      await request("/auth/logout", { method: "POST" });
    } finally {
      tokenStore.clear();
    }
  },
  me: () => request<UserResponse>("/auth/me"),
  changePassword: (current_password: string, new_password: string) =>
    request("/auth/change-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ current_password, new_password }),
    }),
};

// ─── Documents ───────────────────────────────────────────────────────────
export const documentsApi = {
  upload(file: File, onProgress?: (pct: number) => void) {
    return new Promise<DocumentResponse>((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const fd = new FormData();
      fd.append("file", file);
      xhr.open("POST", `${API_BASE_URL}/documents/upload`);
      const token = tokenStore.access;
      if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable && onProgress) onProgress((e.loaded / e.total) * 100);
      };
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText));
          } catch (e) {
            reject(new ApiError(xhr.status, "Invalid response"));
          }
        } else {
          reject(new ApiError(xhr.status, xhr.statusText || "Upload failed"));
        }
      };
      xhr.onerror = () => reject(new ApiError(0, "Network error"));
      xhr.send(fd);
    });
  },
  get: (id: string) => request<DocumentResponse>(`/documents/${id}`),
  status: (id: string) => request<DocumentStatusResponse>(`/documents/${id}/status`),
  fields: (id: string) =>
    request<ExtractedFieldResponse[]>(`/documents/${id}/fields`),
  reviewField: (id: string, payload: FieldReviewRequest) =>
    request<ExtractedFieldResponse>(`/documents/${id}/fields/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  finalizeReview: (id: string) =>
    request<DocumentResponse>(`/documents/${id}/finalize-review`, { method: "POST" }),
};

// ─── Action plan ─────────────────────────────────────────────────────────
export const actionPlanApi = {
  list: (documentId: string) =>
    request<ActionPlanItemResponse[]>(
      `/action-plan/documents/${documentId}/action-plan`
    ),
  review: (documentId: string, payload: ActionPlanReviewRequest) =>
    request<ActionPlanItemResponse>(
      `/action-plan/documents/${documentId}/action-plan/review`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }
    ),
  bulkUpdate: (documentId: string, items: ActionPlanItemResponse[]) =>
    request<ActionPlanItemResponse[]>(
      `/action-plan/documents/${documentId}/action-plan`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items }),
      }
    ),
  finalize: (documentId: string) =>
    request<ActionPlanItemResponse[]>(
      `/action-plan/documents/${documentId}/action-plan/finalize`,
      { method: "POST" }
    ),
};

// ─── Dashboard ───────────────────────────────────────────────────────────
export const dashboardApi = {
  summary: () => request<DashboardStatsResponse>("/dashboard/summary"),
  actions: () => request<DashboardActionItem[]>("/dashboard/actions"),
  departments: () => request<DepartmentSummary[]>("/dashboard/departments"),
  urgent: () => request<DashboardActionItem[]>("/dashboard/urgent"),
  search: (q: string) =>
    request<DashboardActionItem[]>(`/dashboard/search?q=${encodeURIComponent(q)}`),
  exportCsv: () => request<Blob>("/dashboard/export/csv"),
  exportPdfReport: () => request<Blob>("/dashboard/export/pdf-report"),
};

// ─── Admin ───────────────────────────────────────────────────────────────
export const adminApi = {
  auditLogs: () => request<AuditLogEntry[]>("/admin/audit-logs"),
  users: () => request<UserResponse[]>("/admin/users"),
  departments: () => request<DepartmentSummary[]>("/admin/departments"),
};
