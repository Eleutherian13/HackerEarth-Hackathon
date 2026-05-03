export type Status = "pending_review" | "approved" | "rejected" | "complied" | "escalated";
export type Priority = "critical" | "high" | "medium" | "low";
export type SectionType = "final_order" | "interim_order" | "observation" | "condition";

export interface Directive {
  id: string;
  text: string;
  sectionType: SectionType;
  department: string;
  deadline: string; // ISO
  daysLeft: number;
  priority: Priority;
  confidence: number; // 0-1
  status: Status;
  sourcePage: number;
  sourceParagraph: string;
  dependsOn?: string;
  appealRoute: "compliance" | "appeal_likely" | "review";
  limitationDays?: number;
}

export interface CaseFile {
  id: string;
  caseNo: string;
  title: string;
  court: string;
  bench: string;
  judgmentDate: string;
  ingestedAt: string;
  pdfType: "digital" | "scanned";
  pages: number;
  status: "ingested" | "classified" | "in_review" | "active" | "closed";
  directives: number;
  pending: number;
  dnaMatches: number;
  priority: Priority;
}

export const cases: CaseFile[] = [
  {
    id: "c-2041",
    caseNo: "W.P.(C) 8421/2026",
    title: "State of Karnataka vs. Karnataka Pollution Control Board",
    court: "High Court of Karnataka",
    bench: "Hon'ble Justice A. R. Mehta",
    judgmentDate: "2026-04-22",
    ingestedAt: "2026-04-23T09:14:00Z",
    pdfType: "digital",
    pages: 47,
    status: "in_review",
    directives: 9,
    pending: 3,
    dnaMatches: 2,
    priority: "critical",
  },
  {
    id: "c-2040",
    caseNo: "C.A. 1129/2025",
    title: "Union of India vs. Coastal Infra Pvt. Ltd.",
    court: "Supreme Court of India",
    bench: "Hon'ble CJI & Justice S. Iyer",
    judgmentDate: "2026-04-19",
    ingestedAt: "2026-04-20T11:02:00Z",
    pdfType: "digital",
    pages: 112,
    status: "active",
    directives: 14,
    pending: 0,
    dnaMatches: 4,
    priority: "high",
  },
  {
    id: "c-2039",
    caseNo: "W.P.(MD) 3340/2026",
    title: "Citizens Welfare Forum vs. Municipal Commissioner",
    court: "Madras High Court (Madurai Bench)",
    bench: "Hon'ble Justice K. Subramanian",
    judgmentDate: "2026-04-15",
    ingestedAt: "2026-04-16T07:45:00Z",
    pdfType: "scanned",
    pages: 23,
    status: "active",
    directives: 6,
    pending: 1,
    dnaMatches: 0,
    priority: "high",
  },
  {
    id: "c-2038",
    caseNo: "O.A. 412/2024",
    title: "Re: Solid Waste Management — Suo Motu",
    court: "National Green Tribunal",
    bench: "Principal Bench, New Delhi",
    judgmentDate: "2026-04-10",
    ingestedAt: "2026-04-11T16:20:00Z",
    pdfType: "digital",
    pages: 68,
    status: "active",
    directives: 11,
    pending: 0,
    dnaMatches: 3,
    priority: "medium",
  },
  {
    id: "c-2037",
    caseNo: "W.A. 882/2025",
    title: "Director of Education vs. Aided Schools Assn.",
    court: "Bombay High Court",
    bench: "Division Bench",
    judgmentDate: "2026-04-02",
    ingestedAt: "2026-04-03T08:00:00Z",
    pdfType: "scanned",
    pages: 31,
    status: "closed",
    directives: 5,
    pending: 0,
    dnaMatches: 1,
    priority: "low",
  },
];

