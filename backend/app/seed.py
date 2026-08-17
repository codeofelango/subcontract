"""Idempotent dev seed: drops and recreates all tables, then loads realistic reference data
matching the values in `Subcontract Module.dc.html` wherever the two can be made internally
consistent (see ARCHITECTURE.md > 2.4 for the derivation notes on IPC/tracker figures).

Run with: python -m app.seed
"""

import asyncio
import datetime
from decimal import Decimal

from app.business import money
from app.database import Base, async_session_maker, engine
from app.models import (
    ActivityLogEntry,
    AppUser,
    ApprovalStep,
    ChangeOrder,
    ChangeOrderLine,
    Contract,
    ContractLineItem,
    Evaluation,
    EvaluationKpiRow,
    GrnLine,
    Ipc,
    ManpowerContractDetail,
    ManpowerPositionLine,
    OracleContractor,
    OraclePr,
    OraclePrLine,
    OracleProject,
    PaymentTermOption,
    Penalty,
    ServiceTypeOption,
    TimesheetLine,
    VendorInvoiceLine,
    VendorPortalSubmission,
    WorkflowStepTemplate,
    WorkflowTemplate,
)

D = Decimal


CONTRACTS = [
    dict(id="SC-2024-0142", vendor_name="Emrill Services", contractor_no="V-100482", contract_type="scope",
         service_type="Hard FM (MEP)", project_name="Marina Gate Towers", project_no="PRJ-0219", duration_months=24,
         contract_value=D("4200000"), contract_budget=D("4350000"), advance_amount=D("420000"),
         source_pr="PR-0123 / PR-0124", oracle_po="PO-ORA-448120", oracle_po_rev="Rev 1", status="Active",
         progress_pct=62, expiry_date=datetime.date(2027, 3, 31), remaining_months=14,
         location="Dubai", vat_pct=D("15.00"), advance2_pct=D("5.00"), advance2_amount=D("210000")),
    dict(id="SC-2024-0155", vendor_name="Transguard Group", contractor_no="V-100511", contract_type="manpower",
         service_type="Manpower", project_name="Facilities — multi-site", project_no="PRJ-0301", duration_months=36,
         contract_value=D("6800000"), contract_budget=D("6800000"), advance_amount=D("0"), retention_pct=D("0"),
         advance_pct=D("0"), source_pr="PR-0201", oracle_po="PO-ORA-448201", oracle_po_rev="Rev 1", status="Active",
         progress_pct=74, expiry_date=datetime.date(2026, 8, 15), remaining_months=8),
    dict(id="SC-2025-0031", vendor_name="Al Faris Contracting", contractor_no="V-100602", contract_type="scope",
         service_type="Construction / JR", project_name="Dubai Hills Villas", project_no="PRJ-0410", duration_months=20,
         contract_value=D("12500000"), contract_budget=D("12900000"), advance_amount=D("1250000"),
         source_pr="PR-0305", oracle_po="PO-ORA-448305", oracle_po_rev="Rev 1", status="Active",
         progress_pct=38, expiry_date=datetime.date(2026, 12, 1), remaining_months=11),
    dict(id="SC-2024-0098", vendor_name="Berkeley Services", contractor_no="V-100320", contract_type="scope",
         service_type="Soft Services", project_name="Business Bay Offices", project_no="PRJ-0155", duration_months=18,
         contract_value=D("2150000"), contract_budget=D("2200000"), advance_amount=D("215000"),
         source_pr="PR-0088", oracle_po="PO-ORA-447088", oracle_po_rev="Rev 1", status="Expiring",
         progress_pct=88, expiry_date=datetime.date(2026, 2, 28), remaining_months=1),
    dict(id="SC-2025-0044", vendor_name="Imdaad", contractor_no="V-100655", contract_type="scope",
         service_type="Soft Services", project_name="Community Parks", project_no="PRJ-0455", duration_months=24,
         contract_value=D("1760000"), contract_budget=D("1800000"), advance_amount=D("176000"),
         source_pr="PR-0410", oracle_po="PO-ORA-448410", oracle_po_rev="Rev 1", status="Active",
         progress_pct=21, expiry_date=datetime.date(2027, 1, 31), remaining_months=18),
    dict(id="SC-2023-0210", vendor_name="ENGIE Cofely", contractor_no="V-100118", contract_type="scope",
         service_type="Hard FM (MEP)", project_name="Airport Terminal 2", project_no="PRJ-0072", duration_months=36,
         contract_value=D("9300000"), contract_budget=D("9500000"), advance_amount=D("930000"),
         source_pr="PR-0012", oracle_po="PO-ORA-446012", oracle_po_rev="Rev 2", status="Closing",
         progress_pct=96, expiry_date=datetime.date(2026, 1, 31), remaining_months=0),
    dict(id="SC-2025-0051", vendor_name="Khansaheb FM", contractor_no="V-100701", contract_type="scope",
         service_type="Hard FM (MEP)", project_name="Expo City Offices", project_no="PRJ-0500", duration_months=24,
         contract_value=D("5400000"), contract_budget=D("5600000"), advance_amount=D("540000"),
         source_pr="PR-0512", oracle_po=None, oracle_po_rev=None, status="Pending",
         progress_pct=0, expiry_date=None, remaining_months=24),
]

