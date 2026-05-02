import { useState, useEffect, useCallback } from "react";

export interface ActionPlanItem {
  id: string;
  document_id: string;
  extracted_field_id?: string | null;
  item_type: string;
  title: string;
  description: string;
  priority: string;
  due_date?: string | null;
  due_date_source: string;
  responsible_department_id?: string | null;
  responsible_officer?: string | null;
  risk_if_ignored: string;
  suggested_next_step: string;
  source_evidence_links: Array<Record<string, unknown>>;
  source_evidence?: Record<string, unknown>;
  verification_status: string;
  verified_by_user_id?: string | null;
  verification_date?: string | null;
  completion_status: string;
  actual_completion_date?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
  department_name?: string | null;
  time_until_deadline?: string | null;
  status_color_code: string;
}

export const useActionPlan = (documentId?: string) => {
  const [data, setData] = useState<ActionPlanItem[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchActionPlan = useCallback(async () => {
    if (!documentId) {
      setError("Document ID is required");
      setData(null);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const response = await window.fetch(
        `/api/v1/documents/${documentId}/action-plan`,
      );
      if (!response.ok) {
        const text = await response.text();
        setError(
          text || response.statusText || "Failed to load action plan items",
        );
        setData(null);
        return;
      }

      const items: ActionPlanItem[] = await response.json();
      setData(items);
      setError(null);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to load action plan items";
      setError(message);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  useEffect(() => {
    fetchActionPlan();
  }, [fetchActionPlan]);

  return { data, loading, error, refetch: fetchActionPlan };
};
