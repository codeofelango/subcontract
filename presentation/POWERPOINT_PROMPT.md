# Prompt for the Claude add-in in PowerPoint

Copy everything below into the Claude panel inside PowerPoint. Attach all
14 PNG files from the `screenshots/` folder in this same directory when you
submit the prompt (drag them into the chat or use the attach/upload control).

---

Build a management-facing PowerPoint deck (14–16 slides) presenting the
**Subcontract Management Module** — a new internal system for controlling
subcontracted work given to vendors (construction, soft services, hard
FM/MEP, and manpower supply). This is a working application, not a mockup —
the attached screenshots are real captures from the running app, seeded
with realistic sample data in SAR. Audience: senior management (COO,
Procurement Director, CFO) who need to understand what the system does,
why it matters, and what capability it gives them that they don't have
today. Tone: confident, business-outcome-first — lead with the problem
solved, not the tech stack.

Use a clean, corporate design: dark navy/charcoal accent (matching the
app's sidebar color `#0f1523`) with white slide backgrounds, a blue accent
(`#3a5bd9`), and generous white space. Use IBM Plex Sans-style or a similar
clean sans-serif. Each screenshot should be placed large and legible
(these are dense data screens — don't shrink them so far that numbers
become unreadable), with a short headline above stating the business
takeaway (not just the screen name) and 2–4 bullet points of supporting
context below or beside it.

## Slide-by-slide structure

1. **Title slide** — "Subcontract Management Module" / subtitle: "End-to-end
   control of subcontracted work — from contract to payment to performance."
2. **The problem** (no screenshot) — subcontract spend today is managed
   across disconnected spreadsheets/email: no single view of contract
   value, retention, advances, manpower cost leakage, or vendor
   performance; penalties and change orders lack an audit trail.
3. **What this system does** (no screenshot) — one-line summary of the
   five pillars: Contracts, Progress Payments (IPCs), Manpower
   Reconciliation, Change Orders, Penalties & Performance — all linked to
   Oracle PR/PO.
4. **Portfolio Dashboard** — use `01_dashboard.png`. Takeaway: leadership
   gets a single real-time view of active contracts, portfolio value,
   retention held, advance outstanding, and auto-generated alerts —
   nothing manually compiled.
5. **Contracts at a glance** — use `02_contracts_list.png`. Takeaway: every
   vendor contract, value, progress, and status in one place.
6. **Two contract types, two purpose-built flows** — use
   `03_new_contract_chooser.png`. Takeaway: Scope/Works contracts
   (triggered by an approved Oracle PR) and Manpower Supply contracts
   (rate-card based, no PR) are deliberately separate flows so each
   captures exactly the fields it needs — no bloated one-size-fits-all form.
7. **Scope/Works contract creation** — use `04_new_scope_contract_pr_boq.png`.
   Takeaway: contracts are created directly from the approved Oracle PR
   with BOQ line items — full traceability back to procurement's source
   document.
8. **Manpower contract creation** — use `05_new_manpower_contract_ratecard.png`.
   Takeaway: labour contracts are built on a position rate card (staff
   count, hours, salary, allowances) — the baseline used later for
   automatic reconciliation.
9. **Contract tracking & progress payments (IPC)** — use
   `06_scope_contract_tracking_ipcs.png`. Takeaway: retention, advance
   recovery, and net payable are calculated automatically per progress
   certificate — no manual arithmetic, full payment history visible.
10. **Manpower reconciliation — catching overbilling automatically** — use
    `08_manpower_reconciliation.png`. Takeaway: monthly HCM timesheets are
    matched against contract rates and the vendor invoice line-by-line;
    variances ≥ SAR 100 are flagged for review before payment (call out
    the "Cleaner — overbilled by SAR 2,370" example visible in the
    screenshot as proof this catches real leakage).
11. **Change orders — quantity variations with locked rates** — use
    `09_change_orders.png`. Takeaway: quantities can change but unit rates
    stay locked to the original contract, preventing rate creep; an
    approved change order automatically revises the Oracle PO.
12. **Penalties — governed, auditable, multi-level approval** — use
    `10_penalties.png`. Takeaway: SLA breaches flow through a mandatory
    approval chain (PM → COO → Procurement Director → CFO) with a
    required supporting attachment; the vendor is only debited after CFO
    sign-off — no penalty applied without full governance.
13. **Vendor performance scorecards** — use `11_evaluations.png`. Takeaway:
    every subcontractor is scored on a weighted KPI scorecard (schedule,
    quality, HSE, commercial, resources, materials, documentation) with
    an automatic rating band (Excellent/Good/Acceptable/Poor/
    Unsatisfactory) — feeding directly into renewal and award decisions.
14. **Configurable approval governance** — use `13_approval_flows_list.png`.
    Takeaway: approval chains per entity type (contracts, change orders,
    penalties) are visually configurable by admins, not hardcoded —
    only one active flow per type, keeping approvals linear and
    auditable.
15. **AI activity assistant** — use `15_ai_assistant.png`. Takeaway: a
    searchable, natural-language activity log across every contract,
    approval, and payment event — instant answers instead of digging
    through records.
16. **Closing / next steps** (no screenshot) — summarize the business
    impact (spend visibility, leakage prevention, audit-proof
    governance, vendor accountability) and propose next steps (pilot
    scope, rollout timeline, integration with live Oracle/HCM feeds).

## Formatting rules

- One screenshot per slide maximum (except the two no-screenshot slides).
- Keep bullets short — no more than ~12 words each, 4 bullets max per slide.
- Add a slide number and the section name ("Contract Lifecycle" /
  "Financial Control" / "Governance & Performance") as a small footer/kicker
  so slides read as a coherent story, not a random screen dump.
- Do not fabricate numbers beyond what's visible in the screenshots — pull
  callout figures (like the SAR 2,370 variance) directly from what's shown.