# Manpower Supply contracts are created without an Oracle PR — no project/PO/retention/advance,
# a rate-card (ManpowerPositionLine) instead of a BOQ. Value/budget = sum(total_cost * total_staff).
MANPOWER_CONTRACT = dict(
    id="SC-2025-0060", vendor_name="Al Benayat Al Zahabiah", contractor_no="V-100910", contract_type="manpower",
    service_type="Manpower", project_name=None, project_no=None, duration_months=0,
    contract_value=D("420000"), contract_budget=D("420000"), retention_pct=D("0"), advance_pct=D("0"),
    advance_amount=D("0"), payable_terms_days=0, source_pr=None, oracle_po=None, oracle_po_rev=None,
    status="Active", progress_pct=0, expiry_date=None, remaining_months=0,
)
MANPOWER_CONTRACT_DETAIL = dict(
    issue_date=datetime.date(2025, 1, 1), expiry_terms="Automatic renewal", termination_notice="60 Days",
    email_address="hassan@bfm.sa", payment_terms_note="5 days from issue invoice",
    account_number="SA5700006820199853800",
)
MANPOWER_POSITION_LINES = [
    dict(category_position="Janitor", total_staff=200, working_hours=D("8"), basic_salary=D("600"),
         h_allowance=D("0"), t_allowance=D("0"), f_allowance=D("0"), share=D("1500"), total_cost=D("2100"),
         leave_treatment="Deductible", absence_treatment="Non-Deductible"),
]

SERVICE_TYPE_OPTIONS = [
    dict(label="Hard FM (MEP)", contract_category="scope", sort_order=0),
    dict(label="Soft Services", contract_category="scope", sort_order=1),
    dict(label="Construction / JR", contract_category="scope", sort_order=2),
    dict(label="Manpower", contract_category="manpower", sort_order=3),
]

# People already named in today's hardcoded penalty/CO approval templates, plus a few more —
# lets a first Approval Flow be built in the UI against a realistic directory immediately.
# `role` is the fixed SSO access role (admin|procurement_requester|hr_requester|approver|None) -
# separate from `title`, which is just the approval-chain display label.
APP_USERS = [
    dict(name="R. Menon", email="r.menon@mafas.com", department="PMO", title="Project Manager", active=True, role="approver", is_quick_login=True),
    dict(name="K. Ibrahim", email="k.ibrahim@mafas.com", department="Procurement", title="QS / Cost Verification", active=True, role="procurement_requester", is_quick_login=True),
    dict(name="S. Farooq", email="s.farooq@mafas.com", department="Procurement", title="Procurement Director", active=True, role="approver"),
    dict(name="A. Khalil", email="a.khalil@mafas.com", department="Executive", title="COO", active=True, role="approver"),
    dict(name="M. Haddad", email="m.haddad@mafas.com", department="Finance", title="CFO", active=True, role="approver"),
    dict(name="Finance / AP", email="ap@mafas.com", department="Finance", title="Accounts Payable", active=True, role="approver"),
    dict(name="H. Al-Sayed", email="h.alsayed@mafas.com", department="HR", title="HR Lead", active=True, role="hr_requester"),
]

# One person, two directory rows sharing the same email — a single account can be assigned as
# the named approver on two different steps of a chain (see CONTRACT_APPROVAL_FLOWS below).
# Only ONE of the two rows carries a login `role` (the CFO row, as Admin) - login resolves to
# the first active row for that email with a non-null role, so the Procurement Director row
# deliberately stays role=None to avoid ambiguity (see AppUser docstring in models/tables.py).
ELANGO_PROCUREMENT_DIRECTOR = dict(
    name="Elango Shunmugaraj", email="elango@mafas.com", department="Procurement", title="Procurement Director", active=True, role=None
)
ELANGO_CFO = dict(name="Elango Shunmugaraj", email="elango@mafas.com", department="Finance", title="CFO", active=True, role="admin", is_quick_login=True)

