// TypeScript mirrors of the FastAPI Pydantic schemas.
// Keep in sync with backend/app/schemas/*.

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in?: number;
}

export interface UserResponse {
  id: string;
  username: string;
  email?: string;
  full_name?: string;
  role?: string;
  is_active?: boolean;
  department?: string;
}

export type DocumentStatus =
  | "uploaded"
  | "classifying"
  | "extracting"
  | "ocr"
  | "llm_extraction"
  | "action_plan"
  | "review"
  | "verified"
  | "failed";

export type DocumentType = "text" | "scanned" | "hybrid";

export interface DocumentResponse {
  id: string;
  filename: string;
  original_filename?: string;
  doc_type?: DocumentType;
  status: DocumentStatus;
  total_pages?: number;
  uploaded_at: string;
  uploaded_by?: string;
  case_number?: string;
  court?: string;
  bench?: string;
  judgment_date?: string;
  error_message?: string;
}

export interface DocumentStatusResponse {
  id: string;
  status: DocumentStatus;
  progress?: number;
  current_step?: string;
  error_message?: string;
}

export interface ExtractedFieldResponse {
  id: string;
  document_id: string;
  field_name: string;
  field_value: string;
  confidence: number;
  source_page?: number;
  source_paragraph?: string;
  status: "pending" | "approved" | "rejected" | "edited";
  reviewed_by?: string;
  reviewed_at?: string;
  notes?: string;
}

export interface FieldReviewRequest {
  field_id: string;
  status: "approved" | "rejected" | "edited";
  field_value?: string;
  notes?: string;
}

export type ActionStatus =
  | "pending_review"
  | "approved"
  | "rejected"
  | "in_progress"
  | "complied"
  | "escalated";

export type ActionPriority = "critical" | "high" | "medium" | "low";

export interface ActionPlanItemResponse {
  id: string;
  document_id: string;
  directive_text: string;
  section_type?: "final_order" | "interim_order" | "observation" | "condition";
  department?: string;
  responsible_officer?: string;
  deadline?: string;
  priority: ActionPriority;
  status: ActionStatus;
  confidence?: number;
  source_page?: number;
  source_paragraph?: string;
  depends_on?: string;
  appeal_route?: "compliance" | "appeal_likely" | "review";
  notes?: string;
}

export interface ActionPlanReviewRequest {
  action_id: string;
  status: ActionStatus;
  notes?: string;
}

export interface DashboardStatsResponse {
  active_cases: number;
  pending_review: number;
  due_in_7_days: number;
  escalated: number;
  departments_engaged: number;
  total_directives: number;
  complied: number;
}

export interface DashboardActionItem {
  id: string;
  case_number?: string;
  directive_text: string;
  department?: string;
  deadline?: string;
  days_left?: number;
  priority: ActionPriority;
  status: ActionStatus;
}

export interface DepartmentSummary {
  department: string;
  pending: number;
  total: number;
  next_deadline?: string;
}

export interface AuditLogEntry {
  id: string;
  actor: string;
  action: string;
  target_type: string;
  target_id: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}
