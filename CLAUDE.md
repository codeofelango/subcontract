# Subcontract Management Module — Project Instructions

## Project Overview

A **subcontract management module** for controlling subcontracted work given to vendors: contract creation from Oracle Purchase Requisitions (PRs), progress payments (IPCs), retention & advance/down-payment tracking, manpower-supply reconciliation (HCM timesheets × contract rates × vendor invoices), quantity change orders that revise the Oracle PO, SLA-linked penalties with a multi-level approval chain, and subcontractor performance evaluations (scorecards).

Currency is **SAR** throughout. The design reference is `Subcontract Module.dc.html` (a self-contained hi-fi HTML prototype — see `README.md`). This repo recreates that design as a real, working app.

---

## Architecture Stack

| Layer | Technology |
| --- | --- |
| Frontend framework | Next.js 14+ (App Router), React 18, TypeScript |
| Styling | Tailwind CSS |
| Icons | lucide-react |
| Charts (if/when needed) | Recharts |
| Workflow canvas | `@xyflow/react` (React Flow) — powers the Approval Flow Builder (`/approval-flows/[id]`) |
| Backend framework | FastAPI (Python 3.11+), async endpoints |
| Validation | Pydantic v2 / pydantic-settings |
| Database | PostgreSQL (Neon, serverless), SQLAlchemy 2.0 async + asyncpg |
| Background jobs (future) | Celery + Redis, APScheduler — not required by current scope |
| Agentic AI (future) | LangGraph, OpenAI/Gemini, Tavily, MCP — not required by current scope |

**Note on the wider stack:** the environment also has Celery/Redis, LangGraph, Tavily, Playwright, react-globe.gl, Three.js, MediaPipe available (ReactFlow/`@xyflow/react` moved out of this list — it's now a real dependency, see above). None of the remaining screens in this module currently need them (there's no long-running agent workflow, 3D geo view, gesture UI, or multi-agent graph here). Don't force these in — only reach for them if a future feature genuinely needs it (e.g., an AI assistant that drafts penalty justifications could use LangGraph + OpenAI later).

---

## Domain Model & Business Rules (must hold in implementation)