# Sample dynamic approval flows, one per contract-creation route (Scope/Works vs Manpower Supply -
# see app/routers/workflows.py APPLIES_TO_VALUES). Activated immediately so every contract submitted
# after seeding is routed through this chain via seed_approval_steps(); admins can still add/remove/
# reassign steps at any time from /approval-flows since the chain is re-read fresh on each submission.
CONTRACT_APPROVAL_FLOWS = [
    dict(name="Scope/Works Contract — Procurement & Finance Sign-off", applies_to="contract_scope"),
    dict(name="Manpower Supply Contract — Procurement & Finance Sign-off", applies_to="contract_manpower"),
]

SC_0142_LINE_ITEMS = [
    dict(code="MEP-01", pr_line_ref="PR-0123 · L10", description="HVAC preventive maintenance — 12 months",
         qty=D("12"), uom="month", unit_rate=D("95000"), budget=D("1180000"), total=D("1140000"),
         sla_tags="Response ≤ 4h|Resolution ≤ 24h"),
    dict(code="MEP-02", pr_line_ref="PR-0123 · L20", description="Electrical systems maintenance",
         qty=D("12"), uom="month", unit_rate=D("62000"), budget=D("760000"), total=D("744000"),
         sla_tags="Response ≤ 4h|PM Completion ≥ 95%"),
    dict(code="MEP-03", pr_line_ref="PR-0123 · L30", description="Plumbing & drainage",
         qty=D("12"), uom="month", unit_rate=D("38000"), budget=D("470000"), total=D("456000"),
         sla_tags="Resolution ≤ 24h"),
    dict(code="MEP-04", pr_line_ref="PR-0124 · L10", description="BMS & controls",
         qty=D("12"), uom="month", unit_rate=D("41000"), budget=D("500000"), total=D("492000"),
         sla_tags="CSAT ≥ 90%"),
    dict(code="MEP-05", pr_line_ref="PR-0124 · L20", description="Fire & life safety systems",
         qty=D("12"), uom="month", unit_rate=D("55700"), budget=D("640000"), total=D("668400"),
         sla_tags="Response ≤ 4h|Resolution ≤ 24h|CSAT ≥ 90%"),
]

ORACLE_PRS = [
    dict(id="PR-0530", vendor_name="Al Rowad Building Services", contractor_no="V-100788",
         contract_type="scope", service_type="Hard FM (MEP)", project_name="Sky Gardens Residences",
         project_no="PRJ-0560", duration_months=24, contract_value=D("3850000"), contract_budget=D("4000000"),
         retention_pct=D("10"), advance_pct=D("15"), payable_terms_days=30),
    dict(id="PR-0531", vendor_name="Farnek Services", contractor_no="V-100812",
         contract_type="scope", service_type="Soft Services", project_name="Palm Views Residences",
         project_no="PRJ-0575", duration_months=12, contract_value=D("1450000"), contract_budget=D("1500000"),
         retention_pct=D("10"), advance_pct=D("10"), payable_terms_days=45),
    dict(id="PR-0532", vendor_name="Drake & Scull", contractor_no="V-100845",
         contract_type="scope", service_type="Construction / JR", project_name="Downtown Views Extension",
         project_no="PRJ-0590", duration_months=18, contract_value=D("7200000"), contract_budget=D("7500000"),
         retention_pct=D("5"), advance_pct=D("20"), payable_terms_days=60),
]
PR_0530_LINES = [
    dict(code="MEP-01", pr_line_ref="PR-0530 · L10", description="HVAC preventive maintenance — 12 months",
         qty=D("12"), uom="month", unit_rate=D("88000"), budget=D("1100000"),
         sla_tags="Response ≤ 4h|Resolution ≤ 24h"),
    dict(code="MEP-02", pr_line_ref="PR-0530 · L20", description="Electrical systems maintenance",
         qty=D("12"), uom="month", unit_rate=D("57000"), budget=D("700000"),
         sla_tags="Response ≤ 4h|PM Completion ≥ 95%"),
    dict(code="MEP-03", pr_line_ref="PR-0530 · L30", description="Plumbing & drainage",
         qty=D("12"), uom="month", unit_rate=D("35000"), budget=D("440000"),
         sla_tags="Resolution ≤ 24h"),
    dict(code="MEP-04", pr_line_ref="PR-0530 · L40", description="BMS & controls",
         qty=D("12"), uom="month", unit_rate=D("39000"), budget=D("480000"),
         sla_tags="CSAT ≥ 90%"),
]
PR_0531_LINES = [
    dict(code="SS-01", pr_line_ref="PR-0531 · L10", description="Daily cleaning & janitorial services",
         qty=D("12"), uom="month", unit_rate=D("68000"), budget=D("720000"),
         sla_tags="CSAT ≥ 90%"),
    dict(code="SS-02", pr_line_ref="PR-0531 · L20", description="Landscaping & pest control",
         qty=D("12"), uom="month", unit_rate=D("52000"), budget=D("550000"),
         sla_tags="Response ≤ 4h"),
]
PR_0532_LINES = [
    dict(code="CJR-01", pr_line_ref="PR-0532 · L10", description="Structural works — Phase 2",
         qty=D("1"), uom="lump sum", unit_rate=D("4200000"), budget=D("4350000"),
         sla_tags="Milestone completion ≥ 95%"),
    dict(code="CJR-02", pr_line_ref="PR-0532 · L20", description="MEP rough-in — Phase 2",
         qty=D("1"), uom="lump sum", unit_rate=D("2600000"), budget=D("2700000"),
         sla_tags="Milestone completion ≥ 95%"),
]

