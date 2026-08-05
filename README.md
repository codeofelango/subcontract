# Handoff: Subcontract Management Module

## Overview
A subcontract management module for controlling subcontracted work given to vendors: contract creation from Oracle PRs, progress payments (IPCs), retention & advance/down-payment tracking linked to progress, manpower-supply reconciliation (HCM timesheets × contract rates × vendor invoices), quantity change orders that revise the Oracle PO, SLA-linked penalties with a multi-level approval chain, and subcontractor performance evaluations.

Currency: **SAR** throughout.

## About the Design Files
The file in this bundle (`Subcontract Module.dc.html`) is a **design reference created in HTML** — a hi-fi clickable prototype showing intended look and behavior, not production code to copy directly. The task is to **recreate this design in the target codebase's existing environment** (React, Vue, etc.) using its established patterns and libraries — or, if no environment exists yet, choose the most appropriate framework and implement the designs there. The prototype integrates conceptually with **Oracle ERP** (PR/PO) and **Oracle HCM** (attendance/timesheets); real implementations should wire those integrations.

The HTML file is a self-rendering "Design Component": all screens live in one file, switched by a `screen` state variable; every style is inline on the element, so exact values can be read directly from the markup.

## Fidelity
**High-fidelity.** Colors, typography, spacing, and copy are final-intent. Recreate the UI pixel-perfectly using the codebase's existing component library where equivalent components exist. All data values (vendors, amounts, rates, KPI scores) are realistic placeholders to be replaced by live data.

## App Shell
- Left sidebar, `248px` fixed, background `#0f1523`, text `#c3cad9`, sticky full height.
  - Logo block: 34px rounded square in accent color + "Subcontract / Vendor & Manpower Control".
  - Nav groups (uppercase 10px `#5b667e` labels): Overview → Portfolio Dashboard, Contracts; Manage → New Contract, Contract Tracking, Manpower Reconciliation, Change Orders; Governance → Apply Penalty, Evaluations.
  - Nav item: 13px, radius 8px, active = `rgba(255,255,255,.09)` bg + white text + white 6px dot; inactive dot `#5b667e`; hover `rgba(255,255,255,.05)`.
- Top bar, `64px`, white, bottom border `#e6e8ec`, sticky: page title (16.5px/600) + subtitle (12px `#667085`), search field placeholder ("Search contracts, vendors…"), primary button "New Contract" (accent bg, white, radius 8px, 13px/600), avatar circle "RM".
- Main content area: bg `#f4f5f7`, padding `26px 26px 60px`, max content width 1280–1320px.

## Screens / Views

### 1. Portfolio Dashboard
- **KPI row** — 6 equal cards (grid): label 11.5px `#667085`, value 22px/700 IBM Plex Mono, delta note 11px. Values: Active Contracts 24 (+3 this quarter, green), Portfolio Value SAR 68.4M, Executed Spend SAR 41.2M (60% committed), Retention Held SAR 3.9M (SAR 0.4M releasable, amber), Advance Outstanding SAR 2.1M (amber), Expiring ≤30d: 3 (red).
- **Alerts & Attention** (left, 1.55fr) — list rows: colored 8px dot, title 13px/600, detail 12px `#667085`, right pill tag. Alert types: Expiring (amber), SLA (red), Progress (red), Payment (accent blue), Performance (amber). These are auto-generated.
- **Committed Value by Service Type** (right, 1fr) — 4 labeled progress bars: Hard FM (MEP) 34% `#3a5bd9`, Manpower Supply 24% `#4b9fd1`, Construction / JR 22% `#7a5bd9`, Soft Services 20% `#12a679`. Track `#f0f1f4`, 8px, radius 6px.
- **Pending My Action** table — Reference (mono, accent), Item, Vendor, Stage, Amount (right, mono), Waiting (age pill). Rows include contract approval, penalty at CFO, IPC certification, manpower invoice variance review.

