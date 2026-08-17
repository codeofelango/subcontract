import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, JSON, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    vendor_name: Mapped[str] = mapped_column(String(120))
    contractor_no: Mapped[str] = mapped_column(String(30))
    contract_type: Mapped[str] = mapped_column(String(20))  # 'scope' | 'manpower'
    service_type: Mapped[str] = mapped_column(String(40))  # 'Hard FM (MEP)' | 'Manpower' | 'Construction / JR' | 'Soft Services'
    project_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    project_no: Mapped[str | None] = mapped_column(String(30), nullable=True)
    duration_months: Mapped[int] = mapped_column(default=12)

    contract_value: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    contract_budget: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    retention_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("10.00"))
    advance_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("10.00"))
    advance_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    payable_terms_days: Mapped[int] = mapped_column(default=45)

    source_pr: Mapped[str | None] = mapped_column(String(60), nullable=True)
    oracle_po: Mapped[str | None] = mapped_column(String(30), nullable=True)
    oracle_po_rev: Mapped[str | None] = mapped_column(String(20), nullable=True)

    location: Mapped[str | None] = mapped_column(String(80), nullable=True)  # site location shown on the invoice header
    ref_note: Mapped[str | None] = mapped_column(String(60), nullable=True)  # generic "Ref" field on the invoice header
    erp_ref: Mapped[str | None] = mapped_column(String(60), nullable=True)  # "ERP Ref" field on the invoice header
    vat_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("15.00"))
    # Second advance/down-payment tranche, tracked independently of advance_pct/advance_amount (tranche 1) -
    # mirrors the same pro-rata-to-progress recovery mechanism, just against a separate pool.
    advance2_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    advance2_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    # Letter of credit deduction - same mechanism again, defaults to 0/not applicable when unused.
    lc_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    lc_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))

    status: Mapped[str] = mapped_column(String(20), default="Pending")  # Draft|Pending|Active|Expiring|Closing|Rejected
    progress_pct: Mapped[int] = mapped_column(default=0)
    expiry_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    remaining_months: Mapped[int] = mapped_column(default=0)

    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("app_users.id"), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    line_items: Mapped[list["ContractLineItem"]] = relationship(back_populates="contract", cascade="all, delete-orphan")
    ipcs: Mapped[list["Ipc"]] = relationship(back_populates="contract", cascade="all, delete-orphan", order_by="Ipc.id")
    manpower_detail: Mapped["ManpowerContractDetail | None"] = relationship(
        back_populates="contract", cascade="all, delete-orphan", uselist=False
    )
    position_lines: Mapped[list["ManpowerPositionLine"]] = relationship(back_populates="contract", cascade="all, delete-orphan")


class ContractLineItem(Base):
    __tablename__ = "contract_line_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.id"))
    code: Mapped[str] = mapped_column(String(20))
    pr_line_ref: Mapped[str] = mapped_column(String(30))
    description: Mapped[str] = mapped_column(String(200))
    qty: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    uom: Mapped[str] = mapped_column(String(20))
    unit_rate: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    budget: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    sla_tags: Mapped[str] = mapped_column(String(200), default="")  # "|"-joined SLA tag labels for this line
    previous_qty: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)  # qty before the last approved change order
    revised_by_co: Mapped[str | None] = mapped_column(String(20), nullable=True)  # change order id that last revised this line's qty
    section: Mapped[str | None] = mapped_column(String(120), nullable=True)  # optional BOQ section/group header, e.g. "Runway Structural Pavement"

    contract: Mapped["Contract"] = relationship(back_populates="line_items")
    grn_receipts: Mapped[list["GrnLine"]] = relationship(back_populates="line_item", cascade="all, delete-orphan")


class GrnLine(Base):
    """A single Goods Receipt Note (GRN) event against one BOQ line - simulates the Oracle GRN
    feed confirming physical/service quantity actually received against the PO, independent of
    the vendor's self-declared work-done %. Used to compute a receipt-verified completion basis
    for the GRN Invoice report, and to flag variance against the vendor's claimed progress.
    """

    __tablename__ = "grn_lines"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.id"))
    line_item_id: Mapped[int] = mapped_column(ForeignKey("contract_line_items.id"))
    grn_number: Mapped[str] = mapped_column(String(30))
    qty_received: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    received_date: Mapped[datetime.date] = mapped_column(Date)

    line_item: Mapped["ContractLineItem"] = relationship(back_populates="grn_receipts")


