import { useState } from "react";

export type ActionPlanDecision = "APPROVE" | "MODIFY" | "REJECT";

export interface ActionPlanReviewRequest {
  action: ActionPlanDecision;
  modifications?: Record<string, string>;
  rationale?: string;
}

export interface ActionPlanEditRequest {
  title?: string;
  description?: string;
  priority?: string;
  due_date?: string;
  responsible_department_name?: string;
  responsible_officer?: string;
  risk_if_ignored?: string;
  suggested_next_step?: string;
  notes?: string;
}

export const useActionPlanReview = (documentId?: string) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submitReview = async (
    planItemId: string,
    reviewPayload: ActionPlanReviewRequest,
  ) => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `/api/v1/action-items/${planItemId}/review`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(reviewPayload),
        },
      );

      if (!response.ok) {
        const text = await response.text();
        const message =
          text || response.statusText || "Action plan review failed";
        setError(message);
        throw new Error(message);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Failed to submit action plan review";
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const editActionItem = async (
    planItemId: string,
    editPayload: ActionPlanEditRequest,
  ) => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/v1/action-items/${planItemId}/edit`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(editPayload),
      });

      if (!response.ok) {
        const text = await response.text();
        const message =
          text || response.statusText || "Action item edit failed";
        setError(message);
        throw new Error(message);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to edit action plan item";
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const finalizePlan = async () => {
    if (!documentId) {
      setError("Document ID is required to finalize action plan");
      throw new Error("Document ID is required to finalize action plan");
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `/api/v1/documents/${documentId}/finalize-plan`,
        {
          method: "POST",
        },
      );

      if (!response.ok) {
        const text = await response.text();
        const message =
          text || response.statusText || "Action plan finalization failed";
        setError(message);
        throw new Error(message);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to finalize action plan";
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { submitReview, editActionItem };

  const finalizePlan = async () => {
    if (!documentId) {
      setError("Document ID is required to finalize action plan");
      throw new Error("Document ID is required to finalize action plan");
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `/api/v1/documents/${documentId}/finalize-plan`,
        {
          method: "POST",
        },
      );

      if (!response.ok) {
        const text = await response.text();
        const message =
          text || response.statusText || "Action plan finalization failed";
        setError(message);
        throw new Error(message);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to finalize action plan";
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { submitReview, editActionItem, finalizePlan, loading, error };
};
