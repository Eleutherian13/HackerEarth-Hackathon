export interface CaseOverview {
  total_verified_extractions: number;
  verified_action_items: number;
  completed_actions: number;
  pending_actions: number;
}

export interface CaseDocumentPayload {
  id: string;
  case_number?: string | null;
  case_title?: string | null;
  court?: string | null;
  judgment_date?: string | null;
  parties?: string | null;
  bench?: string | null;
  filename?: string | null;
  processing_status?: string | null;
  uploaded_at?: string | null;
}

export interface CaseExtraction {
  id: string;
  field_type: string;
  value: string;
  confidence_score: number;
  verification_status: string;
  verified_by_user_id?: string | null;
  verified_at?: string | null;
  source_quotes?: string | null;
  is_inferred: boolean;
  inference_rationale?: string | null;
}

export interface CaseActionPlanItem {
  id: string;
  title: string;
  description?: string | null;
  item_type: string;
  priority: string;
  due_date?: string | null;
  due_date_source?: string | null;
  responsible_department_id?: string | null;
  responsible_department_name?: string | null;
  responsible_officer?: string | null;
  risk_if_ignored?: string | null;
  suggested_next_step?: string | null;
  verification_status: string;
  completion_status: string;
  actual_completion_date?: string | null;
  notes?: string | null;
  source_evidence?: string | null;
}

export interface CaseHistoryEntry {
  id: string;
  event_type: string;
  action: string;
  changes: string;
  user_id?: string | null;
  timestamp: string;
}

export interface CaseDetailResponse {
  document: CaseDocumentPayload;
  overview: CaseOverview;
  extractions: CaseExtraction[];
  action_plan: CaseActionPlanItem[];
  history: CaseHistoryEntry[];
}

const fetchJson = async <T>(url: string): Promise<T> => {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.statusText}`);
  }
  return response.json();
};

export const caseService = {
  fetchCaseDetail: async (documentId: string) => {
    return fetchJson<CaseDetailResponse>(`/api/v1/cases/${documentId}`);
  },
  fetchCaseHistory: async (documentId: string) => {
    return fetchJson<CaseHistoryEntry[]>(`/api/v1/cases/${documentId}/history`);
  },
  downloadCaseReport: async (documentId: string) => {
    const response = await fetch(`/api/v1/cases/${documentId}/report`);
    if (!response.ok) {
      throw new Error("Failed to download case report");
    }
    return response.blob();
  },
};
