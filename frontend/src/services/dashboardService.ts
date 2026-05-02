export interface DepartmentBreakdownItem {
  department_id: string;
  department_name: string;
  item_count: number;
  overdue_count: number;
}

export interface WeeklyTrendPoint {
  week_start: string;
  verified_count: number;
  pending_count: number;
  rejected_count: number;
}

export interface DashboardSummary {
  total_verified_items: number;
  actions_by_priority: Record<string, number>;
  actions_by_type: Record<string, number>;
  overdue_items_count: number;
  due_within_7_days: number;
  due_within_30_days: number;
  department_breakdown: DepartmentBreakdownItem[];
  weekly_trend: WeeklyTrendPoint[];
}

export interface DashboardActionItem {
  id: string;
  title: string;
  case_number?: string | null;
  court?: string | null;
  department_name?: string | null;
  priority_badge: string;
  due_date?: string | null;
  days_remaining?: number | null;
  status_chip: string;
  item_type: string;
  description: string;
  actual_completion_date?: string | null;
  completion_status: string;
  verified_date?: string | null;
  case_title?: string | null;
  parties?: string | null;
}

export interface DashboardActionsResponse {
  items: DashboardActionItem[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface DashboardFilters {
  department_id?: string;
  priority?: string[];
  type?: string[];
  status?: string[];
  due_date_from?: string;
  due_date_to?: string;
  search_query?: string;
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_order?: string;
}

const buildQueryString = (filters: DashboardFilters) => {
  const params = new URLSearchParams();

  Object.entries(filters).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") {
      return;
    }
    if (Array.isArray(value)) {
      value.forEach((item) => params.append(key, item));
      return;
    }
    params.set(key, String(value));
  });

  return params.toString();
};

const fetchJson = async <T>(url: string): Promise<T> => {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.statusText}`);
  }
  return response.json();
};

export const dashboardService = {
  fetchSummary: async (filters: DashboardFilters = {}) => {
    const qs = buildQueryString(filters);
    return fetchJson<DashboardSummary>(
      `/api/v1/dashboard/summary${qs ? `?${qs}` : ""}`,
    );
  },

  fetchActions: async (filters: DashboardFilters = {}) => {
    const qs = buildQueryString(filters);
    return fetchJson<DashboardActionsResponse>(
      `/api/v1/dashboard/actions${qs ? `?${qs}` : ""}`,
    );
  },

  fetchDepartments: async (filters: DashboardFilters = {}) => {
    const qs = buildQueryString(filters);
    return fetchJson<DepartmentBreakdownItem[]>(
      `/api/v1/dashboard/departments${qs ? `?${qs}` : ""}`,
    );
  },

  fetchUrgentActions: async () => {
    return fetchJson<DashboardActionItem[]>(`/api/v1/dashboard/urgent`);
  },

  searchActions: async (query: string) => {
    return fetchJson<DashboardActionItem[]>(
      `/api/v1/dashboard/search?search_query=${encodeURIComponent(query)}`,
    );
  },

  exportCsv: async (filters: DashboardFilters = {}) => {
    const qs = buildQueryString(filters);
    const response = await fetch(
      `/api/v1/dashboard/export/csv${qs ? `?${qs}` : ""}`,
    );
    if (!response.ok) {
      throw new Error("Failed to export CSV");
    }
    return response.blob();
  },

  exportPdf: async (filters: DashboardFilters = {}) => {
    const qs = buildQueryString(filters);
    const response = await fetch(
      `/api/v1/dashboard/export/pdf-report${qs ? `?${qs}` : ""}`,
    );
    if (!response.ok) {
      throw new Error("Failed to export PDF");
    }
    return response.blob();
  },

  markActionComplete: async (actionId: string) => {
    const response = await fetch(
      `/api/v1/dashboard/actions/${actionId}/complete`,
      {
        method: "POST",
      },
    );
    if (!response.ok) {
      throw new Error("Failed to mark action complete");
    }
    return response.json();
  },
};
