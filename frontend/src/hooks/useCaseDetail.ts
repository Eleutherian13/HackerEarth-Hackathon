import { useCallback, useEffect, useState } from "react";
import {
  caseService,
  CaseDetailResponse,
  CaseHistoryEntry,
} from "../services/caseService";

export interface UseCaseDetailResult {
  caseDetail: CaseDetailResponse | null;
  history: CaseHistoryEntry[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export const useCaseDetail = (documentId: string) => {
  const [caseDetail, setCaseDetail] = useState<CaseDetailResponse | null>(null);
  const [history, setHistory] = useState<CaseHistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadCaseDetail = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [detail, historyEntries] = await Promise.all([
        caseService.fetchCaseDetail(documentId),
        caseService.fetchCaseHistory(documentId),
      ]);
      setCaseDetail(detail);
      setHistory(historyEntries);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to load case details",
      );
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  useEffect(() => {
    void loadCaseDetail();
  }, [loadCaseDetail]);

  return {
    caseDetail,
    history,
    loading,
    error,
    refresh: loadCaseDetail,
  };
};