class OraclePr(Base):
    """Simulated live feed of an approved Oracle Purchase Requisition, header level.

    Real Oracle PR/PO integration is out of scope for now (see CLAUDE.md) - this table stands in
    for it so the New Contract screen can pull BOQ/terms/SLA from the database instead of hardcoding them.
    """

    __tablename__ = "oracle_prs"

    id: Mapped[str] = mapped_column(String(30), primary_key=True)  # PR number, e.g. "PR-0530"
    vendor_name: Mapped[str] = mapped_column(String(120))
    contractor_no: Mapped[str] = mapped_column(String(30))
    contract_type: Mapped[str] = mapped_column(String(20))  # 'scope' | 'manpower'
    service_type: Mapped[str] = mapped_column(String(40))
    project_name: Mapped[str] = mapped_column(String(120))
    project_no: Mapped[str] = mapped_column(String(30))
    duration_months: Mapped[int] = mapped_column(default=12)
    contract_value: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    contract_budget: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    retention_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("10.00"))
    advance_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("10.00"))
    payable_terms_days: Mapped[int] = mapped_column(default=45)

    lines: Mapped[list["OraclePrLine"]] = relationship(back_populates="pr", cascade="all, delete-orphan", order_by="OraclePrLine.id")


class OraclePrLine(Base):
    """A BOQ line within an Oracle PR, including the SLA tags scoped to that line item."""

    __tablename__ = "oracle_pr_lines"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pr_id: Mapped[str] = mapped_column(ForeignKey("oracle_prs.id"))
    code: Mapped[str] = mapped_column(String(20))
    pr_line_ref: Mapped[str] = mapped_column(String(30))
    description: Mapped[str] = mapped_column(String(200))
    qty: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    uom: Mapped[str] = mapped_column(String(20))
    unit_rate: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    budget: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    sla_tags: Mapped[str] = mapped_column(String(200), default="")  # "|"-joined SLA tag labels

    pr: Mapped["OraclePr"] = relationship(back_populates="lines")


class PaymentTermOption(Base):
    """Oracle master list of allowed Payment Terms & Securities values, grouped by category.

    Populates the dropdowns on the New Contract screen so retention/advance/payable-terms
    choices are constrained to what Oracle allows, instead of free-typed numbers.
    """

    __tablename__ = "payment_term_options"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(20))  # 'retention_pct' | 'advance_pct' | 'payable_terms_days'
    value: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    label: Mapped[str] = mapped_column(String(30))
    sort_order: Mapped[int] = mapped_column(default=0)


class OracleContractor(Base):
    """Oracle vendor master - lets the New Contract screen offer a live list of contractors to pick from."""

    __tablename__ = "oracle_contractors"

    contractor_no: Mapped[str] = mapped_column(String(30), primary_key=True)
    vendor_name: Mapped[str] = mapped_column(String(120))


class OracleProject(Base):
    """Oracle project master - lets the New Contract screen offer a live list of projects to pick from."""

    __tablename__ = "oracle_projects"

    project_no: Mapped[str] = mapped_column(String(30), primary_key=True)
    project_name: Mapped[str] = mapped_column(String(120))


class ServiceTypeOption(Base):
    """Maintained list of contract/service types, selectable on the New Contract header."""

    __tablename__ = "service_type_options"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    label: Mapped[str] = mapped_column(String(60))
    contract_category: Mapped[str] = mapped_column(String(20))  # 'scope' | 'manpower' | 'both'
    sort_order: Mapped[int] = mapped_column(default=0)


