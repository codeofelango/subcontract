# Architecture — Subcontract Management Module

## 1. System Overview

```
┌─────────────────────┐        HTTPS/JSON        ┌──────────────────────┐
│  Next.js Frontend    │ ───────────────────────▶ │   FastAPI Backend     │
│  (App Router, TS,    │ ◀─────────────────────── │   (async, Pydantic)   │
│  Tailwind)            │                          │                       │
└─────────────────────┘                          └──────────┬────────────┘
                                                              │ SQLAlchemy async
                                                              │ (asyncpg driver)
                                                              ▼
                                                   ┌──────────────────────┐
                                                   │ PostgreSQL (Neon)     │
                                                   └──────────────────────┘
```

- No auth layer in this phase (single implicit user, matches the design's "RM" avatar). Add SSO/JWT at the FastAPI dependency layer later without touching business logic.
- No background workers needed yet — all computations (IPC net payable, manpower variance, CO impact, evaluation scoring) are cheap synchronous queries, done inline in the request handler. Celery/Redis stay available for later (e.g., nightly HCM ingestion job) but are not wired up now — don't add unused infrastructure.

## 2. Backend

### 2.1 Layout
See `CLAUDE.md` → Project Structure. Routers are one per screen-group; each router owns its Pydantic schemas file.

### 2.2 Data Model (SQLAlchemy, Postgres)

```
contracts
  id (str, PK, e.g. "SC-2024-0142")
  vendor_name, contractor_no
  contract_type            -- 'scope' | 'manpower'
  project_name, project_no             -- nullable: manpower contracts have no project
  duration_months
  contract_value, contract_budget      -- numeric(14,2) -- manpower: budget = value (no separate Oracle budget feed)
  retention_pct, advance_pct           -- numeric(5,2)  -- always 0 for manpower (doesn't apply)
  advance_amount                       -- numeric(14,2)
  payable_terms_days
  source_pr                            -- nullable: e.g. "PR-0123 / PR-0124" — null for manpower (no PR trigger)
  oracle_po, oracle_po_rev             -- null for manpower (no PO — not PR/PO-triggered)
  status                    -- 'Draft'|'Pending'|'Active'|'Expiring'|'Closing'
  progress_pct
  expiry_date
  created_at

contract_line_items          -- Scope/Works BOQ only
  id (PK), contract_id (FK)
  code, pr_line_ref, description
  qty, uom, unit_rate, budget, total
  previous_qty, revised_by_co          -- set when a Change Order revises this line's qty

oracle_prs / oracle_pr_lines           -- simulated Oracle PR feed (Scope/Works creation trigger)
payment_term_options                   -- retention_pct | advance_pct | payable_terms_days choices
oracle_contractors / oracle_projects   -- Oracle vendor/project master lists

service_type_options                   -- maintained Contract Type list, selectable on the header
  id (PK), label, contract_category ('scope'|'manpower'|'both'), sort_order

manpower_contract_details              -- 1:1 with contracts, contract_type='manpower' only
  contract_id (PK, FK)
  issue_date, expiry_terms, termination_notice
  email_address, payment_terms_note, account_number

manpower_position_lines                -- Manpower Supply rate card (replaces BOQ for this type)
  id (PK), contract_id (FK)
  category_position, total_staff, working_hours
  basic_salary, h_allowance, t_allowance, f_allowance, share
  total_cost                           -- server-computed: basic + H + T + F + share, per staff
  leave_treatment, absence_treatment

ipcs                                   -- Scope/Works only
  id (PK), contract_id (FK)
  number, period, work_done_pct
  gross, retention, advance_recovered, net_payable   -- numeric
  status              -- 'Certifying' | 'Paid'

timesheet_lines            -- simulated monthly HCM feed
  id (PK), contract_id (FK), period, job_title
  reg_hours, reg_rate, ot_hours, ot_rate

vendor_invoice_lines        -- simulated vendor invoice
  id (PK), contract_id (FK), period, job_title
  invoiced_amount

change_orders
  id (PK), contract_id (FK)
  reason, status ('Draft'|'In Approval'|'Approved'), po_revision_label
  created_at

change_order_lines
  id (PK), change_order_id (FK)
  code, description, original_qty, revised_qty, contract_rate

penalties
  id (PK), contract_id (FK)
  reason, basis, amount, status ('In Approval'|'Approved'|'Debited')
  attachment_ref, raised_by, raised_on
  sla_actual_pct, sla_target_pct, sla_breach_months

approval_steps                -- generic, used by penalties, change_orders, AND contracts
  id (PK), owner_type ('penalty'|'change_order'|'contract'), owner_id
  seq, role, approver_name, state ('done'|'current'|'pending'), acted_at, meta_note

app_users                      -- lightweight directory, no login/passwords
  id (PK), name, email, department, title, active

workflow_templates             -- one configured approval flow per applies_to; only one is_active=true at a time
  id (PK), name, applies_to ('contract_scope'|'contract_manpower'|'change_order'|'penalty'), is_active
  canvas_nodes (JSON), canvas_edges (JSON)   -- raw @xyflow/react graph, round-tripped by the editor
  created_at

workflow_step_templates        -- derived, ordered chain computed server-side from canvas_nodes/canvas_edges on save
  id (PK), template_id (FK), seq, role, user_id (FK app_users, nullable)

evaluations
  id (PK)
  service_line ('jr'|'soft'|'hard'), subcontractor, project, period, evaluator

evaluation_kpi_rows
  id (PK), evaluation_id (FK)
  category, kpi, target_label, target_value, direction ('higher'|'lower'|'zero')
  weight, actual
```

Derived (computed at query time, not stored): IPC net payable check, manpower variance/status, CO value impact, evaluation score/weighted/rating, dashboard KPIs/alerts/service-mix/pending-actions.

### 2.3 API Contract

All responses are JSON; all list endpoints return `{ items: [...], count }` where relevant. Errors use FastAPI's standard `HTTPException` → `{ detail }`.

```
GET  /health

GET  /dashboard
     → { kpis: [{label, value, delta, deltaColor}],
         alerts: [{title, detail, tag, color, bg}],
         serviceMix: [{label, amount, pct, color}],
         pendingActions: [{ref, item, vendor, stage, amount, age, color, bg}] }

GET  /contracts?project=&serviceType=&vendor=&status=&expiry=
     → { items: [ContractSummary (incl. contractCategory: 'scope'|'manpower')], count }

GET  /contracts/oracle-prs
     → [{ id, vendorName, projectName, serviceType, contractValueFmt }]   -- Scope/Works PR picker

GET  /contracts/new/draft?pr=<id>
     → NewContractDraftResponse (PR header + BOQ + payment-term options + serviceTypeOptions)

POST /contracts                -- Scope/Works only
     body: NewContractRequest (header + terms + lineItems[] + slaTags[] + sourcePr)
     → ContractSummary (status='Pending', oracle_po=null)

GET  /contracts/new/manpower-draft
     → { contractNumberHint, serviceTypeOptions, contractorOptions }   -- no PR/line data

POST /contracts/manpower       -- Manpower Supply only, no sourcePr/lineItems
     body: NewManpowerContractRequest (header fields + positionLines[])
     → ContractSummary (status='Pending', contract_value/budget = Σ(totalCost × totalStaff))

POST /contracts/{id}/approve            -- only when no approval chain is configured for this contract
     → ContractSummary (status='Active'; oracle_po/oracle_po_rev assigned only if contract_type='scope')

GET  /contracts/{id}/approval-steps     -- [] unless a Contract flow (see /workflows) has been activated
     → [ApprovalStepOut]

POST /contracts/{id}/advance-step       -- only when an approval chain exists; 400 otherwise (use /approve)
     → ContractSummary-shaped { id, status, oracle_po, oracle_po_rev }

GET  /contracts/{id}/tracking          -- Scope/Works only (400 if contract_type='manpower')
     → { header: {...}, finance: [...], trackers: [{title,sub,barW,barColor,rows}], ipcs: [...] }

GET  /contracts/{id}/manpower-summary  -- Manpower Supply only (400 if contract_type='scope')
     → { header fields, contractValue, contractBudget, positionLines: [...] }

POST /contracts/{id}/ipcs      -- record a new IPC for the contract (Scope/Works only)
     body: { period, workDonePct, gross }
     → IPC   (server computes retention = gross*retention_pct, advance_recovered pro-rata, net_payable)

GET  /manpower/{contractId}?period=
     → { context: {...}, rows: [...], total: {...}, varianceNote }

POST /manpower/{contractId}/approve-matched?period=
POST /manpower/{contractId}/dispute?period=

GET  /change-orders/{contractId}
     → { context, affectedLineItems: [], history: [], valueRows: [], approvalSteps: [] }

POST /change-orders
     body: { contractId, reason, lines: [{code, description, revisedQty, contractRate, originalQty}] }
     → ChangeOrder (status='In Approval')

POST /change-orders/{id}/advance-step
     → advances the current approval step; if it was the last step, contract.oracle_po_rev increments and CO.status='Approved'

GET  /penalties/{id}
     → { fields: [...], slaBreach: {...}, approvalSteps: [...] }

POST /penalties
     body: NewPenaltyRequest (contractId, reason, basis, amount, draftToken, slaActualPct, slaTargetPct, slaBreachMonths)
     → Penalty (status='In Approval', 6-step chain seeded as pending except step 1 = done)

POST /penalties/{id}/advance-step
     → advances chain; on completing "Debit Supplier Account" sets status='Debited'

GET  /evaluations?serviceLine=jr|soft|hard
     → { meta, rows: [{cat, kpi, target, weight, actual, score, weighted}], total, rating, cats: [], adj: [], ratingGuide: [] }

GET    /users
POST   /users            body: UserIn (name, email, department, title, active)
PUT    /users/{id}       body: UserIn
DELETE /users/{id}       -- 204; nulls out any WorkflowStepTemplate.user_id referencing this user

GET  /workflows?appliesTo=
     → [{ id, name, appliesTo, isActive, stepCount, createdAt }]

GET  /workflows/{id}
     → { id, name, appliesTo, isActive, nodes: [@xyflow/react Node], edges: [@xyflow/react Edge] }

POST /workflows           body: { name, appliesTo }
     → WorkflowDetail (single auto-created "Raised" start node, isActive=false)

PUT  /workflows/{id}      body: { name, nodes, edges }
     → WorkflowDetail. 400 unless nodes+edges form one connected linear chain (one start, one end, no
       branches/cycles) — see _ordered_node_ids() in app/routers/workflows.py. Recomputes
       WorkflowStepTemplate rows from the validated chain order on success.

POST /workflows/{id}/activate
     → WorkflowDetail (isActive=true; any other template with the same appliesTo is deactivated)
```

### 2.4 Scoring / Computation Reference (server-side, single source of truth)

```python
def score_kpi(actual: float, target: float, direction: str) -> float:
    if direction == "zero":
        return 100.0 if actual == 0 else 0.0
    if direction == "lower":
        return 100.0 if actual <= target else max(0.0, min(1.0, target / actual) * 100)
    return min(1.0, actual / target) * 100  # higher

def rating(score: float) -> tuple[str, str, str]:  # label, color, bg
    if score >= 90: return "Excellent", "#12805c", "#e6f4ee"
    if score >= 80: return "Good", "#177245", "#e9f5ee"
    if score >= 70: return "Acceptable", "#b45309", "#fbf1e3"
    if score >= 60: return "Poor", "#b54708", "#fbeee3"
    return "Unsatisfactory", "#c0362c", "#fbeceb"
```

Manpower: `contract_amount = reg_hours*reg_rate + ot_hours*ot_rate`; `variance = invoiced − contract_amount`; `status = "Review" if abs(variance) >= 100 else "Matched"`.

CO: `value_impact = (revised_qty - original_qty) * contract_rate`.

IPC: `net_payable = gross - retention - advance_recovered`, where `retention = gross * retention_pct` and `advance_recovered` is capped so cumulative recovery never exceeds `advance_amount`.

## 3. Frontend

### 3.1 Routing (App Router, one route per screen)
`/dashboard`, `/contracts`, `/contracts/new` (chooser), `/contracts/new/work` (PR picker → BOQ form), `/contracts/new/manpower` (rate-card form), `/contracts/[id]` (Scope/Works IPC tracking), `/contracts/[id]/manpower` (Manpower Supply read-only summary), `/manpower`, `/change-orders`, `/penalties`, `/evaluations`, `/users` (User Management), `/approval-flows` (list, grouped by entity type), `/approval-flows/[id]` (React Flow canvas editor). Root `/` redirects to `/dashboard`. The Contracts List routes each row to `/contracts/[id]` or `/contracts/[id]/manpower` based on `contractCategory` — the two contract types never share a detail screen. Both Contract detail screens render a shared `ContractApprovalCard` (`app/contracts/ContractApprovalCard.tsx`) that's empty unless a Contract approval flow has been activated.

### 3.2 Shell
`app/layout.tsx` renders `<Sidebar>` + `<Header pageTitle pageSubtitle>` + page content, matching the design's fixed 248px sidebar / 64px header / `#f4f5f7` content bg.

### 3.3 Data fetching
Server components fetch directly from the FastAPI backend at request time (`fetch(process.env.NEXT_PUBLIC_API_URL + '/...', {cache: 'no-store'})` inside a small wrapper in `lib/api.ts`). Client components (forms, tab-switchers, approve/dispute buttons) call the same `lib/api.ts` functions and re-render on response.

### 3.4 Shared UI primitives (`components/ui/`)
`Card`, `Pill` (status/tag badge — takes `color`/`bg`), `ProgressBar` (track `#f0f1f4`, colored fill), `MonoValue` (IBM Plex Mono numeric span), `DataTable` (generic column-def table matching the header/row styles used across all 8 screens), `ApprovalTimeline` (dot + connecting line + role/name/meta, 3 visual states: done/current/pending).

## 4. Environments

| Env | Frontend | Backend | DB |
| --- | --- | --- | --- |
| Local dev | `next dev` :3001 | `uvicorn --reload` :8010 | Neon Postgres (shared dev branch — see `backend/.env`) |

## 5. Why not the full agentic stack

The brief made LangGraph/Celery/Redis/Tavily/MCP/react-globe.gl/Three.js/MediaPipe/ReactFlow available. This module is a transactional CRUD + approval-chain system with tabular dashboards — most of those tools still don't solve a problem this module has:
- No multi-step autonomous agent reasoning → no LangGraph.
- No long-running async job (nothing here takes >1s) → no Celery/Redis yet.
- No web research/tool-use → no Tavily/MCP.
- No 3D/geospatial visualization → no Three.js/react-globe.gl.
- No camera/gesture interaction anywhere in the brief → no MediaPipe.

**Exception: `@xyflow/react` (React Flow) is now used** — the Approval Flow Builder (`/approval-flows/[id]`) is a genuine node-graph editing problem (visually assembling an ordered approval chain, n8n-style), which is exactly what this library is for. This is the one case where a previously-unused tool from the wider stack was adopted because a real feature needed it, per this section's own stated policy — not added speculatively.

Recharts is a reasonable future add if a screen needs a true chart (currently everything is bars/tables, built directly with Tailwind, matching the HTML reference exactly). Keep this section updated if a real future requirement needs one of these — don't add speculatively.
