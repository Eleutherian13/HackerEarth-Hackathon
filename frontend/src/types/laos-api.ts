// TypeScript mirrors of the FastAPI Pydantic schemas.
// Keep in sync with backend/app/models/schemas/*.

export interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  user: UserResponse;
}

export interface DocumentListItem {
  id: string;
  filename: string;
  status: string;
  page_count: number | null;
  file_size_mb: number;
  is_text_based: boolean | null;
  uploaded_at: string | null;
  error_message: string | null;
}

export interface DocumentListResponse {
  total: number;
  page: number;
  per_page: number;
  pages: number;
  documents: DocumentListItem[];
}

export interface DocumentResponse {
  id: string;
  filename: string;
  status: string;
  page_count: number | null;
  file_size_bytes: number | null;
  is_text_based: boolean | null;
  error_message: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface DocumentPageStatus {
  page_number: number;
  has_text: boolean;
  text_length: number;
  extraction_quality: number | null;
  needs_manual_review: boolean;
  ocr_status: string | null;
}

export interface DocumentStatusResponse {
  document_id: string;
  filename: string;
  status: string;
  page_count: number | null;
  is_text_based: boolean | null;
  error_message: string | null;
  pages: DocumentPageStatus[];
}

export interface HighlightQuote {
  text?: string;
  page?: number;
  bbox?: number[] | { x: number; y: number; width: number; height: number };
  quote?: string;
}

export interface ExtractedFieldResponse {
  id: string;
  document_id: string;
  field_type: string;
  value: string;
  normalized_value: string | null;
  confidence_score: number;
  extraction_method: string;
  is_inferred: boolean;
  inference_rationale: string | null;
  source_page_ids: number[];
  source_quotes: HighlightQuote[];
  verification_status: string;
  version: number;
  verified_by_user_id: string | null;
  verified_at: string | null;
  edit_history: Record<string, unknown>[];
  reviewer_comments: string | null;
  created_at: string;
  updated_at: string;
  verification_status_badge?: { label: string; color_code: string } | null;
  reviewer_info?: Record<string, unknown> | null;
}

export interface FieldReviewRequest {
  action: string;
  comments?: string;
  expected_version: number;
  edited_value?: string;
  edit_reason?: string;
}

export interface ActionPlanItemResponse {
  id: string;
  document_id: string;
  extracted_field_id: string | null;
  item_type: string;
  title: string;
  description: string;
  priority: string;
  due_date: string | null;
  due_date_source: string;
  responsible_department_id: string | null;
  responsible_officer: string | null;
  risk_if_ignored: string | null;
  suggested_next_step: string | null;
  source_evidence_links: Array<Record<string, unknown>>;
  source_evidence: Record<string, unknown>;
  verification_status: string;
  version: number;
  verified_by_user_id: string | null;
  verification_date: string | null;
  completion_status: string;
  actual_completion_date: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  department_name: string | null;
  time_until_deadline: string | null;
  status_color_code: string;
}

export interface DashboardStatsResponse {
  total_verified_items: number;
  actions_by_priority: Record<string, number>;
  actions_by_type: Record<string, number>;
  overdue_items_count: number;
  due_within_7_days: number;
  due_within_30_days: number;
  department_breakdown: Array<{
    department_id: string;
    department_name: string;
    item_count: number;
  }>;
  weekly_trend: Array<{
    week_start: string;
    value: number;
  }>;
}

export interface DashboardActionItem {
  id: string;
  document_id: string;
  title: string;
  priority: string;
  completion_status: string;
  department_name: string | null;
  due_date: string | null;
  risk_if_ignored: string | null;
  suggested_next_step: string | null;
}

export interface DepartmentSummary {
  department_id: string;
  department_name: string;
  item_count: number;
}

export interface AuditLogEntry {
  id: string;
  event_type: string;
  user_id: string | null;
  document_id: string | null;
  entity_type: string;
  entity_id: string | null;
  action: string;
  changes: Record<string, unknown>;
  ip_address: string | null;
  request_id: string | null;
  user_agent: string | null;
  created_at: string;
}