### 2. Contracts List
- Filter chips row: Project, Service Type, Vendor, Status, Expiry (white chips, chevron), count at right.
- Register table columns: Contract # (mono, accent), Vendor (600), Type (colored square badge), Project, Value (right, mono), Progress (66px bar + %: ≥80% green `#12805c`, ≥40% accent, else amber `#b45309`), Expiry (mono 12px), Status pill (Active green / Expiring amber / Closing blue / Pending amber).
- Row click navigates to Contract Tracking for that contract. Hover bg `#fafbfc`.
- Type badge colors: Hard FM (MEP) `#3a5bd9`/`#eef1fd`; Manpower `#2c7fb0`/`#e7f1f8`; Construction / JR `#7a5bd9`/`#f0ecfb`; Soft Services `#12805c`/`#e6f4ee`.

### 3. New Contract (creation)
Two-column: form (1fr) + sticky summary rail (320px).
- **Oracle PR trigger banner** (top): accent-tinted bg, icon square, "Triggered by approved Oracle PR — PR-0123, PR-0124", caption "PR lines flow in from Oracle and populate the BOQ below. On approval a PO is auto-created back in Oracle.", green "PR Approved" pill. **The approved Oracle PR is the process trigger.**
- **Contract Type toggle** — two radio cards: "Scope / Works Contract" (selected: 2px accent border, tinted bg; lump-sum/measured works, IPC-billed, retention & advance apply) and "Manpower Supply" (rate-based labour, monthly HCM reconciliation).
- **Contract Header** — 3-col grid of fields: Contractor Name, Contractor No. (read-only grey), Contract Type, Contract Number (auto), Contract Duration, Project Name, Project Number (read-only), Contract Value, Contract Budget.
- **Payment Terms & Securities** — 4 fields with helper notes: Retention % (10% — "Held per IPC, released on handover"), Advance Payment % (10% — "Down payment on mobilisation"), Advance Amount (SAR 420,000 — "Recovered pro-rata to progress"), Payable Terms (45 days — "From certified IPC date").
- **Line Items (BOQ)** table — columns: Code, **Oracle PR Line** (mono, accent — e.g. "PR-0123 · L10"; PR reference is at line-item level), Description, Qty, UoM, Unit Rate, Budget, Total. "+ Add item" link.
- **Summary rail** — rows: Contract Value, Contract Budget, Estimated Saving (green), Retention (10%) amber, Advance (10%) blue, Source PR (Oracle) with caption "Purchase Requisition approved in Oracle — the trigger that starts this contract.", Oracle PO "Auto-created on approval" with caption "Purchase Order is generated automatically in Oracle once the contract is approved."
- **SLA Package** card — pill tags: Response ≤ 4h, Resolution ≤ 24h, PM Completion ≥ 95%, CSAT ≥ 90%; "3 documents attached".
- Footer buttons: Save Draft (secondary), Submit for Approval (primary).

### 4. Contract Tracking
- **Header card**: contract id (mono, accent) + status pill, vendor 17px/600, type · project; chips: "Oracle PO PO-ORA-448120 · Rev 1" (accent tint) and "Source PR PR-0123 / PR-0124" (grey); caption "PO auto-created in Oracle on approval; Source PR is the approved Oracle requisition that triggered this contract." Right side stats: Overall Progress 62%, Remaining Duration 14 mo, Expires date (20px/700 mono).
- **4 finance cards**: Contract Value SAR 4.20M (Budget 4.35M), Executed to Date SAR 2.60M (62% committed), Remaining SAR 1.60M, Penalties Applied SAR 12,500 (red).
- **3 tracker cards**, each with title, progress bar, 3 key/value rows:
  - Retention (10% held, amber bar): Held to date 260,400 / Released 0 / Remaining held 260,400.
  - Advance Recovery (62%, blue bar `#2c7fb0`): Advance paid 420,000 / Recovered 260,400 / Outstanding 159,600. Recovery is pro-rata to progress.
  - Payable Status (89%, green bar): Net certified 2,083,200 / Paid 1,850,000 / Remaining 233,200.
- **IPC table** (Progress Payment Certificates): IPC #, Period, Work Done %, Gross, Retention (amber), Advance Rec. (blue), Net Payable (bold), Status pill (Paid green / Certifying accent). Net = Gross − Retention − Advance recovery.

