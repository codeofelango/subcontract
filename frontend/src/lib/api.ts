import type {
  ActivityEntry,
  AttachmentOut,
  ApprovalStepOut,
  AppUser,
  AskActivityResponse,
  ChangeOrderDetailResponse,
  ContractListResponse,
  ContractSummary,
  ContractSummaryDoc,
  DashboardResponse,
  EvaluationResponse,
  IpcCertificate,
  IpcRow,
  ManpowerContractDraftResponse,
  ManpowerContractSummaryResponse,
  ManpowerPositionLineIn,
  ManpowerResponse,
  NewContractDraftResponse,
  OraclePrOption,
  PenaltyDetailResponse,
  TrackingResponse,
  VendorSubmission,
  WorkflowAppliesTo,
  WorkflowDetail,
  WorkflowEdge,
  WorkflowNode,
  WorkflowSummary,
} from "./types";

export interface NewContractRequest {
  vendorName: string;
  contractorNo: string;
  contractType: string;
  serviceType: string;
  projectName: string;
  projectNo: string;
  durationMonths: number;
  contractValue: number;
  contractBudget: number;
  retentionPct: number;
  advancePct: number;
  advanceAmount: number;
  payableTermsDays: number;
  sourcePr: string;
  lineItems: Array<{
    code: string;
    prLineRef: string;
    description: string;
    qty: number;
    uom: string;
    unitRate: number;
    budget: number;
    slaTags: string[];
  }>;
  draftToken: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8010";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${path} failed (${res.status}): ${body}`);
  }
  return res.json() as Promise<T>;
}

export function getDashboard(): Promise<DashboardResponse> {
  return apiFetch<DashboardResponse>("/dashboard");
}

export function listContracts(params: Record<string, string> = {}): Promise<ContractListResponse> {
  const query = new URLSearchParams(params).toString();
  return apiFetch<ContractListResponse>(`/contracts${query ? `?${query}` : ""}`);
}

export function listOraclePrs(): Promise<OraclePrOption[]> {
  return apiFetch<OraclePrOption[]>("/contracts/oracle-prs");
}

export function getNewContractDraft(prId: string): Promise<NewContractDraftResponse> {
  return apiFetch<NewContractDraftResponse>(`/contracts/new/draft?pr=${encodeURIComponent(prId)}`);
}

export function createContract(payload: NewContractRequest): Promise<ContractSummary> {
  return apiFetch<ContractSummary>("/contracts", { method: "POST", body: JSON.stringify(payload) });
}

export interface NewManpowerContractRequest {
  vendorName: string;
  contractorNo: string;
  serviceType: string;
  issueDate: string;
  expiryTerms: string;
  terminationNotice: string;
  emailAddress: string;
  paymentTermsNote: string;
  accountNumber: string;
  positionLines: ManpowerPositionLineIn[];
  draftToken: string;
}

export function getManpowerContractDraft(): Promise<ManpowerContractDraftResponse> {
  return apiFetch<ManpowerContractDraftResponse>("/contracts/new/manpower-draft");
}

export function createManpowerContract(payload: NewManpowerContractRequest): Promise<ContractSummary> {
  return apiFetch<ContractSummary>("/contracts/manpower", { method: "POST", body: JSON.stringify(payload) });
}

export function getManpowerContractSummary(id: string): Promise<ManpowerContractSummaryResponse> {
  return apiFetch<ManpowerContractSummaryResponse>(`/contracts/${id}/manpower-summary`);
}

export function approveContract(id: string): Promise<{ id: string; status: string; oracle_po: string; oracle_po_rev: string }> {
  return apiFetch(`/contracts/${id}/approve`, { method: "POST" });
}

export function getContractApprovalSteps(id: string): Promise<ApprovalStepOut[]> {
  return apiFetch<ApprovalStepOut[]>(`/contracts/${id}/approval-steps`);
}

export function getApprovalPreview(appliesTo: "contract_scope" | "contract_manpower"): Promise<ApprovalStepOut[]> {
  return apiFetch<ApprovalStepOut[]>(`/contracts/new/approval-preview?appliesTo=${appliesTo}`);
}

export function advanceContractStep(id: string): Promise<{ id: string; status: string }> {
  return apiFetch(`/contracts/${id}/advance-step`, { method: "POST" });
}

export function getContractTracking(id: string): Promise<TrackingResponse> {
  return apiFetch<TrackingResponse>(`/contracts/${id}/tracking`);
}

export function getContractSummary(id: string): Promise<ContractSummaryDoc> {
  return apiFetch<ContractSummaryDoc>(`/contracts/${id}/summary`);
}

export function getIpcCertificate(contractId: string, ipcId: number): Promise<IpcCertificate> {
  return apiFetch<IpcCertificate>(`/contracts/${contractId}/ipcs/${ipcId}/certificate`);
}

export function getVendorSubmissions(contractId: string): Promise<VendorSubmission[]> {
  return apiFetch<VendorSubmission[]>(`/contracts/${contractId}/vendor-submissions`);
}

