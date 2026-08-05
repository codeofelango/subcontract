export interface KpiItem {
  label: string;
  value: string;
  delta: string;
  deltaColor: string;
}

export interface AlertItem {
  title: string;
  detail: string;
  tag: string;
  color: string;
  bg: string;
}

export interface ServiceMixItem {
  label: string;
  amount: string;
  pct: string;
  width: string;
  color: string;
}

export interface PendingActionItem {
  ref: string;
  item: string;
  vendor: string;
  stage: string;
  amount: string;
  age: string;
  color: string;
  bg: string;
}

export interface VendorSummaryItem {
  vendor: string;
  contractorNo: string;
  contractsCount: number;
  activeCount: number;
  totalValue: string;
  avgProgress: string;
  progressColor: string;
  rating: string;
  ratingColor: string;
  ratingBg: string;
}

export interface DashboardResponse {
  kpis: KpiItem[];
  alerts: AlertItem[];
  serviceMix: ServiceMixItem[];
  pendingActions: PendingActionItem[];
  vendors: VendorSummaryItem[];
}

export interface ContractSummary {
  id: string;
  vendor: string;
  type: string;
  contractCategory: "scope" | "manpower";
  project: string;
  valueFmt: string;
  progress: string;
  progressW: string;
  progressColor: string;
  expiry: string;
  status: string;
  typeColor: string;
  typeBg: string;
  statusColor: string;
  statusBg: string;
}

export interface ContractListResponse {
  items: ContractSummary[];
  count: number;
}

export interface DraftLineItem {
  id: number;
  code: string;
  prLineRef: string;
  description: string;
  qty: number;
  uom: string;
  unitRate: number;
  budget: number;
  slaTags: string[];
}

export interface PaymentTermOption {
  value: number;
  label: string;
}

export interface ContractorOption {
  contractorNo: string;
  vendorName: string;
}

export interface ProjectOption {
  projectNo: string;
  projectName: string;
}

export interface NewContractDraftResponse {
  sourcePr: string;
  vendorName: string;
  contractorNo: string;
  contractType: string;
  serviceType: string;
  projectName: string;
  projectNo: string;
  contractNumberHint: string;
  durationMonths: number;
  contractValue: number;
  contractBudget: number;
  retentionPct: number;
  advancePct: number;
  payableTermsDays: number;
  lineItems: DraftLineItem[];
  prLineCatalog: DraftLineItem[];
  retentionOptions: PaymentTermOption[];
  advanceOptions: PaymentTermOption[];
  payableTermsOptions: PaymentTermOption[];
  contractorOptions: ContractorOption[];
  projectOptions: ProjectOption[];
  serviceTypeOptions: string[];
}

export interface OraclePrOption {
  id: string;
  vendorName: string;
  projectName: string;
  serviceType: string;
  contractValueFmt: string;
}

export interface ManpowerPositionLineIn {
  categoryPosition: string;
  totalStaff: number;
  workingHours: number;
  basicSalary: number;
  hAllowance: number;
  tAllowance: number;
  fAllowance: number;
  share: number;
  leaveTreatment: string;
  absenceTreatment: string;
}

export interface ManpowerContractDraftResponse {
  contractNumberHint: string;
  serviceTypeOptions: string[];
  contractorOptions: ContractorOption[];
}

export interface ManpowerPositionLineOut {
  categoryPosition: string;
  totalStaff: number;
  workingHours: string;
  basicSalary: string;
  hAllowance: string;
  tAllowance: string;
  fAllowance: string;
  share: string;
  totalCost: string;
  leaveTreatment: string;
  absenceTreatment: string;
}

export interface ManpowerContractSummaryResponse {
  id: string;
  vendorName: string;
  contractorNo: string;
  serviceType: string;
  status: string;
  issueDate: string;
  expiryTerms: string;
  terminationNotice: string;
  emailAddress: string;
  paymentTermsNote: string;
  accountNumber: string;
  contractValue: string;
  contractBudget: string;
  positionLines: ManpowerPositionLineOut[];
}

export interface FinanceCard {
  label: string;
  value: string;
  note: string;
  color: string;
}

export interface TrackerRow {
  k: string;
  v: string;
  w: number;
  c: string;
}

export interface TrackerCard {
  title: string;
  sub: string;
  barW: string;
  barColor: string;
  rows: TrackerRow[];
}

export interface IpcRow {
  id: number;
  n: string;
  period: string;
  done: string;
  gross: string;
  ret: string;
  adv: string;
  net: string;
  status: string;
  color: string;
  bg: string;
}

export interface TrackingHeader {
  id: string;
  vendor: string;
  type: string;
  project: string;
  status: string;
  progress: string;
  progressColor: string;
  remainMonths: string;
  expiry: string;
  po: string | null;
  poRev: string | null;
  pr: string;
}

export interface TrackingResponse {
  header: TrackingHeader;
  finance: FinanceCard[];
  trackers: TrackerCard[];
  ipcs: IpcRow[];
}

export interface VendorSubmission {
  id: number;
  period: string;
  workDonePct: string;
  grossClaimed: string;
  submittedBy: string;
  submittedAt: string;
  status: string;
}

export interface SummaryLineItem {
  code: string;
  prLineRef: string;
  description: string;
  qty: string;
  uom: string;
  unitRate: string;
  budget: string;
  total: string;
  slaTags: string[];
  previousQty: string | null;
  revisedByCo: string | null;
}

