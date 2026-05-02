import { useState } from 'react';

export type HumanReviewAction = 'APPROVE' | 'EDIT' | 'REJECT';

export interface DocumentReviewRequest {
  field_id: string;
  action: HumanReviewAction;
  edited_value?: string;
  comments?: string;
  edit_reason?: string;
}

export const useDocumentReview = (documentId?: string) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submitReview = async (reviewPayload: DocumentReviewRequest) => {
    if (!documentId) {
      setError('Document ID is required for review actions');
      throw new Error('Document ID is required for review actions');
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `/api/v1/documents/${documentId}/fields/${reviewPayload.field_id}/review`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(reviewPayload),
        }
      );

      if (!response.ok) {
        const errorText = await response.text();
        const message = errorText || response.statusText || 'Review submission failed';
        setError(message);
        throw new Error(message);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to submit review';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    submitReview,
    loading,
    error,
  };
};