class ManpowerContractDetail(Base):
    """One-to-one HR/contractor detail for a Manpower Supply contract (contract_type='manpower').

    Manpower Supply contracts are created without an Oracle PR (unlike Scope/Works contracts) -
    this table plus ManpowerPositionLine hold the fields that flow doesn't need Contract's
    PR/retention/advance columns for.
    """

    __tablename__ = "manpower_contract_details"

    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.id"), primary_key=True)
    issue_date: Mapped[datetime.date] = mapped_column(Date)
    expiry_terms: Mapped[str] = mapped_column(String(60))  # e.g. "Automatic renewal" or a fixed date label
    termination_notice: Mapped[str] = mapped_column(String(30))  # e.g. "60 Days"
    email_address: Mapped[str] = mapped_column(String(120))
    payment_terms_note: Mapped[str] = mapped_column(String(80))  # e.g. "5 days from issue invoice"
    account_number: Mapped[str] = mapped_column(String(40))

    contract: Mapped["Contract"] = relationship(back_populates="manpower_detail")


class ManpowerPositionLine(Base):
    """One rate-card row (per job-category position) on a Manpower Supply contract."""

    __tablename__ = "manpower_position_lines"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.id"))
    category_position: Mapped[str] = mapped_column(String(60))
    total_staff: Mapped[int] = mapped_column()
    working_hours: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    basic_salary: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    h_allowance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    t_allowance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    f_allowance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    share: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    total_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2))  # basic + H + T + F + share, per staff
    leave_treatment: Mapped[str] = mapped_column(String(20))  # "Deductible" | "Non-Deductible"
    absence_treatment: Mapped[str] = mapped_column(String(20))

    contract: Mapped["Contract"] = relationship(back_populates="position_lines")


class Ipc(Base):
    __tablename__ = "ipcs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.id"))
    number: Mapped[str] = mapped_column(String(20))
    period: Mapped[str] = mapped_column(String(20))
    work_done_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    gross: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    retention: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    advance_recovered: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    net_payable: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    status: Mapped[str] = mapped_column(String(20), default="Certifying")  # Certifying | Paid
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    invoice_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    period_from: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    period_to: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    # Discretionary charge entered at certification time - not derivable from any rate, unlike retention/advance.
    equipment_rental_deduction: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    # Whether this PM-approved invoice has been pushed to Oracle (AP invoice creation) yet, and
    # the confirmation code Oracle's API returns once it has - real integration not wired up, so
    # certify_vendor_submission() simulates the push the same way PO creation is simulated on
    # contract approval, immediately at PM-approval time.
    oracle_push_status: Mapped[str] = mapped_column(String(20), default="Not Pushed")  # "Not Pushed" | "Pushed"
    oracle_confirmation_code: Mapped[str | None] = mapped_column(String(40), nullable=True)

    contract: Mapped["Contract"] = relationship(back_populates="ipcs")


class VendorPortalSubmission(Base):
    """Simulated feed of the subcontractor's progress submission via the Oracle vendor portal.

    The vendor claims a work-done % and gross amount for a period; PMO certifies it here,
    which creates the actual IPC. Real Oracle vendor-portal integration is out of scope for
    now (see CLAUDE.md) - this table stands in for that feed.
    """

    __tablename__ = "vendor_portal_submissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.id"))
    period: Mapped[str] = mapped_column(String(20))
    work_done_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    gross_claimed: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    submitted_by: Mapped[str] = mapped_column(String(80))
    submitted_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[str] = mapped_column(String(20), default="Submitted")  # Submitted | Certified
    # Set at certify time to the GRN it was approved into - lets the Invoice Submission list show
    # the Oracle push confirmation without re-deriving it.
    ipc_id: Mapped[int | None] = mapped_column(ForeignKey("ipcs.id"), nullable=True)


class TimesheetLine(Base):
    """Simulated monthly HCM attendance feed, post salary-close."""

    __tablename__ = "timesheet_lines"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.id"))
    period: Mapped[str] = mapped_column(String(20))
    job_title: Mapped[str] = mapped_column(String(60))
    nationality: Mapped[str] = mapped_column(String(40), default="")
    employee_count: Mapped[int] = mapped_column(default=1)
    reg_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    reg_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    ot_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    ot_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2))


class VendorInvoiceLine(Base):
    """Simulated vendor invoice submitted for the same period/job title/nationality group."""

    __tablename__ = "vendor_invoice_lines"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.id"))
    period: Mapped[str] = mapped_column(String(20))
    job_title: Mapped[str] = mapped_column(String(60))
    nationality: Mapped[str] = mapped_column(String(40), default="")
    invoiced_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))


