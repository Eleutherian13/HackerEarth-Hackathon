import { useCallback, useEffect, useState } from "react";
import {
  dashboardService,
  DashboardActionItem,
  DashboardFilters,
  DashboardSummary,
} from "../services/dashboardService";

export interface UseDashboardResult {
  summary: DashboardSummary | null;
  actions: DashboardActionItem[];
  departments: {
    department_id: string;
    department_name: string;
    item_count: number;
    overdue_count: number;
  }[];
  loading: boolean;
  error: string | null;
  page: number;
  perPage: number;
  total: number;
  pages: number;
  filters: DashboardFilters;
  refetch: () => Promise<void>;
  setFilters: (filters: DashboardFilters) => void;
}

export const useDashboard = (initialFilters: DashboardFilters = {}) => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [actions, setActions] = useState<DashboardActionItem[]>([]);
  const [departments, setDepartments] = useState<
    UseDashboardResult["departments"]
  >([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<DashboardFilters>({
    per_page: 25,
    ...initialFilters,
  });
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(0);
  const [page, setPage] = useState(filters.page ?? 1);
  const [perPage, setPerPage] = useState(filters.per_page ?? 25);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [summaryResult, actionsResult, departmentsResult] =
        await Promise.all([
          dashboardService.fetchSummary(filters),
          dashboardService.fetchActions(filters),
          dashboardService.fetchDepartments(filters),
        ]);
      setSummary(summaryResult);
      setActions(actionsResult.items);
      setTotal(actionsResult.total);
      setPage(actionsResult.page);
      setPerPage(actionsResult.per_page);
      setPages(actionsResult.pages);
      setDepartments(departmentsResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load dashboard");
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  const refetch = useCallback(async () => {
    await loadDashboard();
  }, [loadDashboard]);

  return {
    summary,
    actions,
    departments,
    loading,
    error,
    page,
    perPage,
    total,
    pages,
    filters,
    setFilters,
    refetch,
  };
};
