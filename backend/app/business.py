"""Shared computation rules - single source of truth for every derived value in the module.
See CLAUDE.md > Domain Model & Business Rules and ARCHITECTURE.md > 2.4 for the spec these implement.
"""

from decimal import ROUND_HALF_UP, Decimal

TYPE_COLORS = {
    "Hard FM (MEP)": ("#3a5bd9", "#eef1fd"),
    "Manpower": ("#2c7fb0", "#e7f1f8"),
    "Construction / JR": ("#7a5bd9", "#f0ecfb"),
    "Soft Services": ("#12805c", "#e6f4ee"),
}
STATUS_COLORS = {
    "Active": ("#12805c", "#e6f4ee"),
    "Expiring": ("#b45309", "#fbf1e3"),
    "Closing": ("#2c7fb0", "#e7f1f8"),
    "Draft": ("#667085", "#f0f1f4"),
    "Pending": ("#b45309", "#fbf1e3"),
}
RATING_BANDS = [
    (90, "Excellent", "#12805c", "#e6f4ee"),
    (80, "Good", "#177245", "#e9f5ee"),
    (70, "Acceptable", "#b45309", "#fbf1e3"),
    (60, "Poor", "#b54708", "#fbeee3"),
    (0, "Unsatisfactory", "#c0362c", "#fbeceb"),
]


def money(n: Decimal | float | int) -> str:
    d = Decimal(str(n)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return "SAR " + f"{int(d):,}"


def fmt_num(n: Decimal | float | int) -> str:
    d = Decimal(str(n)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return f"{int(d):,}"


def progress_color(pct: float) -> str:
    if pct >= 80:
        return "#12805c"
    if pct >= 40:
        return "#3a5bd9"
    return "#b45309"


def type_colors(service_type: str) -> tuple[str, str]:
    return TYPE_COLORS.get(service_type, ("#667085", "#f0f1f4"))


def status_colors(status: str) -> tuple[str, str]:
    return STATUS_COLORS.get(status, ("#667085", "#f0f1f4"))


def score_kpi(actual: float, target: float, direction: str) -> float:
    if direction == "zero":
        return 100.0 if actual == 0 else 0.0
    if direction == "lower":
        if actual <= target:
            return 100.0
        return max(0.0, min(1.0, target / actual) * 100)
    # higher-is-better
    if target == 0:
        return 100.0
    return min(1.0, actual / target) * 100


def rating_for(score: float) -> tuple[str, str, str]:
    """Returns (label, color, bg) for an overall evaluation score."""
    for threshold, label, color, bg in RATING_BANDS:
        if score >= threshold:
            return label, color, bg
    return RATING_BANDS[-1][1], RATING_BANDS[-1][2], RATING_BANDS[-1][3]


def manpower_variance(reg_hours: Decimal, reg_rate: Decimal, ot_hours: Decimal, ot_rate: Decimal, invoiced: Decimal):
    contract_amount = reg_hours * reg_rate + ot_hours * ot_rate
    variance = invoiced - contract_amount
    matched = abs(variance) < Decimal("100")
    return contract_amount, variance, matched


def co_value_impact(original_qty: Decimal, revised_qty: Decimal, contract_rate: Decimal) -> Decimal:
    return (revised_qty - original_qty) * contract_rate


def split_tags(stored: str) -> list[str]:
    return [t for t in stored.split("|") if t]


def join_tags(tags: list[str]) -> str:
    return "|".join(t.strip() for t in tags if t.strip())