class ChangeOrder(Base):
    __tablename__ = "change_orders"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.id"))
    title: Mapped[str] = mapped_column(String(200))
    reason: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="In Approval")  # Draft|In Approval|Approved|Rejected
    po_revision_label: Mapped[str] = mapped_column(String(30), default="Rev pending")
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("app_users.id"), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lines: Mapped[list["ChangeOrderLine"]] = relationship(back_populates="change_order", cascade="all, delete-orphan")
    # Approval steps are NOT an ORM relationship (owner_id is a polymorphic key, not a real FK) -
    # fetch them explicitly with select(ApprovalStep).where(owner_type=..., owner_id=self.id) in routers.


class ChangeOrderLine(Base):
    __tablename__ = "change_order_lines"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    change_order_id: Mapped[str] = mapped_column(ForeignKey("change_orders.id"))
    code: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(String(200))
    original_qty: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    revised_qty: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    contract_rate: Mapped[Decimal] = mapped_column(Numeric(14, 2))

    change_order: Mapped["ChangeOrder"] = relationship(back_populates="lines")


class Penalty(Base):
    __tablename__ = "penalties"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.id"))
    reason: Mapped[str] = mapped_column(String(200))
    basis: Mapped[str] = mapped_column(String(120))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    status: Mapped[str] = mapped_column(String(20), default="In Approval")  # In Approval|Approved|Debited|Rejected
    attachment_ref: Mapped[str] = mapped_column(String(200))
    raised_by: Mapped[str] = mapped_column(String(80))
    raised_on: Mapped[datetime.date] = mapped_column(Date)
    sla_actual_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    sla_target_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    sla_breach_months: Mapped[int] = mapped_column(default=1)
    sla_label: Mapped[str] = mapped_column(String(80), default="SLA Score")


class ApprovalStep(Base):
    """Generic sequential approval step, shared by contracts, penalties, and change orders."""

    __tablename__ = "approval_steps"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_type: Mapped[str] = mapped_column(String(20))  # 'contract' | 'penalty' | 'change_order'
    owner_id: Mapped[str] = mapped_column(String(20))
    seq: Mapped[int] = mapped_column()
    role: Mapped[str] = mapped_column(String(80))
    approver_name: Mapped[str] = mapped_column(String(80))
    # Linked AppUser for the named approver, when one was assigned via the WorkflowStepTemplate
    # builder - lets /decide and /revise check "is this really your turn" instead of trusting
    # the free-text approver_name. Null for legacy hardcoded fallback chains.
    approver_user_id: Mapped[int | None] = mapped_column(ForeignKey("app_users.id", ondelete="SET NULL"), nullable=True)
    state: Mapped[str] = mapped_column(String(20), default="pending")  # done|current|pending|rejected|skipped
    decision: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 'approved' | 'rejected'
    acted_by_id: Mapped[int | None] = mapped_column(ForeignKey("app_users.id"), nullable=True)
    acted_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    meta_note: Mapped[str] = mapped_column(String(120), default="")


class ApprovalStepHistory(Base):
    """Append-only audit log of decision revisions on an ApprovalStep - written every time an
    approver changes an Approve/Reject decision they already made (see /revise endpoints).
    """

    __tablename__ = "approval_step_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    step_id: Mapped[int] = mapped_column(ForeignKey("approval_steps.id"))
    previous_decision: Mapped[str | None] = mapped_column(String(20), nullable=True)
    previous_state: Mapped[str] = mapped_column(String(20))
    new_decision: Mapped[str] = mapped_column(String(20))
    new_state: Mapped[str] = mapped_column(String(20))
    changed_by_id: Mapped[int] = mapped_column(ForeignKey("app_users.id"))
    changed_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reason: Mapped[str] = mapped_column(String(200), default="")


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    service_line: Mapped[str] = mapped_column(String(20))  # jr | soft | hard
    subcontractor: Mapped[str] = mapped_column(String(120))
    project: Mapped[str] = mapped_column(String(120))
    period: Mapped[str] = mapped_column(String(20))
    evaluator: Mapped[str] = mapped_column(String(80))
    penalty_adj_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    incentive_adj_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))

    kpi_rows: Mapped[list["EvaluationKpiRow"]] = relationship(back_populates="evaluation", cascade="all, delete-orphan")


