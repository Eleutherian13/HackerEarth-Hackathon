import { useState, useEffect, useCallback, useRef } from 'react';

export interface ProcessingLogEntry {
  stage: string;
  status: string;
  message: string;
  timestamp: string;
  page_number?: number;
  confidence?: number;
  retry_count?: number;
}

export interface PagePreview {
  page_number: number;
  preview_text: string;
  confidence: number;
  is_low_confidence: boolean;
  has_text: boolean;
  has_ocr: boolean;
}

export interface DocumentStatusResponse {
  document: {
    id: string;
    filename: string;
    status: string;
    status_label?: string;
    status_color?: string;
    error_message?: string;
    page_count?: number;
    file_size_mb: number;
    is_text_based?: boolean;
    metadata: Record<string, string>;
    uploaded_by_department?: string;
    created_at: string;
    updated_at: string;
  };
  progress_percentage: number;
  current_stage: string;
  estimated_time_remaining_seconds?: number | null;
  processing_log: ProcessingLogEntry[];
  page_previews: PagePreview[];
  low_confidence_pages: number[];
  can_retry: boolean;
  retry_endpoint?: string | null;
  retry_count: number;
  processing_jobs: any[];
  extracted_fields: any[];
  action_plan_items: any[];
  summary: {
    total_fields_extracted: number;
    fields_verified: number;
    total_action_items: number;
    action_items_completed: number;
    action_items_pending: number;
  };
}

interface UseDocumentStatusOptions {
  autoRefresh?: boolean;
  processingIntervalMs?: number;
  idleIntervalMs?: number;
}

const PROCESSING_STATUSES = new Set([
  'UPLOADED',
  'CLASSIFYING',
  'EXTRACTING',
  'PENDING_REVIEW',
  'UNDER_REVIEW',
]);
const TERMINAL_STATUSES = new Set(['VERIFIED', 'REJECTED', 'FAILED']);

export const useDocumentStatus = (
  documentId: string | undefined,
  options: UseDocumentStatusOptions = {}
) => {
  const {
    autoRefresh = true,
    processingIntervalMs = 3000,
    idleIntervalMs = 30000,
  } = options;

  const [data, setData] = useState<DocumentStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAutoRefreshing, setIsAutoRefreshing] = useState(autoRefresh);
  const lastStatusRef = useRef<string | null>(null);
  const pollTimerRef = useRef<number | null>(null);

  const fetchDocumentStatus = useCallback(async () => {
    if (!documentId) {
      setError('Document ID is required');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const response = await window.fetch(`/api/v1/documents/${documentId}/status`);

      if (!response.ok) {
        if (response.status === 404) {
          setError('Document not found');
        } else {
          setError(`Error: ${response.statusText}`);
        }
        setData(null);
        return;
      }

      const statusData: DocumentStatusResponse = await response.json();
      setData(statusData);
      setError(null);

      const currentStatus = statusData.document.status;
      if (lastStatusRef.current && lastStatusRef.current !== currentStatus) {
        await new Promise((resolve) => setTimeout(resolve, 500));
      }
      lastStatusRef.current = currentStatus;

      if (TERMINAL_STATUSES.has(currentStatus)) {
        setIsAutoRefreshing(false);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch status';
      setError(message);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  useEffect(() => {
    fetchDocumentStatus();
  }, [documentId, fetchDocumentStatus]);

  useEffect(() => {
    if (!isAutoRefreshing || !documentId) {
      if (pollTimerRef.current) {
        window.clearTimeout(pollTimerRef.current);
      }
      return;
    }

    const status = data?.document.status ?? null;
    const interval = status && PROCESSING_STATUSES.has(status) ? processingIntervalMs : idleIntervalMs;

    pollTimerRef.current = window.setTimeout(async () => {
      await fetchDocumentStatus();
    }, interval);

    return () => {
      if (pollTimerRef.current) {
        window.clearTimeout(pollTimerRef.current);
      }
    };
  }, [isAutoRefreshing, documentId, data?.document.status, fetchDocumentStatus, processingIntervalMs, idleIntervalMs]);

  return {
    data,
    loading,
    error,
    refetch: fetchDocumentStatus,
    stopAutoRefresh: () => setIsAutoRefreshing(false),
    resumeAutoRefresh: () => setIsAutoRefreshing(true),
    isAutoRefreshing,
  };
};