- **Contract**: two contract types, created via **completely separate flows that never share fields or validation** (`/contracts/new` is a chooser between them):
  - **Scope / Works Contract** — created from an approved Oracle PR (the process trigger; PR references live at the **line-item level**, e.g. `PR-0123 · L10`). BOQ line items, lump-sum/measured works, IPC-billed, retention & advance apply.
  - **Manpower Supply** — created directly, **with no Oracle PR**. Header is contractor/HR-shaped (issue date, expiry/renewal terms, termination notice, email, payment terms, account number) plus a **position rate card** (one row per job category/position: total staff, working hours, basic salary, H/T/F allowance, share, computed total cost, leave/absence treatment) instead of a BOQ. No retention/advance/payable-terms (don't apply). Rate-based labour, reconciled monthly against HCM timesheets.
- **Contract Type** (the service-type label shown on the header, e.g. "Hard FM (MEP)"/"Manpower") is picked from a maintained lookup list (`ServiceTypeOption`), not free text — same pattern as the existing `PaymentTermOption` lookup.
- **Oracle PO**: auto-created in Oracle when a **Scope/Works** contract is approved; PO number + revision displayed on the contract. Manpower Supply contracts never get a PO (not PR/PO-triggered). Approved Change Orders create **PO revisions** (increment rev number), not new POs.
- **Retention**: withheld per IPC at `retentionPct`, released on handover.
- **Advance**: paid on mobilisation, recovered **pro-rata to progress**. `Net Payable = Gross − Retention − Advance Recovered`.
- **Manpower reconciliation**: contract rates **including OT rates** are the baseline. Monthly HCM attendance (post salary-close) × contract rate is compared per job title against the vendor invoice. Variance is flagged when `|invoiced − contract-computed| ≥ SAR 100`. "Approve Matched" pays only matched (non-flagged) lines; "Raise Dispute" is used for variances.
- **Change Orders**: vary **quantities only** — unit rates stay locked to the contract baseline. `Value Impact = (Revised Qty − Original Qty) × Contract Rate`. An approved CO revises the Oracle PO.
- **Penalties**: require a mandatory supporting attachment and the full sequential approval chain: `PM raises → PM Acknowledge → COO Approval → Procurement Director → CFO Approval → Debit Supplier Account (Finance/AP)`. The supplier is debited **only after CFO approval**.
- **Approval flows are dynamic and configurable** (`/approval-flows`, backed by `WorkflowTemplate`/`WorkflowStepTemplate`): an admin visually builds a **linear** chain of named-approver steps per entity type (Scope/Works Contract, Manpower Supply Contract, Change Order, Penalty) and explicitly **Activates** one flow per type. New Contracts/Change Orders/Penalties seed their real `ApprovalStep` rows from whichever flow is active for their type; if none is active, they fall back to the original built-in chains (e.g. the Penalty chain described above). Only one flow per type can be active at a time — branching/conditional approval is intentionally **not** supported, to match the "no skipping, one step at a time" rule above.
- **Users** (`AppUser`) are a lightweight directory (name/email/department/title) assignable to approval-flow steps — **not a login/auth system**; there is still no session/current-user concept anywhere in the app.
- **Evaluations**: KPI scorecards per subcontractor per service line (Construction/JR, Soft Services, Hard FM/MEP), each with its own KPI set and weights (weights sum to 100). Score rule per KPI:
  - higher-is-better: `min(1, actual/target) × 100`
  - lower-is-better: `actual <= target ? 100 : min(1, target/actual) × 100`
  - zero-target (e.g. LTI count): `100 if actual == 0 else 0`
  - Weighted score = `weight × score / 100`; total = sum of weighted scores.
  - Rating bands: `≥90` Excellent · `80–89.9` Good · `70–79.9` Acceptable · `60–69.9` Poor · `<60` Unsatisfactory.
- **Alerts** on the dashboard are auto-generated (expiring contracts, SLA breaches, progress slippage, pending payments, poor performance trend) — not manually authored.

Real integrations to wire eventually: Oracle PR/PO APIs, HCM attendance feed (monthly), vendor invoice/supplier portal. For now these are modeled as data entities seeded with realistic placeholder values (see `backend/app/seed.py`), matching the values in the design HTML.

---

## Data Model (backend/app/models)

`Contract` (header, type, value, budget, retention_pct, advance_pct, advance_amount, payable_terms_days, source_pr, oracle_po, oracle_po_rev, status, progress_pct, expiry_date — the PR/PO/retention/advance/project fields are nullable and left blank for Manpower Supply)
→ `ContractLineItem` (Scope/Works BOQ only: code, pr_line_ref, description, qty, uom, unit_rate, budget, total)
→ `ManpowerContractDetail` (1:1, Manpower Supply only: issue_date, expiry_terms, termination_notice, email_address, payment_terms_note, account_number) + `ManpowerPositionLine` (rate card: category_position, total_staff, working_hours, basic_salary, h/t/f_allowance, share, total_cost, leave_treatment, absence_treatment)
→ `ServiceTypeOption` (maintained Contract Type lookup, tagged 'scope'|'manpower'|'both')
→ `IPC` (Scope/Works only: number, period, work_done_pct, gross, retention, advance_recovered, net_payable, status)
→ `RetentionLedger`, `AdvanceLedger` (running totals per contract, derived from IPCs)
→ `TimesheetLine` (from HCM: job_title, reg_hours, ot_hours, period) × `VendorInvoiceLine` (job_title, invoiced_amount, period) — reconciled at query time against contract rates
→ `ChangeOrder` (number, reason, status, po_revision) → `ChangeOrderLine` (code, original_qty, revised_qty, contract_rate)
→ `Penalty` (number, reason, basis, amount, status) → `ApprovalStep` (owner_type: contract/change_order/penalty, role, approver_name, state: done/current/pending, acted_at)
→ `Evaluation` (subcontractor, project, period, evaluator, service_line) → `EvaluationKpiRow` (category, kpi, target, direction, weight, actual)
→ `Alert` (type, title, detail, severity) — dashboard only, generated by a query, not hand-authored per contract.

`AppUser` (name, email, department, title, active) — lightweight directory, no login.
`WorkflowTemplate` (name, applies_to, is_active, canvas_nodes, canvas_edges) → `WorkflowStepTemplate` (seq, role, user_id) — configured approval flows; `seed_approval_steps()` (backend/app/workflow_engine.py) materializes real `ApprovalStep` rows from whichever template is active, falling back to each router's original hardcoded chain if none is.

All monetary values are stored as `numeric`/`Decimal`, never floats. All Pydantic schemas mirror these 1:1 with a `Response` suffix.

---

## Environment Variables

### Backend (`backend/.env`)

```
DATABASE_URL=postgresql://neondb_owner:npg_in0V6UsgpBPS@ep-twilight-term-auqw5qfa-pooler.c-10.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8010
CORS_ORIGINS=http://localhost:3001
# Reserved for future agentic/notification features — not required by current scope:
TAVILY_API_KEY=
GOOGLE_API_KEY=
GROQ_API_KEY=
LLM_PROVIDER=google
LLM_MODEL_NAME=gemini-2.5-flash
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
```

Use `pydantic-settings` in `app/config.py` to load these. Never hardcode secrets. `.env` is git-ignored.

### Frontend (`frontend/.env.local`)

```
NEXT_PUBLIC_API_URL=http://localhost:8010
```

> Port note: on this dev machine, port 8000 is blocked by Windows (`WinError 10013`, socket access forbidden — an OS/networking reservation, not an in-use port). We standardized local dev on **8010** instead. If your machine doesn't have that conflict, any free port works — just keep `BACKEND_PORT` and `NEXT_PUBLIC_API_URL` in sync.

---

## Project Structure

```
design_handoff_subcontract_module/
├── CLAUDE.md / PRD.md / ARCHITECTURE.md
├── README.md                        # original design handoff brief
├── Subcontract Module.dc.html       # design reference — do not ship, read-only source of truth for styling/data
│
├── backend/
│   ├── .env
│   ├── requirements.txt
│   └── app/
│       ├── main.py                  # FastAPI app, CORS, router registration
│       ├── config.py                # pydantic-settings
│       ├── database.py              # async engine/session
│       ├── seed.py                  # idempotent seed script (design-reference data)
│       ├── workflow_engine.py       # seed_approval_steps() - active-flow-or-fallback approval seeding
│       ├── models/                  # SQLAlchemy ORM models
│       ├── schemas/                 # Pydantic request/response models
│       └── routers/
│           ├── dashboard.py
│           ├── contracts.py         # list, create, tracking detail
│           ├── manpower.py
│           ├── change_orders.py
│           ├── penalties.py
│           ├── evaluations.py
│           ├── users.py             # AppUser CRUD
│           └── workflows.py         # WorkflowTemplate CRUD, graph validation, activate
│
└── frontend/
    ├── package.json / tsconfig.json / tailwind.config.ts / next.config.ts
    ├── .env.local
    └── src/
        ├── app/
        │   ├── layout.tsx            # sidebar + header shell
        │   ├── page.tsx              # redirect → /dashboard
        │   ├── dashboard/page.tsx
        │   ├── contracts/page.tsx
        │   ├── contracts/new/page.tsx           # chooser: Scope/Works vs Manpower Supply
        │   ├── contracts/new/work/page.tsx      # Oracle PR picker → BOQ form (NewContractForm)
        │   ├── contracts/new/manpower/page.tsx  # rate-card form (ManpowerContractForm), no PR
        │   ├── contracts/[id]/page.tsx          # Scope/Works Contract Tracking (IPCs)
        │   ├── contracts/[id]/manpower/page.tsx # Manpower Supply read-only summary + rate card
        │   ├── manpower/page.tsx
        │   ├── change-orders/page.tsx
        │   ├── penalties/page.tsx
        │   ├── evaluations/page.tsx
        │   ├── users/page.tsx                   # User Management (AppUser directory)
        │   ├── approval-flows/page.tsx          # flows grouped by entity type, Active/Draft pills
        │   └── approval-flows/[id]/CanvasEditor.tsx  # @xyflow/react n8n-style builder
        ├── components/
        │   ├── layout/ (Sidebar, Header)
        │   └── ui/ (Card, Pill, ProgressBar, DataTable, ApprovalTimeline)
        └── lib/
            ├── api.ts                # all fetch calls, typed
            └── types.ts
```

---

## Design Tokens (from the HTML reference — match these exactly)

- **Fonts**: IBM Plex Sans (UI text), IBM Plex Mono (numbers/ids/amounts).
- **Colors**: bg `#f4f5f7`; surface `#fff`; alt row `#fafbfc`; border `#e6e8ec` (light `#f0f1f4`); text `#101828`; secondary `#475467`/`#667085`; muted `#98a2b3`; sidebar `#0f1523`; accent `#3a5bd9`; success `#12805c` on `#e6f4ee`; warning `#b45309` on `#fbf1e3`; danger `#c0362c` on `#fbeceb`; info `#2c7fb0` on `#e7f1f8`; purple `#7a5bd9` on `#f0ecfb`.
- **Radius**: cards 10px; inputs/buttons 7–8px; pills 20px; badges 6px.
- **Sidebar**: 248px fixed, `#0f1523` bg, `#c3cad9` text, active nav item = `rgba(255,255,255,.09)` bg + white text + white dot.
- **Top bar**: 64px, white, border-bottom `#e6e8ec`.
- Full per-screen layout/spacing/typography spec is in `README.md` — read it before building a screen, and cross-check exact values against `Subcontract Module.dc.html` (every style is inline there).

---

## Coding Standards

### Backend (Python)
1. Type hints everywhere; Pydantic v2 models for every request/response.
2. Async endpoints; SQLAlchemy async session via `Depends()`.
3. Wrap external calls in try/except → `HTTPException`.
4. `logging` module for request-level logging.
5. No hardcoded config — everything through `app/config.py`.

### Frontend (TypeScript)
1. Strict TypeScript, no `any`. Interfaces for all API payloads live in `lib/types.ts`.
2. `"use client"` only where interactivity/hooks are needed; prefer server components for static screens.
3. All fetches go through `lib/api.ts` — never `fetch` directly in a component.
4. No external state library — `useState`/`useReducer` only.
5. Recreate the HTML reference **pixel-for-pixel** where it specifies exact values; use Tailwind utility classes (arbitrary values like `text-[13.5px]` are fine) rather than approximating to the default scale.

---

## Running the Project

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m app.seed        # one-time: create tables + seed reference data
uvicorn app.main:app --reload --port 8010
```

### Frontend
```bash
cd frontend
npm install
npm run dev                # http://localhost:3001
```