class EvaluationKpiRow(Base):
    __tablename__ = "evaluation_kpi_rows"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    evaluation_id: Mapped[int] = mapped_column(ForeignKey("evaluations.id"))
    category: Mapped[str] = mapped_column(String(60))
    kpi: Mapped[str] = mapped_column(String(160))
    target_label: Mapped[str] = mapped_column(String(30))
    target_value: Mapped[Decimal] = mapped_column(Numeric(6, 4))
    direction: Mapped[str] = mapped_column(String(10))  # higher | lower | zero
    weight: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    actual: Mapped[Decimal] = mapped_column(Numeric(6, 4))

    evaluation: Mapped["Evaluation"] = relationship(back_populates="kpi_rows")


class AppUser(Base):
    """User directory - assignable as a named approver on a WorkflowStepTemplate, and (when
    `role` is set) a real Microsoft-SSO login identity with page/action access via that role.

    `email` is intentionally not unique - one person can hold multiple approver personas (e.g.
    the same person as both Procurement Director and CFO on different chains). Login resolves to
    the first active row for that email that has a non-null `role` - only one duplicate-email row
    should ever carry a role.
    """

    __tablename__ = "app_users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(120))
    department: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(60))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Fixed access role - 'admin' | 'procurement_requester' | 'hr_requester' | 'approver' - or
    # None if this row is a directory-only entry with no login rights.
    role: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # Marks this row as the one-click test login for its role's quick-login slot (admin |
    # requester | approver - see app/auth.py's quick_login_slot()). Only meaningful when `role`
    # is set; only one active row per slot should carry this at a time (enforced in
    # app/routers/users.py). Lets an admin move which real account backs each quick-login button
    # from the Users page instead of it being hardcoded.
    is_quick_login: Mapped[bool] = mapped_column(Boolean, default=False)


class WorkflowTemplate(Base):
    """A configured, visually-built approval flow for one entity type. Only one template per
    applies_to should have is_active=True at a time - that's the one consulted when a new
    Contract/ChangeOrder/Penalty is created (see app/workflow_engine.py).
    """

    __tablename__ = "workflow_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120))
    applies_to: Mapped[str] = mapped_column(String(30))  # 'contract_scope'|'contract_manpower'|'change_order'|'penalty'
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    canvas_nodes: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    canvas_edges: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    steps: Mapped[list["WorkflowStepTemplate"]] = relationship(
        back_populates="template", cascade="all, delete-orphan", order_by="WorkflowStepTemplate.seq"
    )


class WorkflowStepTemplate(Base):
    """Derived, ordered approval chain computed server-side from canvas_nodes/canvas_edges on
    save - this is what seed_approval_steps() reads to materialize real ApprovalStep rows.
    """

    __tablename__ = "workflow_step_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("workflow_templates.id"))
    seq: Mapped[int] = mapped_column()
    role: Mapped[str] = mapped_column(String(80))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("app_users.id", ondelete="SET NULL"), nullable=True)

    template: Mapped["WorkflowTemplate"] = relationship(back_populates="steps")


class Attachment(Base):
    """Uploaded supporting document. Uploaded before its owner exists (grouped by draft_token,
    generated client-side per form session) and "claimed" (owner_type/owner_id set, draft_token
    cleared) once the real record is created - see claim_attachments() in app/storage.py.

    owner_type is polymorphic, matching the existing ApprovalStep convention: 'contract' today,
    'penalty'/'change_order' are natural future additions once those have create screens.
    """

    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    draft_token: Mapped[str | None] = mapped_column(String(64), nullable=True)
    owner_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    owner_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column()
    storage_path: Mapped[str] = mapped_column(String(500))
    uploaded_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ActivityLogEntry(Base):
    """Audit trail of every action taken across the module - backs the Activity Assistant chat screen.

    No embeddings/vector search here (out of current scope, see CLAUDE.md); the assistant does simple
    keyword matching over `summary` plus recency ordering.
    """

    __tablename__ = "activity_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contract_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(30))  # contract | ipc | change_order | penalty | manpower
    entity_id: Mapped[str] = mapped_column(String(30))
    action: Mapped[str] = mapped_column(String(60))
    summary: Mapped[str] = mapped_column(String(300))
    actor: Mapped[str] = mapped_column(String(80), default="System")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