ORACLE_CONTRACTORS = [
    dict(contractor_no=c["contractor_no"], vendor_name=c["vendor_name"]) for c in CONTRACTS
] + [dict(contractor_no=pr["contractor_no"], vendor_name=pr["vendor_name"]) for pr in ORACLE_PRS] + [
    dict(contractor_no=MANPOWER_CONTRACT["contractor_no"], vendor_name=MANPOWER_CONTRACT["vendor_name"])
]

ORACLE_PROJECTS = [
    dict(project_no=c["project_no"], project_name=c["project_name"]) for c in CONTRACTS if c["project_no"]
] + [dict(project_no=pr["project_no"], project_name=pr["project_name"]) for pr in ORACLE_PRS]

PAYMENT_TERM_OPTIONS = [
    *[dict(category="retention_pct", value=v, label=f"{v}%", sort_order=i) for i, v in enumerate([D("5"), D("10"), D("15")])],
    *[dict(category="advance_pct", value=v, label=f"{v}%", sort_order=i) for i, v in enumerate([D("0"), D("10"), D("15"), D("20")])],
    *[dict(category="payable_terms_days", value=v, label=f"{v} days", sort_order=i) for i, v in enumerate([D("15"), D("30"), D("45"), D("60"), D("90")])],
]

SC_0142_IPCS = [
    dict(number="IPC 1", period="Q3 2025", work_done_pct=D("18"), gross=D("756000"), retention=D("75600"), advance_recovered=D("113400"), net_payable=D("567000"), status="Paid",
         invoice_number="INV-0142-01", period_from=datetime.date(2025, 7, 1), period_to=datetime.date(2025, 9, 30), equipment_rental_deduction=D("0"),
         oracle_push_status="Pushed", oracle_confirmation_code="ORA-CONF-100201"),
    dict(number="IPC 2", period="Q4 2025", work_done_pct=D("34"), gross=D("672000"), retention=D("67200"), advance_recovered=D("100800"), net_payable=D("504000"), status="Paid",
         invoice_number="INV-0142-02", period_from=datetime.date(2025, 10, 1), period_to=datetime.date(2025, 12, 31), equipment_rental_deduction=D("0"),
         oracle_push_status="Pushed", oracle_confirmation_code="ORA-CONF-100202"),
    dict(number="IPC 3", period="Q1 2026", work_done_pct=D("52"), gross=D("756000"), retention=D("75600"), advance_recovered=D("46200"), net_payable=D("634200"), status="Paid",
         invoice_number="INV-0142-03", period_from=datetime.date(2026, 1, 1), period_to=datetime.date(2026, 3, 31), equipment_rental_deduction=D("8500"),
         oracle_push_status="Pushed", oracle_confirmation_code="ORA-CONF-100203"),
    # IPC 4's advance recovery is capped: only SAR 159,600 of the 10% advance remains outstanding at this point.
    # Still Certifying and not yet pushed to Oracle - demonstrates the pending state on the tracking page.
    dict(number="IPC 4", period="Q2 2026", work_done_pct=D("62"), gross=D("420000"), retention=D("42000"), advance_recovered=D("0"), net_payable=D("378000"), status="Certifying",
         invoice_number="INV-0142-04", period_from=datetime.date(2026, 4, 1), period_to=datetime.date(2026, 6, 30), equipment_rental_deduction=D("0")),
]

# Simulated Oracle GRN (Goods Receipt Note) feed - one delivery/service-completion event per BOQ
# line per IPC period, logged independently of the vendor's self-declared work-done % above. Four
# of five lines track the claimed progress closely (small realistic rounding noise); MEP-03 (Plumbing
# & drainage) is deliberately under-delivered, growing into a visible variance by IPC 4 - demonstrates
# the GRN Invoice report's ability to flag claimed-vs-actually-received discrepancies.
SC_0142_GRN_QTY_BY_CODE = {
    "MEP-01": [D("2.5917"), D("2.3050"), D("2.5896"), D("1.4407")],
    "MEP-02": [D("2.5917"), D("2.3050"), D("2.5896"), D("1.4407")],
    "MEP-03": [D("2.5917"), D("2.10"), D("1.90"), D("1.00")],  # under-delivered from IPC 2 onward
    "MEP-04": [D("2.5917"), D("2.3050"), D("2.5896"), D("1.4407")],
    "MEP-05": [D("2.5917"), D("2.3050"), D("2.5896"), D("1.4407")],
}
SC_0142_GRN_PERIOD_DATES = [datetime.date(2025, 9, 30), datetime.date(2025, 12, 31), datetime.date(2026, 3, 31), datetime.date(2026, 6, 30)]

