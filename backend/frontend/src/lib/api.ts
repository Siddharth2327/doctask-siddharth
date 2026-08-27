const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
  "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  code?: string;

  constructor(status: number, message: string, code?: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body && !(init.body instanceof FormData)
        ? { "Content-Type": "application/json" }
        : {}),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    let message = response.statusText;
    let code: string | undefined;

    try {
      const body = await response.json();
      message = body?.error?.message ?? body?.detail ?? message;
      code = body?.error?.code;
    } catch {
      // response had no JSON body — fall back to statusText
    }

    throw new ApiError(response.status, message, code);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

// ------------------------------------------------------------------
// Documents
// ------------------------------------------------------------------

export interface DocumentSummary {
  id: string;
  name: string;
  source: string;
  created_at: string;
}

export interface DocumentVersion {
  id: string;
  document_id: string;
  parent_version_id: string | null;
  version_number: number;
  filename: string;
  content_type: string;
  content_hash: string;
  source: string;
  storage_reference: string | null;
  created_at: string;
}

export interface DocumentUploadResult extends DocumentSummary {
  version: DocumentVersion;
}

export function listDocuments(): Promise<{ documents: DocumentSummary[] }> {
  return request("/documents");
}

export function uploadDocument(params: {
  file: File;
  name: string;
  source: string;
}): Promise<DocumentUploadResult> {
  const form = new FormData();
  form.append("file", params.file);
  form.append("name", params.name);
  form.append("source", params.source);

  return request("/documents", { method: "POST", body: form });
}

export interface VersionUploadResult {
  version: DocumentVersion;
  is_duplicate: boolean;
}

export function uploadNewVersion(params: {
  documentId: string;
  file: File;
  source: string;
}): Promise<VersionUploadResult> {
  const form = new FormData();
  form.append("file", params.file);
  form.append("source", params.source);

  return request(`/documents/${params.documentId}/versions`, {
    method: "POST",
    body: form,
  });
}

export function listVersions(
  documentId: string,
): Promise<{ versions: DocumentVersion[] }> {
  return request(`/documents/${documentId}/versions`);
}

export interface EvidenceRecord {
  id: string;
  run_id: string;
  document_id: string;
  document_version_id: string;
  field: string | null;
  location: string | null;
  chunk_id: string | null;
  quote: string | null;
  created_at: string;
}

export function listEvidenceForDocument(
  documentId: string,
): Promise<{ evidence: EvidenceRecord[] }> {
  return request(`/documents/${documentId}/evidence`);
}

// ------------------------------------------------------------------
// Runs
// ------------------------------------------------------------------

export interface RunStartResult {
  run_id: string;
  case_id: string;
  status: string;
  facts?: Record<string, unknown>[] | null;
  conflicts?: string[] | null;
  findings?: string[] | null;
  errors?: string[] | null;
}

export interface RunStatus {
  run_id: string;
  case_id: string;
  document_id: string;
  document_version_id: string;
  status: string;
  created_at: string;
  updated_at: string;
  input_tokens: number;
  output_tokens: number;
  estimated_cost: number;
}

export interface CommitResult {
  run_id: string;
  status: string;
  committed: string[];
  skipped_rejected: string[];
  already_committed: string[];
  still_pending: string[];
}

export function startRun(params: {
  documentId: string;
  documentVersionId: string;
  caseId: string;
}): Promise<RunStartResult> {
  return request("/runs", {
    method: "POST",
    body: JSON.stringify({
      document_id: params.documentId,
      document_version_id: params.documentVersionId,
      case_id: params.caseId,
    }),
  });
}

export function getRun(runId: string): Promise<RunStatus> {
  return request(`/runs/${runId}`);
}

export function finalizeRun(runId: string): Promise<CommitResult> {
  return request(`/runs/${runId}/finalize`, { method: "POST" });
}

// ------------------------------------------------------------------
// Findings / review
// ------------------------------------------------------------------

export type FindingStatus = "pending" | "approved" | "rejected" | "committed";
export type FindingType = "conflict" | "extraction" | "rule_violation";

export interface Finding {
  id: string;
  run_id: string;
  case_id: string;
  type: FindingType;
  field: string | null;
  proposed_value: string | null;
  severity: "low" | "medium" | "high";
  confidence: number | null;
  evidence_ids: string[];
  rationale: string;
  status: FindingStatus;
  reviewer: string | null;
  review_comment: string | null;
}

export function listFindings(params: {
  runId?: string;
  caseId?: string;
  status?: FindingStatus;
}): Promise<{ findings: Finding[] }> {
  const query = new URLSearchParams();
  if (params.runId) query.set("run_id", params.runId);
  if (params.caseId) query.set("case_id", params.caseId);
  if (params.status) query.set("status", params.status);

  return request(`/findings?${query.toString()}`);
}

export function decideFinding(params: {
  findingId: string;
  decision: "approved" | "rejected";
  reviewer: string;
  comment?: string;
  editedValue?: string;
}): Promise<Finding> {
  return request(`/findings/${params.findingId}/decide`, {
    method: "POST",
    body: JSON.stringify({
      decision: params.decision,
      reviewer: params.reviewer,
      comment: params.comment ?? null,
      edited_value: params.editedValue ?? null,
    }),
  });
}

// ------------------------------------------------------------------
// Case report (canonical register)
// ------------------------------------------------------------------

export interface CanonicalFact {
  field: string;
  value: string;
  evidence_id: string | null;
  updated_at: string;
}

export function getCaseReport(
  caseId: string,
): Promise<{ case_id: string; facts: CanonicalFact[] }> {
  return request(`/cases/${caseId}/report`);
}