export const directives: Directive[] = [
  {
    id: "d-9001",
    text: "The State Pollution Control Board shall submit a comprehensive compliance report on industrial effluent discharge for all 142 listed units within thirty (30) days from the date of this order.",
    sectionType: "final_order",
    department: "Pollution Control Board",
    deadline: "2026-05-22",
    daysLeft: 21,
    priority: "critical",
    confidence: 0.97,
    status: "pending_review",
    sourcePage: 38,
    sourceParagraph: "¶ 47",
    appealRoute: "compliance",
    limitationDays: 90,
  },
  {
    id: "d-9002",
    text: "The Member Secretary shall personally appear before this Court on the next date of hearing with the verified inspection register.",
    sectionType: "interim_order",
    department: "Pollution Control Board",
    deadline: "2026-05-08",
    daysLeft: 7,
    priority: "critical",
    confidence: 0.94,
    status: "approved",
    sourcePage: 39,
    sourceParagraph: "¶ 49",
    appealRoute: "compliance",
  },
  {
    id: "d-9003",
    text: "Department of Industries shall coordinate with the Board to facilitate inspections and shall not obstruct any process initiated under the Water Act, 1974.",
    sectionType: "final_order",
    department: "Industries Department",
    deadline: "2026-06-21",
    daysLeft: 51,
    priority: "high",
    confidence: 0.88,
    status: "pending_review",
    sourcePage: 40,
    sourceParagraph: "¶ 51",
    dependsOn: "d-9001",
    appealRoute: "compliance",
  },
  {
    id: "d-9004",
    text: "We are constrained to observe that the conduct of certain officials suggests systemic apathy, though we refrain from naming individuals at this stage.",
    sectionType: "observation",
    department: "—",
    deadline: "—" as unknown as string,
    daysLeft: 999,
    priority: "low",
    confidence: 0.91,
    status: "approved",
    sourcePage: 35,
    sourceParagraph: "¶ 41",
    appealRoute: "review",
  },
  {
    id: "d-9005",
    text: "Compliance shall be subject to the condition that no industrial unit shall be sealed without a 72-hour show-cause notice.",
    sectionType: "condition",
    department: "Pollution Control Board",
    deadline: "2026-05-22",
    daysLeft: 21,
    priority: "high",
    confidence: 0.82,
    status: "pending_review",
    sourcePage: 41,
    sourceParagraph: "¶ 53",
    dependsOn: "d-9001",
    appealRoute: "compliance",
  },
  {
    id: "d-9006",
    text: "The Registry shall communicate this order to the Chief Secretary, Government of Karnataka, within 48 hours.",
    sectionType: "final_order",
    department: "Registry",
    deadline: "2026-04-24",
    daysLeft: -7,
    priority: "critical",
    confidence: 0.99,
    status: "complied",
    sourcePage: 42,
    sourceParagraph: "¶ 55",
    appealRoute: "compliance",
  },
];

export const dnaTimeline = [
  { date: "2023-08-12", caseNo: "W.P.(C) 5512/2023", event: "Original PIL filed; notice issued to PCB", outcome: "ordered" },
  { date: "2024-02-04", caseNo: "I.A. 18/2024", event: "Interim order: status report every quarter", outcome: "complied" },
  { date: "2024-11-19", caseNo: "I.A. 44/2024", event: "Court flagged delay in 23 inspections", outcome: "partial" },
  { date: "2025-07-30", caseNo: "Cont.Cas. 9/2025", event: "Contempt notice; affidavit filed", outcome: "complied" },
  { date: "2026-04-22", caseNo: "W.P.(C) 8421/2026", event: "Fresh directions; scope expanded to 142 units", outcome: "active" },
];

export const layers = [
  {
    n: "01",
    name: "Ingestion",
    role: "PDF intake & type detection",
    detail: "Auto-classifies digital vs. scanned PDFs. pdfplumber for native text; Tesseract + pdf2image OCR pipeline for scanned. Page-level character density check.",
    metric: "Avg 4.2s / 50pg",
  },
  {
    n: "02",
    name: "Legal Intelligence",
    role: "Section-typed extraction",
    detail: "Classifies into Final Orders, Interim Orders, Observations, and Conditions. Not a flat entity dump — a structured legal taxonomy.",
    metric: "Differentiator",
    highlight: true,
  },
  {
    n: "03",
    name: "Action Engine",
    role: "Directive → task object",
    detail: "Department mapping, deadline calculation from order date, dependency graph, and parallel appeal-vs-compliance route analysis with limitation period.",
    metric: "What the brief asks",
    highlight: true,
  },
  {
    n: "04",
    name: "Verification",
    role: "Mandatory human review",
    detail: "Split-pane source highlighting, per-directive confidence scores, and a version-controlled audit trail. Nothing unverified moves forward.",
    metric: "Explainable",
  },
  {
    n: "05",
    name: "Orchestration",
    role: "Live compliance dashboard",
    detail: "Department views, deadline countdowns, escalation triggers, and Judgment DNA cross-case context.",
    metric: "Operational",
  },
];