# Vendor's next progress claim via the Oracle vendor portal - not yet certified into an IPC.
SC_0142_VENDOR_SUBMISSIONS = [
    dict(period="Q3 2026", work_done_pct=D("74"), gross_claimed=D("480000"), submitted_by="Emrill Services — Vendor Portal", status="Submitted"),
]

MP_BASE = [
    dict(job_title="MEP Technician", nationality="Indian", employee_count=10, reg_hours=D("1760"), reg_rate=D("35"), ot_hours=D("96"), ot_rate=D("52.5"), invoiced=D("66640")),
    dict(job_title="Security Guard", nationality="Nepalese", employee_count=24, reg_hours=D("4224"), reg_rate=D("22"), ot_hours=D("380"), ot_rate=D("33"), invoiced=D("105468")),
    dict(job_title="Cleaner", nationality="Bangladeshi", employee_count=20, reg_hours=D("3520"), reg_rate=D("18"), ot_hours=D("210"), ot_rate=D("27"), invoiced=D("71400")),
    dict(job_title="Multi-skill Helper", nationality="Pakistani", employee_count=15, reg_hours=D("2640"), reg_rate=D("16"), ot_hours=D("140"), ot_rate=D("24"), invoiced=D("45600")),
    dict(job_title="Supervisor", nationality="Filipino", employee_count=4, reg_hours=D("704"), reg_rate=D("45"), ot_hours=D("40"), ot_rate=D("67.5"), invoiced=D("34380")),
]
MP_PERIOD = "February 2026"

CHANGE_ORDERS = [
    dict(id="CO-2026-001", contract_id="SC-2024-0142", title="Additional AHU servicing — scope increase",
         reason="Additional AHU servicing — scope increase", status="Approved", po_revision_label="Rev 1",
         lines=[dict(code="MEP-01", description="HVAC preventive maintenance — extra AHU unit", original_qty=D("12"), revised_qty=D("13"), contract_rate=D("96000"))]),
    dict(id="CO-2026-002", contract_id="SC-2024-0142", title="Descope — external drainage line",
         reason="Descope — external drainage line", status="Approved", po_revision_label="Rev 1",
         lines=[dict(code="MEP-03X", description="External drainage line (descoped)", original_qty=D("1"), revised_qty=D("0"), contract_rate=D("42000"))]),
    dict(id="CO-2026-003", contract_id="SC-2024-0142", title="Quantity variation — Additional fire & life-safety units",
         reason="Additional fire & life-safety units", status="In Approval", po_revision_label="Rev 2 pending",
         lines=[
             dict(code="MEP-01", description="HVAC preventive maintenance", original_qty=D("12"), revised_qty=D("14"), contract_rate=D("95000")),
             dict(code="MEP-03", description="Plumbing & drainage", original_qty=D("12"), revised_qty=D("11"), contract_rate=D("38000")),
         ]),
]
CO_003_STEPS = [
    dict(seq=0, role="Raised by Project Manager", approver_name="R. Menon", state="done", meta_note="Qty variation logged · 08 Feb 2026"),
    dict(seq=1, role="QS / Cost Verification", approver_name="K. Ibrahim", state="done", meta_note="Rates checked vs contract · 09 Feb 2026"),
    dict(seq=2, role="Procurement Director", approver_name="S. Farooq", state="current", meta_note="Awaiting approval"),
    dict(seq=3, role="Revise PO in Oracle", approver_name="PO-ORA-448120 → Rev 2", state="pending", meta_note="Pending approval"),
]

PENALTY = dict(
    id="PN-2026-004", contract_id="SC-2024-0098", reason="SLA breach — Cleaning Quality",
    basis="2% of monthly service charge", amount=D("42500"), status="In Approval",
    attachment_ref="Inspection_Report_Jan2026.pdf", raised_by="R. Menon (PM)",
    raised_on=datetime.date(2026, 2, 5), sla_actual_pct=D("84"), sla_target_pct=D("90"),
    sla_breach_months=2, sla_label="Cleaning Quality Score",
)
PENALTY_STEPS = [
    dict(seq=0, role="Raised by Project Manager", approver_name="R. Menon", state="done", meta_note="Completed · 05 Feb 2026"),
    dict(seq=1, role="PM Acknowledge", approver_name="R. Menon", state="done", meta_note="Attachment verified · 05 Feb 2026"),
    dict(seq=2, role="COO Approval", approver_name="A. Khalil", state="done", meta_note="Approved · 07 Feb 2026"),
    dict(seq=3, role="Procurement Director", approver_name="S. Farooq", state="current", meta_note="Awaiting review"),
    dict(seq=4, role="CFO Approval", approver_name="M. Haddad", state="pending", meta_note="Pending"),
    dict(seq=5, role="Debit Supplier Account", approver_name="Finance / AP", state="pending", meta_note="Pending"),
]

