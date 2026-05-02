export interface AuditLogEntry {
  id: string;
  event_type: string;
  user_id?: string | null;
  document_id?: string | null;
  entity_type: string;
  entity_id?: string | null;
  action: string;
  changes: Record<string, unknown>;
  ip_address?: string | null;
  user_agent?: string | null;
  created_at: string;
}

export interface AuditLogResponse {
  items: AuditLogEntry[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface UserAdminEntry {
  id: string;
  email: string;
  full_name: string;
  role: string;
  department_id?: string | null;
  is_active: boolean;
}

export interface DepartmentAdminEntry {
  id: string;
  name: string;
  description?: string | null;
  active_user_count?: number | null;
}

export interface QueueStatus {
  processing: number;
  pending: number;
  failed: number;
  completed: number;
}

export interface SystemSettings {
  app_name: string;
  environment: string;
  version: string;
  audit_enabled: boolean;
  default_page_size: number;
}

const buildQueryString = (params: Record<string, unknown>) => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null) {
      return;
    }
    if (Array.isArray(value)) {
      value.forEach((item) => query.append(key, String(item)));
      return;
    }
    query.set(key, String(value));
  });
  return query.toString();
};

const fetchJson = async <T>(url: string): Promise<T> => {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.statusText}`);
  }
  return response.json();
};

export const adminService = {
  fetchAuditLogs: async (params: Record<string, unknown> = {}) => {
    const qs = buildQueryString(params);
    return fetchJson<AuditLogResponse>(
      `/api/v1/admin/audit-logs${qs ? `?${qs}` : ""}`,
    );
  },

  fetchUsers: async (params: Record<string, unknown> = {}) => {
    const qs = buildQueryString(params);
    return fetchJson<{ items: UserAdminEntry[]; total: number }>(
      `/api/v1/admin/users${qs ? `?${qs}` : ""}`,
    );
  },

  updateUser: async (
    userId: string,
    body: Partial<Pick<UserAdminEntry, "role" | "is_active">>,
  ) => {
    const response = await fetch(`/api/v1/admin/users/${userId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      throw new Error("Failed to update user");
    }
    return response.json() as Promise<UserAdminEntry>;
  },

  fetchDepartments: async (params: Record<string, unknown> = {}) => {
    const qs = buildQueryString(params);
    return fetchJson<{ items: DepartmentAdminEntry[]; total: number }>(
      `/api/v1/admin/departments${qs ? `?${qs}` : ""}`,
    );
  },

  fetchSystemSettings: async () => {
    return fetchJson<SystemSettings>(`/api/v1/admin/settings`);
  },

  fetchQueueStatus: async () => {
    return fetchJson<QueueStatus>(`/api/v1/admin/queue-status`);
  },
};