export function certifyVendorSubmission(contractId: string, submissionId: number): Promise<IpcRow> {
  return apiFetch<IpcRow>(`/contracts/${contractId}/vendor-submissions/${submissionId}/certify`, { method: "POST" });
}

export function getManpower(contractId: string, period: string): Promise<ManpowerResponse> {
  return apiFetch<ManpowerResponse>(`/manpower/${contractId}?period=${encodeURIComponent(period)}`);
}

export function approveMatched(contractId: string, period: string): Promise<{ status: string; amountPaid: string }> {
  return apiFetch(`/manpower/${contractId}/approve-matched?period=${encodeURIComponent(period)}`, { method: "POST" });
}

export function raiseDispute(contractId: string, period: string): Promise<{ status: string }> {
  return apiFetch(`/manpower/${contractId}/dispute?period=${encodeURIComponent(period)}`, { method: "POST" });
}

export function getChangeOrders(contractId: string): Promise<ChangeOrderDetailResponse> {
  return apiFetch<ChangeOrderDetailResponse>(`/change-orders/${contractId}`);
}

export function advanceChangeOrderStep(coId: string): Promise<{ id: string; status: string }> {
  return apiFetch(`/change-orders/${coId}/advance-step`, { method: "POST" });
}

export function getPenalty(id: string): Promise<PenaltyDetailResponse> {
  return apiFetch<PenaltyDetailResponse>(`/penalties/${id}`);
}

export function advancePenaltyStep(id: string): Promise<{ id: string; status: string }> {
  return apiFetch(`/penalties/${id}/advance-step`, { method: "POST" });
}

export interface UserInput {
  name: string;
  email: string;
  department: string;
  title: string;
  active: boolean;
}

export function getUsers(): Promise<AppUser[]> {
  return apiFetch<AppUser[]>("/users");
}

export function createUser(payload: UserInput): Promise<AppUser> {
  return apiFetch<AppUser>("/users", { method: "POST", body: JSON.stringify(payload) });
}

export function updateUser(id: number, payload: UserInput): Promise<AppUser> {
  return apiFetch<AppUser>(`/users/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

export function deleteUser(id: number): Promise<void> {
  return apiFetch<void>(`/users/${id}`, { method: "DELETE" });
}

export function listWorkflows(appliesTo?: WorkflowAppliesTo): Promise<WorkflowSummary[]> {
  return apiFetch<WorkflowSummary[]>(`/workflows${appliesTo ? `?appliesTo=${appliesTo}` : ""}`);
}

export function getWorkflow(id: number): Promise<WorkflowDetail> {
  return apiFetch<WorkflowDetail>(`/workflows/${id}`);
}

export function createWorkflow(name: string, appliesTo: WorkflowAppliesTo): Promise<WorkflowDetail> {
  return apiFetch<WorkflowDetail>("/workflows", { method: "POST", body: JSON.stringify({ name, appliesTo }) });
}

export function saveWorkflow(id: number, name: string, nodes: WorkflowNode[], edges: WorkflowEdge[]): Promise<WorkflowDetail> {
  return apiFetch<WorkflowDetail>(`/workflows/${id}`, { method: "PUT", body: JSON.stringify({ name, nodes, edges }) });
}

export function activateWorkflow(id: number): Promise<WorkflowDetail> {
  return apiFetch<WorkflowDetail>(`/workflows/${id}/activate`, { method: "POST" });
}

export function getEvaluation(serviceLine: string): Promise<EvaluationResponse> {
  return apiFetch<EvaluationResponse>(`/evaluations?serviceLine=${serviceLine}`);
}

export function getActivity(limit = 30): Promise<ActivityEntry[]> {
  return apiFetch<ActivityEntry[]>(`/activity?limit=${limit}`);
}

export function askActivity(question: string): Promise<AskActivityResponse> {
  return apiFetch<AskActivityResponse>("/activity/ask", { method: "POST", body: JSON.stringify({ question }) });
}

// Attachments: uploaded before the owning record exists, grouped by a client-generated
// draftToken, then claimed by the backend once the contract is actually created.
export async function uploadAttachment(draftToken: string, file: File): Promise<AttachmentOut> {
  const form = new FormData();
  form.append("draftToken", draftToken);
  form.append("file", file);
  const res = await fetch(`${API_URL}/attachments`, { method: "POST", body: form });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Upload failed (${res.status}): ${body}`);
  }
  return res.json() as Promise<AttachmentOut>;
}

export function listDraftAttachments(draftToken: string): Promise<AttachmentOut[]> {
  return apiFetch<AttachmentOut[]>(`/attachments?draftToken=${encodeURIComponent(draftToken)}`);
}

export function deleteAttachment(id: number): Promise<void> {
  return apiFetch<void>(`/attachments/${id}`, { method: "DELETE" });
}

export function getContractAttachments(contractId: string): Promise<AttachmentOut[]> {
  return apiFetch<AttachmentOut[]>(`/contracts/${contractId}/attachments`);
}

export function attachmentDownloadUrl(id: number): string {
  return `${API_URL}/attachments/${id}/download`;
}