EVALUATIONS = {
    "jr": dict(
        subcontractor="Al Faris Contracting", project="Dubai Hills Villas", period="Q1 2026", evaluator="PMO / QAQC",
        penalty_adj_pct=D("-3"), incentive_adj_pct=D("0"),
        kpis=[
            ("Schedule", "Milestone / activity completion vs baseline", "≥95%", D("0.95"), "higher", D("12"), D("0.91")),
            ("Schedule", "Weekly progress vs approved look-ahead", "≥90%", D("0.90"), "higher", D("8"), D("0.86")),
            ("Quality", "Workmanship inspection pass rate", "≥95%", D("0.95"), "higher", D("10"), D("0.93")),
            ("Quality", "Snag / punch list closure within SLA", "≥90%", D("0.90"), "higher", D("10"), D("0.88")),
            ("Quality", "Rework rate (% of completed value)", "≤3%", D("0.03"), "lower", D("8"), D("0.045")),
            ("HSE", "Lost Time Incidents (LTI)", "0", D("0"), "zero", D("10"), D("0")),
            ("HSE", "PTW / method statement / JSA compliance", "100%", D("1"), "higher", D("7"), D("0.98")),
            ("HSE", "Housekeeping & site safety score", "≥95%", D("0.95"), "higher", D("5"), D("0.90")),
            ("Commercial", "Progress billing submitted on time", "100%", D("1"), "higher", D("5"), D("0.80")),
            ("Commercial", "VO substantiation turnaround", "≥90%", D("0.90"), "higher", D("5"), D("0.85")),
            ("Commercial", "Unapproved cost overrun vs value", "≤2%", D("0.02"), "lower", D("5"), D("0.015")),
            ("Resources", "Skilled manpower availability vs plan", "≥95%", D("0.95"), "higher", D("5"), D("0.90")),
            ("Resources", "Supervisor / engineer attendance", "≥95%", D("0.95"), "higher", D("3"), D("0.96")),
            ("Materials", "Submittal / sample lead-time compliance", "≥90%", D("0.90"), "higher", D("3"), D("0.82")),
            ("Documentation", "As-built / handover dossier on time", "≥90%", D("0.90"), "higher", D("4"), D("0.70")),
        ],
    ),
    "soft": dict(
        subcontractor="Berkeley Services", project="Business Bay Offices", period="Jan 2026", evaluator="FM Ops",
        penalty_adj_pct=D("-5"), incentive_adj_pct=D("0"),
        kpis=[
            ("Cleaning", "Cleaning quality score", "≥90%", D("0.90"), "higher", D("15"), D("0.84")),
            ("Cleaning", "Frequency compliance", "100%", D("1"), "higher", D("10"), D("0.98")),
            ("Cleaning", "Complaint rate", "≤5%", D("0.05"), "lower", D("10"), D("0.07")),
            ("Security", "Incident response time", "≥95%", D("0.95"), "higher", D("10"), D("0.92")),
            ("Security", "Patrol compliance", "100%", D("1"), "higher", D("10"), D("0.97")),
            ("Security", "Incident reporting accuracy", "≥95%", D("0.95"), "higher", D("5"), D("0.94")),
            ("HSE", "Safety compliance", "100%", D("1"), "higher", D("10"), D("0.99")),
            ("HSE", "Training attendance", "≥95%", D("0.95"), "higher", D("5"), D("0.90")),
            ("Customer", "Customer satisfaction (CSAT)", "≥90%", D("0.90"), "higher", D("10"), D("0.88")),
            ("Customer", "Complaint closure time", "≥95%", D("0.95"), "higher", D("5"), D("0.93")),
            ("Manpower", "Staff attendance", "100%", D("1"), "higher", D("5"), D("0.97")),
            ("Manpower", "Grooming & conduct", "≥95%", D("0.95"), "higher", D("5"), D("0.92")),
        ],
    ),
    "hard": dict(
        subcontractor="ENGIE Cofely", project="Airport Terminal 2", period="Q4 2025", evaluator="Hard FM",
        penalty_adj_pct=D("-2"), incentive_adj_pct=D("0"),
        kpis=[
            ("Service Delivery", "Response time compliance", "≥95%", D("0.95"), "higher", D("12.5"), D("0.93")),
            ("Service Delivery", "Resolution time compliance", "≥90%", D("0.90"), "higher", D("12.5"), D("0.89")),
            ("Service Delivery", "First-time fix rate", "≥85%", D("0.85"), "higher", D("12.5"), D("0.87")),
            ("Preventive Maint.", "PM completion", "≥95%", D("0.95"), "higher", D("12.5"), D("0.96")),
            ("Preventive Maint.", "PM quality score", "≥90%", D("0.90"), "higher", D("6.25"), D("0.91")),
            ("Asset Performance", "MTTR compliance", "Within SLA", D("0.90"), "higher", D("6.25"), D("0.88")),
            ("Quality", "NCR closure", "≥95%", D("0.95"), "higher", D("6.25"), D("0.92")),
            ("HSE", "Incident rate (LTI)", "0", D("0"), "zero", D("6.25"), D("0")),
            ("HSE", "PTW compliance", "100%", D("1"), "higher", D("6.25"), D("0.98")),
            ("Customer", "CSAT", "≥90%", D("0.90"), "higher", D("6.25"), D("0.90")),
            ("Customer", "Complaint closure", "≥95%", D("0.95"), "higher", D("6.25"), D("0.94")),
            ("Reporting", "Timely reports", "100%", D("1"), "higher", D("3.75"), D("0.95")),
            ("Reporting", "CMMS accuracy", "≥95%", D("0.95"), "higher", D("2.5"), D("0.93")),
        ],
    ),
}


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        for c in CONTRACTS:
            session.add(Contract(**c))
        session.add(Contract(**MANPOWER_CONTRACT))
        await session.flush()

        sc_0142_lines_by_code: dict[str, ContractLineItem] = {}
        for li in SC_0142_LINE_ITEMS:
            line_item = ContractLineItem(contract_id="SC-2024-0142", **li)
            session.add(line_item)
            sc_0142_lines_by_code[li["code"]] = line_item
        await session.flush()  # assigns line_item.id, needed for the GRN rows below

        for ipc in SC_0142_IPCS:
            session.add(Ipc(contract_id="SC-2024-0142", **ipc))

        for code, qtys_by_period in SC_0142_GRN_QTY_BY_CODE.items():
            line_item = sc_0142_lines_by_code[code]
            for period_idx, qty in enumerate(qtys_by_period):
                session.add(GrnLine(
                    contract_id="SC-2024-0142", line_item_id=line_item.id, grn_number=f"GRN-0142-{code}-{period_idx + 1}",
                    qty_received=qty, received_date=SC_0142_GRN_PERIOD_DATES[period_idx],
                ))
        for sub in SC_0142_VENDOR_SUBMISSIONS:
            session.add(VendorPortalSubmission(contract_id="SC-2024-0142", **sub))

        session.add(ManpowerContractDetail(contract_id=MANPOWER_CONTRACT["id"], **MANPOWER_CONTRACT_DETAIL))
        for line in MANPOWER_POSITION_LINES:
            session.add(ManpowerPositionLine(contract_id=MANPOWER_CONTRACT["id"], **line))

        for pr in ORACLE_PRS:
            session.add(OraclePr(**pr))
        await session.flush()
        for line in PR_0530_LINES:
            session.add(OraclePrLine(pr_id="PR-0530", **line))
        for line in PR_0531_LINES:
            session.add(OraclePrLine(pr_id="PR-0531", **line))
        for line in PR_0532_LINES:
            session.add(OraclePrLine(pr_id="PR-0532", **line))

        for opt in PAYMENT_TERM_OPTIONS:
            session.add(PaymentTermOption(**opt))
        for opt in SERVICE_TYPE_OPTIONS:
            session.add(ServiceTypeOption(**opt))
        for u in APP_USERS:
            session.add(AppUser(**u))
        elango_pd = AppUser(**ELANGO_PROCUREMENT_DIRECTOR)
        elango_cfo = AppUser(**ELANGO_CFO)
        session.add(elango_pd)
        session.add(elango_cfo)
        await session.flush()  # assign ids so the workflow steps below can reference them

        for flow in CONTRACT_APPROVAL_FLOWS:
            nodes = [
                {"id": "n1", "type": "step", "position": {"x": 60, "y": 120}, "data": {"label": "Raised", "userId": None}},
                {"id": "n2", "type": "step", "position": {"x": 300, "y": 120}, "data": {"label": "Procurement Director Approval", "userId": elango_pd.id}},
                {"id": "n3", "type": "step", "position": {"x": 540, "y": 120}, "data": {"label": "CFO Approval", "userId": elango_cfo.id}},
            ]
            edges = [
                {"id": "e-n1-n2", "source": "n1", "target": "n2"},
                {"id": "e-n2-n3", "source": "n2", "target": "n3"},
            ]
            template = WorkflowTemplate(name=flow["name"], applies_to=flow["applies_to"], is_active=True, canvas_nodes=nodes, canvas_edges=edges)
            session.add(template)
            await session.flush()
            session.add(WorkflowStepTemplate(template_id=template.id, seq=0, role="Raised", user_id=None))
            session.add(WorkflowStepTemplate(template_id=template.id, seq=1, role="Procurement Director Approval", user_id=elango_pd.id))
            session.add(WorkflowStepTemplate(template_id=template.id, seq=2, role="CFO Approval", user_id=elango_cfo.id))

        for c in ORACLE_CONTRACTORS:
            session.add(OracleContractor(**c))
        for p in ORACLE_PROJECTS:
            session.add(OracleProject(**p))

        for row in MP_BASE:
            session.add(TimesheetLine(
                contract_id="SC-2024-0155", period=MP_PERIOD, job_title=row["job_title"],
                nationality=row["nationality"], employee_count=row["employee_count"],
                reg_hours=row["reg_hours"], reg_rate=row["reg_rate"], ot_hours=row["ot_hours"], ot_rate=row["ot_rate"],
            ))
            session.add(VendorInvoiceLine(
                contract_id="SC-2024-0155", period=MP_PERIOD, job_title=row["job_title"],
                nationality=row["nationality"], invoiced_amount=row["invoiced"],
            ))

        for co in CHANGE_ORDERS:
            lines = co.pop("lines")
            session.add(ChangeOrder(**co))
            await session.flush()
            for line in lines:
                session.add(ChangeOrderLine(change_order_id=co["id"], **line))
        for step in CO_003_STEPS:
            session.add(ApprovalStep(owner_type="change_order", owner_id="CO-2026-003", **step))

        session.add(Penalty(**PENALTY))
        for step in PENALTY_STEPS:
            session.add(ApprovalStep(owner_type="penalty", owner_id="PN-2026-004", **step))

        for service_line, data in EVALUATIONS.items():
            evaluation = Evaluation(
                service_line=service_line, subcontractor=data["subcontractor"], project=data["project"],
                period=data["period"], evaluator=data["evaluator"],
                penalty_adj_pct=data["penalty_adj_pct"], incentive_adj_pct=data["incentive_adj_pct"],
            )
            session.add(evaluation)
            await session.flush()
            for cat, kpi, target_label, target_value, direction, weight, actual in data["kpis"]:
                session.add(EvaluationKpiRow(
                    evaluation_id=evaluation.id, category=cat, kpi=kpi, target_label=target_label,
                    target_value=target_value, direction=direction, weight=weight, actual=actual,
                ))

        for c in CONTRACTS:
            session.add(ActivityLogEntry(
                contract_id=c["id"], entity_type="contract", entity_id=c["id"], action="created",
                summary=f"Contract {c['id']} created for {c['vendor_name']} — {c['project_name']} ({c['service_type']}), value {money(c['contract_value'])}",
            ))
            if c["status"] != "Pending":
                session.add(ActivityLogEntry(
                    contract_id=c["id"], entity_type="contract", entity_id=c["id"], action="approved",
                    summary=f"Contract {c['id']} approved — Oracle PO {c['oracle_po']} ({c['oracle_po_rev']}) created for {c['vendor_name']}",
                ))
        session.add(ActivityLogEntry(
            contract_id=MANPOWER_CONTRACT["id"], entity_type="contract", entity_id=MANPOWER_CONTRACT["id"], action="created",
            summary=f"Manpower Supply contract {MANPOWER_CONTRACT['id']} created for {MANPOWER_CONTRACT['vendor_name']}, value {money(MANPOWER_CONTRACT['contract_value'])}",
        ))
        for ipc in SC_0142_IPCS:
            session.add(ActivityLogEntry(
                contract_id="SC-2024-0142", entity_type="ipc", entity_id=ipc["number"], action="created",
                summary=f"{ipc['number']} created for SC-2024-0142 — {ipc['period']}, {ipc['work_done_pct']}% complete, net payable {money(ipc['net_payable'])}",
            ))
        for co in CHANGE_ORDERS:
            session.add(ActivityLogEntry(
                contract_id=co["contract_id"], entity_type="change_order", entity_id=co["id"], action="created",
                summary=f"Change order {co['id']} raised for {co['contract_id']} — {co['reason']} (status: {co['status']})",
            ))
        session.add(ActivityLogEntry(
            contract_id=PENALTY["contract_id"], entity_type="penalty", entity_id=PENALTY["id"], action="raised",
            summary=f"Penalty {PENALTY['id']} raised against {PENALTY['contract_id']} — {PENALTY['reason']}, amount {money(PENALTY['amount'])}",
        ))

        await session.commit()

    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
