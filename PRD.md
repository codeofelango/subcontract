# PRD — Subcontract Management Module

## 1. Purpose & Background

Contracting/PMO teams currently manage subcontracted vendor work (MEP/Hard FM, Soft Services, Construction, Manpower Supply) with fragmented spreadsheets alongside Oracle ERP (PR/PO) and Oracle HCM (attendance). This causes:
- No single view of contract commitments, retention/advance exposure, or expiring contracts.
- Manual, error-prone manpower invoice checking against timesheets.
- Inconsistent penalty application and no audit trail of the approval chain.
- No standardized, weighted vendor performance scoring.

This module gives contract administrators, PMs, QS/cost teams, procurement, and finance a single system of record for the subcontract lifecycle, tightly coupled to Oracle PR/PO as the source of truth for commercial commitment.

## 2. Goals

1. Give a portfolio-level view (value, spend, retention, advance, expiring contracts, alerts) in one dashboard.
2. Create subcontracts only from an approved Oracle PR, carrying PR line references into the BOQ, and auto-reflect the Oracle PO once approved.
3. Track progress payments (IPCs) with correct retention withholding and pro-rata advance recovery.
4. Reconcile monthly manpower invoices against HCM timesheets × contract rates (incl. OT) automatically, surfacing only exceptions for human review.
5. Support quantity-only change orders that revise the Oracle PO, with unit rates locked to contract baseline.
6. Enforce a mandatory, sequential penalty approval chain, debiting the vendor only after CFO sign-off.
7. Produce standardized, weighted subcontractor scorecards per service line.

## 3. Non-Goals (this phase)

- Real Oracle PR/PO/HCM API integrations — this phase models these as internal data entities seeded with realistic values; live integration is a follow-on phase.
- Multi-tenant / multi-company support.
- Mobile app (responsive web only, desktop + tablet).
- Authentication/authorization system (single implicit user "RM" as in the design, no login flow) — assume it sits behind existing SSO in production.
- Document storage backend (attachment upload is represented, not persisted to blob storage).

## 4. Users / Personas

| Persona | Needs |
| --- | --- |
| Contracts Administrator | Create contracts from PRs, maintain BOQ, submit for approval |
| Project Manager | Raise change orders, raise penalties, review reconciliation variances |
| QS / Cost Verification | Verify CO rates against contract baseline |
| Procurement Director | Approve contracts, CO PO revisions |
| Finance / AP | Certify IPCs, debit penalties, track payable status |
| COO / CFO | Approve penalties above their threshold in the chain |
| FM Ops / PMO / QAQC (Evaluators) | Score subcontractor performance per period |

## 5. Scope — Screens & Functional Requirements

### 5.1 Portfolio Dashboard
- 6 KPI cards: Active Contracts, Portfolio Value, Executed Spend, Retention Held, Advance Outstanding, Expiring ≤30 days.
- Auto-generated Alerts & Attention feed (expiring, SLA breach, progress slippage, pending payment, performance trend).
- Committed Value by Service Type (4 categories, % of portfolio).
- Pending My Action table (cross-entity: contract approvals, penalty approvals, IPC certifications, manpower invoice reviews) with waiting-age.

**Acceptance:** all 6 KPIs, alerts, service mix, and pending-action rows are computed from live contract/IPC/penalty/manpower data, not hardcoded — except alert *generation thresholds*, which are simple rules (e.g. expiry ≤30 days, SLA <90% for 2 consecutive periods).

### 5.2 Contracts List
- Filterable register (Project, Service Type, Vendor, Status, Expiry).
- Columns: Contract #, Vendor, Type, Project, Value, Progress bar, Expiry, Status.
- Row click → Contract Tracking.

**Acceptance:** filters combine with AND semantics; progress bar color follows ≥80% green / ≥40% accent / else amber.

### 5.3 New Contract — two fully separate flows