export interface ContractSummaryDoc {
  id: string;
  vendor: string;
  contractorNo: string;
  serviceType: string;
  project: string;
  projectNo: string;
  durationMonths: number;
  contractValue: string;
  contractBudget: string;
  retentionPct: string;
  advancePct: string;
  payableTermsDays: string;
  sourcePr: string;
  oraclePo: string | null;
  oraclePoRev: string | null;
  status: string;
  createdAt: string;
  lineItems: SummaryLineItem[];
}

export interface ManpowerContext {
  contractId: string;
  vendor: string;
  period: string;
  source: string;
  netVariance: string;
  netVarianceColor: string;
}

export interface ManpowerRow {
  title: string;
  reg: string;
  regRate: string;
  ot: string;
  otRate: string;
  contract: string;
  invoiced: string;
  variance: string;
  varColor: string;
  status: string;
  color: string;
  bg: string;
}

export interface ManpowerResponse {
  context: ManpowerContext;
  rows: ManpowerRow[];
  total: { contract: string; invoiced: string; variance: string };
  varianceNote: string | null;
  matchedTotal: string;
}

export interface CoContext {
  id: string;
  title: string;
  contractId: string;
  vendor: string;
  po: string;
  status: string;
}

export interface CoLineRow {
  code: string;
  desc: string;
  orig: string;
  rev: string;
  delta: string;
  deltaColor: string;
  rate: string;
  impact: string;
  impactColor: string;
}

export interface CoHistoryRow {
  id: string;
  reason: string;
  impact: string;
  impactColor: string;
  po: string;
  status: string;
  color: string;
  bg: string;
}

export interface CoValueRow {
  k: string;
  v: string;
  w: number;
  c: string;
}

export interface ApprovalStepOut {
  seq: number;
  role: string;
  name: string;
  meta: string;
  state: "done" | "current" | "pending";
}

export interface ChangeOrderDetailResponse {
  context: CoContext;
  affectedLineItems: CoLineRow[];
  history: CoHistoryRow[];
  valueRows: CoValueRow[];
  approvalSteps: ApprovalStepOut[];
}

export interface PenaltyField {
  label: string;
  value: string;
  weight: number;
  color: string;
}

export interface SlaBreach {
  actualPct: string;
  label: string;
  detail: string;
}

export interface PenaltyDetailResponse {
  id: string;
  title: string;
  status: string;
  fields: PenaltyField[];
  attachment: string;
  slaBreach: SlaBreach;
  approvalSteps: ApprovalStepOut[];
}

export interface EvalMetaItem {
  k: string;
  v: string;
}

export interface EvalKpiRow {
  cat: string;
  catWeight: number;
  kpi: string;
  target: string;
  weight: string;
  actual: string;
  score: string;
  scoreColor: string;
  weighted: string;
}

export interface EvalCatBar {
  label: string;
  val: string;
  width: string;
  color: string;
}

export interface EvalAdjRow {
  k: string;
  v: string;
  w: number;
  c: string;
}

export interface EvalRatingGuideRow {
  range: string;
  label: string;
  color: string;
}

export interface EvalRating {
  label: string;
  color: string;
  bg: string;
}

export interface EvalTab {
  id: string;
  label: string;
}

export interface EvaluationResponse {
  tabs: EvalTab[];
  activeTab: string;
  meta: EvalMetaItem[];
  rows: EvalKpiRow[];
  total: string;
  rating: EvalRating;
  cats: EvalCatBar[];
  adj: EvalAdjRow[];
  ratingGuide: EvalRatingGuideRow[];
}

export interface ActivityEntry {
  id: number;
  contractId: string | null;
  entityType: string;
  entityId: string;
  action: string;
  summary: string;
  actor: string;
  createdAt: string;
}

export interface AskActivityResponse {
  answer: string;
  matches: ActivityEntry[];
}

export interface IpcCertificate {
  contractId: string;
  vendor: string;
  contractorNo: string;
  project: string;
  projectNo: string;
  oraclePo: string | null;
  oraclePoRev: string | null;
  ipcNumber: string;
  period: string;
  workDonePct: string;
  gross: string;
  retentionPct: string;
  retention: string;
  advanceRecovered: string;
  netPayable: string;
  payableTermsDays: string;
  status: string;
  createdAt: string;
}

export interface AppUser {
  id: number;
  name: string;
  email: string;
  department: string;
  title: string;
  active: boolean;
}

export type WorkflowAppliesTo = "contract_scope" | "contract_manpower" | "change_order" | "penalty";

export interface WorkflowSummary {
  id: number;
  name: string;
  appliesTo: WorkflowAppliesTo;
  isActive: boolean;
  stepCount: number;
  createdAt: string;
}

export interface WorkflowNodeData {
  label: string;
  userId: number | null;
}

export interface WorkflowNode {
  id: string;
  type: "step";
  position: { x: number; y: number };
  data: WorkflowNodeData;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
}

export interface WorkflowDetail {
  id: number;
  name: string;
  appliesTo: WorkflowAppliesTo;
  isActive: boolean;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface AttachmentOut {
  id: number;
  filename: string;
  contentType: string;
  sizeBytes: number;
  uploadedAt: string;
}