### 5. Manpower Reconciliation
- **Context bar**: Contract (SC-2024-0155 · Transguard Group), Period (February 2026), Source ("HCM Attendance · post salary-close"), right-aligned Net Variance "+ SAR 2,370" (red, mono 18px/700).
- Legend: green = Matched to contract rate; amber = Variance — review. Italic note: "Contract rates (incl. OT) are the baseline for all calculations."
- **Reconciliation table** — per job title: Reg Hrs, Rate, OT Hrs, OT Rate, **Contract Amount** (computed = reg×rate + ot×otRate; tinted column `#f2f6fc`/`#f8fafd`), Invoiced, Variance (red if |v| ≥ 100), Status pill (Matched/Review). Rows: MEP Technician (35/52.5), Security Guard (22/33), Cleaner (18/27 — Review: OT overbilled), Multi-skill Helper (16/24), Supervisor (45/67.5). Totals row with grand variance.
- **Variance callout** (amber banner): "Cleaner — OT hours invoiced (250) exceed HCM-recorded OT (210). SAR 2,370 overbilled at contract OT rate. Adjust invoice or attach approved overtime authorisation."
- Actions: "Raise Dispute" (secondary), "Approve Matched (SAR 321,118)" (primary).

### 6. Change Orders
Two-column: content (1fr) + sticky rail (330px).
- **CO header card**: CO-2026-003 (mono, accent) + "In Approval" pill, title "Quantity variation — Additional fire & life-safety units", context line (contract, vendor, PO number), "+ New Change Order" button.
- **Affected Line Items** table — Code, Description, Original Qty, Revised Qty, Δ Qty (green +/red −), Contract Rate, Value Impact (± SAR, colored). Note: "Unit rates locked to contract baseline" — only quantities change.
- **Change Order History** table — CO #, Reason, Impact (±, colored), PO Revision, Status pill (Approved/In Approval).
- **Rail — Revised Contract Value**: Original value, Net change impact, Revised value (bold), Retention (10%) revised, Advance (10%) unchanged.
- **Rail — Approval & PO Revision** timeline: Raised by Project Manager → QS / Cost Verification → Procurement Director (current) → **Revise PO in Oracle (PO-ORA-448120 → Rev 2)**. Approved CO revises the Oracle PO.

### 7. Apply Penalty
Two-column: detail (1fr) + approval rail (380px).
- **Penalty card**: PN-2026-004, vendor, "In Approval" pill; field grid: Contract Number, Project, Reason (SLA breach — Cleaning Quality), Basis (2% of monthly service charge), Penalty Amount SAR 42,500 (red, 700), Raised On/by. Footer: mandatory attachment row (Inspection_Report_Jan2026.pdf).
- **Linked SLA Breach** card: red-tinted panel, "84%" big mono red vs SLA target ≥ 90%, breached 2 consecutive months.
- **Approval Route** vertical timeline (caption: "Debited to supplier account only after CFO approval"): Raised by PM → PM Acknowledge → COO Approval → Procurement Director (current) → CFO Approval → Debit Supplier Account (Finance/AP). Done = green filled dot + ✓; current = accent outline; pending = grey.

### 8. Evaluations (Subcontractor scorecards)
- Segmented tabs (pill group, `#eef0f3` track, active = white + shadow + accent text): **Construction / JR**, **Soft Services**, **Hard FM (MEP)** — each a separate scorecard dataset.
- **Meta card**: Subcontractor, Project, Period, Evaluator.
- **KPI table**: Category (shown once per group, 600), KPI, SLA Target, Weight, Actual, Score % (green ≥90 / amber ≥70 / red), Weighted. Weights sum to 100. Score rule: higher-is-better = min(1, actual/target)×100; lower-is-better = target/actual capped; zero-target (LTI) = 100 if 0 else 0. Total Weighted Score row.
- **Rating rail**: big overall score (44px mono, rating-colored), rating pill, per-category weighted bars, Penalty/Incentive card (Penalty %, Incentive %, Net Adjustment), Rating Guide legend: ≥90 Excellent `#12805c`; 80–89.9 Good `#177245`; 70–79.9 Acceptable `#b45309`; 60–69.9 Poor `#b54708`; <60 Unsatisfactory `#c0362c`.
- KPI sets per tab are enumerated in the HTML (`datasets` object in the logic script): JR (Schedule, Quality, HSE, Commercial, Resources, Materials, Documentation), Soft Services (Cleaning, Security, HSE, Customer, Manpower), Hard FM (Service Delivery, Preventive Maint., Asset Performance, Quality, HSE, Customer, Reporting).