The New Contract entry point (`/contracts/new`) is a chooser between two flows that share no fields, no validation rules, and no downstream screen — per CLAUDE.md's domain rules, Scope/Works and Manpower Supply "total different flow, do not mix with each other."

**5.3a Scope / Works Contract** (`/contracts/new/work`)
- Step 1: pick an approved Oracle PR from a live list (`GET /contracts/oracle-prs`) — this is the trigger; nothing renders until a PR is chosen.
- Step 2 (`/contracts/new/work?pr=<id>`): PR banner (read-only, simulated), BOQ line items table with PR-line reference per row (add-item affordance, PR-line picker autofills code/description/qty/uom/rate/budget/SLA tags), Payment Terms & Securities (Retention %, Advance %, Advance Amount, Payable Terms — options from Oracle's maintained list), Contract Header (Contractor Name/No. from Oracle master, **Contract Type from a maintained service-type list** (`ServiceTypeOption`, user-selectable — not just inherited from the PR), Project Name/No. from the PR, Contract Value/Budget summed live from the BOQ), sticky summary rail, Submit for Approval.
- Downstream: IPC tracking, retention/advance recovery, change orders all apply.

**5.3b Manpower Supply** (`/contracts/new/manpower`)
- No Oracle PR step — created directly (`GET /contracts/new/manpower-draft` has no PR/line data, only contractor options + the maintained service-type list).
- Contract Header: Contractor Name/No., Contract Type, Contract Issue Date, Expiry/Renewal Terms, Termination Notice Period, Email Address, Payment Terms, Account Number (IBAN).
- Position Rate Card (replaces the BOQ): one row per job Category/Position — Total Staff, Working Hours, Basic Salary, H/T/F Allowance, Share, computed Total Cost (`basic + H + T + F + share`), Leave Treatment, Absence Treatment.
- Contract Value/Budget = `Σ (Total Cost × Total Staff)` across position rows — no separate Oracle budget feed for this flow, so budget = value.
- No retention/advance/payable-terms fields (don't apply to Manpower Supply per CLAUDE.md).
- Downstream: the read-only Manpower Contract view (`/contracts/{id}/manpower`) instead of the IPC tracker; monthly reconciliation (§5.5) applies instead of IPCs.

**Acceptance:** on submit, contract + (line items | position lines + contractor detail) persist under the matching `contract_type`; Oracle PO fields remain "Auto-created on approval" and are only ever populated for Scope/Works — Manpower Supply contracts never get a PO/PO-rev, since they aren't PR/PO-triggered.

### 5.4 Contract Tracking
- Header: id, status, vendor, type/project, Oracle PO + rev chip, Source PR chip, overall progress/remaining duration/expiry.
- 4 finance cards: Contract Value, Executed to Date, Remaining, Penalties Applied.
- 3 tracker cards: Retention (held/released/remaining), Advance Recovery (paid/recovered/outstanding), Payable Status (certified/paid/remaining).
- IPC table: per-certificate work-done%, gross, retention, advance recovered, net payable, status.

**Acceptance:** `Net Payable = Gross − Retention − Advance Recovered` for every IPC row; tracker totals equal the sum/latest state of the IPC ledger.

### 5.5 Manpower Reconciliation
- Context bar: contract, period, source ("HCM Attendance · post salary-close"), net variance.
- Per-job-title table: Reg Hrs/Rate, OT Hrs/Rate, computed Contract Amount, Invoiced, Variance, Status (Matched/Review).
- Variance callout banner explaining the largest exception.
- Actions: Raise Dispute, Approve Matched (pays only non-flagged lines).

**Acceptance:** `Contract Amount = reg_hrs×reg_rate + ot_hrs×ot_rate`; `Variance = Invoiced − Contract Amount`; status = Review when `|variance| ≥ SAR 100` else Matched; "Approve Matched" total = sum of Contract Amount for Matched rows only.

### 5.6 Change Orders
- CO header (id, status, title, contract/vendor/PO context), "+ New Change Order".
- Affected Line Items: original/revised qty, Δ qty, contract rate (locked), value impact.
- Change Order History table for the contract.
- Rail: Revised Contract Value (original, net impact, revised, retention/advance recomputed), Approval & PO Revision timeline ending in a PO revision.

**Acceptance:** rates cannot be edited on a CO, only quantities; `Value Impact = Δ Qty × Contract Rate`; approving a CO increments `oracle_po_rev` and recomputes retention off the revised value (advance stays unchanged, per design).

### 5.7 Apply Penalty
- Penalty detail: contract, project, reason, basis, amount, raised-by/on, mandatory attachment.
- Linked SLA Breach panel (actual vs target, consecutive breach count).
- Approval Route timeline: PM raise → PM Acknowledge → COO → Procurement Director → CFO → Debit Supplier Account.

**Acceptance:** a penalty cannot be submitted without an attachment reference; each approval step must be actioned in order (no skipping); only after the CFO step completes does the "Debit Supplier Account" step activate.

### 5.8 Evaluations
- Tabs per service line (Construction/JR, Soft Services, Hard FM/MEP), each its own KPI dataset/weights.
- Meta card (subcontractor/project/period/evaluator).
- KPI table grouped by category with SLA target, weight, actual, score%, weighted score; total row.
- Rating rail: big overall score, rating pill, per-category weighted bars, Penalty/Incentive adjustment, rating-band legend.

**Acceptance:** weights within a service line sum to 100; scoring rule matches §Domain Model in CLAUDE.md exactly; rating band thresholds are ≥90/≥80/≥70/≥60/<60.

### 5.9 User Management
- Directory of people (`AppUser`: name, email, department, title, active) assignable as named approvers when building an Approval Flow. No login/passwords — a lightweight directory, not an auth system.
- Inline add/edit/delete in a single table; no separate create screen.

**Acceptance:** a user can be added, edited, and deleted without a page reload; deleting a user referenced by a `WorkflowStepTemplate` step nulls out that step's assignment (falls back to "raiser" at runtime) rather than being blocked.

### 5.10 Approval Flows (dynamic approval-flow builder)
- One section per entity type — Scope/Works Contract, Manpower Supply Contract, Change Order, Penalty — each listing its drafted flows with an Active/Draft pill; "+ New Flow" creates a draft with a single "Raised" starting step.
- Canvas editor (`@xyflow/react`, n8n-styled: pan/zoom/minimap/background grid): click the **+** button on any step to insert the next step in the chain (auto-connected, auto-laid-out left→right); click a step to edit its Role label and assigned User in a side inspector; delete a step and its neighbors reconnect automatically.
- **Linear chains only** — no branching/conditions. Matches the "each approval step must be actioned in order" rule (§Domain Model) and keeps the builder a straight sequence, not a graph to reason about.
- Save persists the draft; **Activate** is a separate, explicit action — only one flow per entity type is active at a time, and editing/saving never silently changes what's live.

**Acceptance:** a saved flow is rejected with a clear error unless it forms a single connected chain from one start node to one end node (no branches, no cycles, no orphans); activating a flow deactivates any previously-active flow for the same entity type; a newly created Contract/Change Order/Penalty seeds its real approval steps from whichever flow is active for its type, falling back to the original built-in default chain when none has been activated yet.

## 6. Cross-cutting Requirements
- All money shown as `SAR <formatted number>`; stored as Decimal, never float, to avoid rounding drift across IPCs/reconciliation/CO impact math.
- Every list/detail screen must handle empty/loading/error states.
- Sidebar/header shell persists across all screens (SPA-like navigation via Next.js routing).

## 7. Success Metrics (qualitative, MVP)
- All 8 screens are pixel-consistent with the design reference for layout, type, and color.
- All computed values (IPC net payable, manpower variance, CO impact, evaluation scores) are derived server-side from stored data, not client-hardcoded.
- A user can: create a contract → see it in tracking → record an IPC → see retention/advance move → raise and approve a CO → see PO rev bump → raise and progress a penalty through the chain → score an evaluation tab — all backed by Postgres.

## 8. Roadmap — Phases 2-8

Phase 1 split Scope/Works and Manpower Supply contract creation into two fully separate flows (§5.3). Phase 3 (the dynamic approval-flow engine, §5.9-5.10) is now built. Remaining phases are scoped, with key design decisions already locked in, so a future pass can implement directly rather than re-litigate approach.

**Phase 2 — Lightweight access control (partially done).** The `AppUser` directory (§5.9) now exists, giving named people to assign as approvers — but there is still no "sign in as" session/current-user concept, no request header carrying identity, and no department-scoped filtering of which contracts a department can see (procurement → Scope/Works only, HR → Manpower Supply only). That remains the open part of this phase: a client-side "sign in as" picker sending a header the backend uses to scope contract list/detail queries. Auth itself (passwords/SSO) is still explicitly out of scope (§3 Non-Goal).

**Phase 3 — Dynamic, reusable approval-flow engine. ✅ Done.** `WorkflowTemplate`/`WorkflowStepTemplate` (backend/app/models/tables.py) plus a shared `seed_approval_steps()` helper (backend/app/workflow_engine.py) replaced the hardcoded `PENALTY_STEP_TEMPLATE`/`CO_STEP_TEMPLATE` constants as the *primary* source (those constants remain only as the fallback used when no flow has been activated for a type — nothing broke). `owner_type='contract'` now exists too — both Scope/Works and Manpower Supply contract creation seed real approval steps when a flow is active, with a new `POST /contracts/{id}/advance-step` alongside the original one-shot `/approve` (used only when no chain is configured). Built as a **linear-chain-only** engine (no branching) per an explicit scope decision — see §5.10. The `_steps_for`/`advance_step` duplication between `penalties.py`/`change_orders.py` was *not* consolidated (out of scope for this pass — each still has its own near-identical advance-step handler); a future cleanup pass could extract that.

**Phase 4 — Real attachments + notifications.** Multipart file upload, stored on local disk (no S3/blob), tracked in a DB row (filename/path/content-type) — replaces today's `attachment_ref` plain-string field (Penalty only) and the New Contract screen's non-functional "3 documents attached" label. Mandatory-attachment validation (already enforced for Penalties) extends to Contract and Change Order submission. On each approval-step transition, a notification is generated with the attachment referenced — written to a log/outbox table rather than sent via real SMTP (the Office365 credentials already reserved in `backend/.env` stay unused until this is explicitly turned on).

**Phase 5 — Oracle GRN/certificate + vendor invoice ingestion (Scope/Works).** Model GRN/certificate and vendor-invoice-from-portal as simulated feed tables (same pattern as `OraclePr`/`VendorPortalSubmission` today), tying an approved GRN to IPC eligibility and a vendor invoice to IPC certification, mirroring how `VendorPortalSubmission` already stands in for the Oracle vendor portal.

**Phase 6 — Change-order-style revisioning for both contract types.** Today only Scope/Works has Change Orders (quantity-only, rate locked). Extend the same revisioning concept — new line items, a revision number, its own approval cycle via the Phase 3 engine, and a GRN/certificate-percentage impact — to Manpower Supply contracts (e.g. revising the position rate card), and formalize revision numbering on both.

**Phase 7 — Monthly manpower reconciliation upgrade.** Today's `/manpower` screen reconciles exactly one hardcoded contract/period at a time with no persisted match/dispute state. Add a period selector, persist match/dispute outcomes per timesheet line (new status column, not just an activity-log entry), and a "push to Finance" record capturing the discrepancy detail for a distinct Finance-facing queue.

**Phase 8 — Document export + Oracle DFF push.** A real downloadable file (not the current print-styled HTML pages) generated from contract data, with fields mapped into Oracle Descriptive Flexfield (DFF) slots — today there is no PDF/XLSX generation library or DFF concept in the codebase at all; this is greenfield.
