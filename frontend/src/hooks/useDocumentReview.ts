import { useState } from 'react';
import { ReviewApiError } from './useExtractionReview';

export type HumanReviewAction = 'APPROVE' | 'EDIT' | 'REJECT';

export interface DocumentReviewRequest {
  field_id: string;
  action: HumanReviewAction;
  edited_value?: string;
  comments?: string;
  edit_reason?: string;
  expected_version: number;
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
        const payload = await response.json().catch(() => null);
        if (response.status === 409 && payload) {
          const message = payload.message || 'This field was just modified by another reviewer';
          setError(message);
          throw new ReviewApiError(message, response.status, payload);
        }

        const errorText = typeof payload === 'string' ? payload : null;
        const message = errorText || response.statusText || 'Review submission failed';
        setError(message);
        throw new ReviewApiError(message, response.status);
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