## Interactions & Behavior
- Sidebar nav switches screens (SPA-style; implement as routes).
- Contracts list row click → Contract Tracking for that contract.
- Top-bar "New Contract" → creation screen.
- Evaluation tabs switch scorecard datasets; totals/ratings recompute.
- Manpower reconciliation: variance auto-flagged when |invoiced − contract-computed| ≥ SAR 100; "Approve Matched" pays only matched lines; "Raise Dispute" for variances.
- Penalty & Change Order approval chains: sequential; penalty debits supplier only after CFO approval; approved CO issues a PO revision in Oracle.
- Hovers: nav items, table rows (`#fafbfc`), primary buttons (`filter: brightness(1.08)`).
- No animations/transitions were specified; use the codebase's defaults.

## Business Rules (must hold in implementation)
- Approved Oracle **PR is the trigger**; PR references live at **line-item level**.
- **PO auto-created in Oracle** when contract is approved; PO number displayed on contract; change orders create PO **revisions**.
- Retention % withheld per IPC, released on handover; Advance recovered pro-rata to progress; Net payable = Gross − retention − advance recovery.
- Manpower: contract rates **including OT rates** are the calculation baseline; monthly HCM attendance (post salary-close) × contract rates is compared to the vendor invoice per job title.
- Penalty requires a mandatory attachment and the full approval chain (PM → COO → Procurement Director → CFO → debit).
- Change orders vary **quantities only**; unit rates stay locked to contract baseline.

## State Management
- `screen` (current view), `selectedContract`, `evalTab`.
- Data entities: Contract (header, terms, BOQ lines w/ PR line refs, PO ref + revision), IPC, RetentionLedger, AdvanceLedger, TimesheetLine (from HCM), VendorInvoiceLine, ChangeOrder (+lines), Penalty, Evaluation (+KPI rows), Alert, ApprovalStep.
- Data fetching: Oracle PR/PO APIs, HCM attendance feed (monthly), vendor invoices (supplier portal).

## Design Tokens
- **Fonts**: IBM Plex Sans (UI), IBM Plex Mono (numbers, ids, amounts). Weights 400–700.
- **Colors**: bg `#f4f5f7`; surface `#fff`; alt row `#fafbfc`; border `#e6e8ec` (light `#f0f1f4`); text `#101828`; secondary `#475467`/`#667085`; muted `#98a2b3`; sidebar `#0f1523`; accent `#3a5bd9` (themeable — alt options `#0f766e`, `#7c3aed`, `#b45309`); success `#12805c` on `#e6f4ee`; warning `#b45309` on `#fbf1e3`; danger `#c0362c` on `#fbeceb`; info blue `#2c7fb0` on `#e7f1f8`; purple `#7a5bd9` on `#f0ecfb`.
- **Spacing**: card padding 16–20px; section gap 16–20px; table cell ~10–13px vertical / 14–18px horizontal.
- **Radius**: cards 10px; inputs/buttons 7–8px; pills 20px; badges 6px.
- **Type scale**: page title 16.5/600; card title 13.5–14/600; body 13; table 12.5; captions 11–12; column headers 10–11 uppercase +0.03–0.05em; KPI values 19–22/700 mono; hero score 44/700 mono.
- **Pill/badge**: 11px/600, padding 3px 9–10px.

## Assets
No external images. Icons are inline SVG (24px viewBox, stroke-based ~2px — search, plus, document, warning triangle, checkmark). Map to the codebase's icon library (e.g. Lucide/Feather equivalents).

## Files
- `Subcontract Module.dc.html` — the full prototype: all 8 screens (markup with inline styles) + a logic script at the bottom containing all sample datasets, computed reconciliation/scoring logic, and state handling. Read exact styles and data shapes from here.
