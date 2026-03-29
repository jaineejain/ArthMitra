import math
from datetime import datetime

from scipy.optimize import brentq


# ----------------------------
# Helpers (paise-based)
# ----------------------------


def _clamp(n: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, n))


def _int_round(n: float) -> int:
    return int(round(n))


def _safe_div(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return a / b


def _band_for_total(total: int) -> str:
    # Aligned with frontend ring colors: <50 red, <70 amber, >=70 green.
    if total < 50:
        return "critical"
    if total < 70:
        return "poor"
    if total < 85:
        return "fair"
    return "good"


def _pct_strict(value: float) -> int:
    # Avoid weird float behavior around boundaries.
    return int(round(_clamp(value, 0.0, 100.0)))


def _paise_from_rupees(value: float | int) -> int:
    return int(round(float(value) * 100.0))


# ----------------------------
# MHS (Money Health Score)
# ----------------------------


def calculate_mhs(profile: dict) -> dict:
    """
    Input amounts are expected in paise (integers).
    Example values (rough rupees -> paise):
      - emergency_fund: 2000000 (rupees 20,000)
      - monthly_income: 85000*100
    """

    age = int(profile.get("age") or 0)
    if age <= 0:
        age = 30

    monthly_income = int(profile.get("monthly_income") or 0)
    monthly_expenses = int(profile.get("monthly_expenses") or 0)
    monthly_emi = int(profile.get("monthly_emi") or 0)
    emergency_fund = int(profile.get("emergency_fund") or 0)

    term_cover = int(profile.get("term_cover") or 0)
    health_cover = int(profile.get("health_cover") or 0)
    cc_outstanding = int(profile.get("cc_outstanding") or 0)

    equity_pct = float(profile.get("equity_pct") or 0.7)
    invested_80c = int(profile.get("invested_80c") or 0)
    has_nps = bool(profile.get("has_nps") or False)

    total_investments = int(profile.get("total_investments") or 0)
    monthly_sip = int(profile.get("monthly_sip") or 0)

    # Emergency score (0-100) — months covered vs (expenses + EMIs), target 6 months (Arth protocol)
    monthly_outflow = monthly_expenses + monthly_emi
    if monthly_outflow <= 0:
        ef_months = 0.0
    else:
        ef_months = _safe_div(emergency_fund, monthly_outflow)
    required_months = 6.0
    emergency_score = min(100.0, _safe_div(ef_months, required_months) * 100.0)

    # Insurance score (0-100)
    term_needed = monthly_income * 12 * 15
    term_score = 0.0 if term_needed == 0 else min(50.0, (term_cover / term_needed) * 50.0)
    health_score = min(30.0, (health_cover / (500000 * 100.0)) * 30.0)
    pa_score = 20.0
    insurance_score = term_score + health_score + pa_score

    # Debt score (0-100)
    foir = 0.0 if monthly_income == 0 else (monthly_emi / monthly_income)
    if foir < 0.30:
        debt_score = 100.0
    elif foir < 0.40:
        debt_score = 80.0
    elif foir < 0.50:
        debt_score = 60.0
    else:
        debt_score = max(0.0, 100.0 - foir * 200.0)
    if cc_outstanding > 0:
        debt_score = max(0.0, debt_score - 30.0)

    # Investment diversification score (0-100)
    ideal_equity = (100.0 - float(age)) / 100.0
    deviation = abs(equity_pct - ideal_equity)
    investment_score = max(0.0, 100.0 - deviation * 200.0)

    # Tax efficiency score (0-100)
    invested_cap = min(invested_80c, 150000 * 100)
    if invested_cap <= 0:
        invested_80c_score = 0.0
    else:
        invested_80c_score = (invested_cap / (150000 * 100.0)) * 40.0

    nps_score = 20.0 if has_nps else 0.0
    hra_score = 20.0  # default if we don't know HRA details
    regime_score = 20.0
    tax_score = invested_80c_score + nps_score + hra_score + regime_score

    # Retirement readiness (0-100)
    years_left = max(60 - int(age), 1)
    corpus_needed = monthly_expenses * 12 * 25
    if corpus_needed <= 0:
        retirement_score = 0.0
    else:
        projected = (
            total_investments * (1.11**years_left)
            + monthly_sip * 12 * ((1.11**years_left - 1.0) / 0.11)
        )
        retirement_score = min(100.0, (projected / corpus_needed) * 100.0)

    dimensions = {
        "emergency": _pct_strict(emergency_score),
        "insurance": _pct_strict(insurance_score),
        "debt": _pct_strict(debt_score),
        "investment": _pct_strict(investment_score),
        "tax": _pct_strict(tax_score),
        "retirement": _pct_strict(retirement_score),
    }

    weights = {
        "emergency": 0.20,
        "insurance": 0.25,
        "debt": 0.15,
        "investment": 0.20,
        "tax": 0.10,
        "retirement": 0.10,
    }

    total_score = 0.0
    for k, w in weights.items():
        total_score += dimensions[k] * w

    total = _int_round(total_score)

    weakest = min(dimensions.items(), key=lambda kv: kv[1])[0]
    return {
        "total": int(total),
        "dimensions": {k: int(v) for k, v in dimensions.items()},
        "weakest": weakest,
        "band": _band_for_total(int(total)),
    }


# ----------------------------
# FIRE
# ----------------------------


def calculate_fire(profile: dict) -> dict:
    age = int(profile.get("age") or 0)
    if age <= 0:
        age = 30
    target_retirement_age = int(profile.get("target_retirement_age") or 60)
    years = max(target_retirement_age - age, 1)

    inflation = 0.065
    swr = 0.035
    equity_return = 0.11

    monthly_income = int(profile.get("monthly_income") or 0)
    monthly_expenses = int(profile.get("monthly_expenses") or 0)
    total_investments = int(profile.get("total_investments") or 0)
    monthly_sip = int(profile.get("monthly_sip") or 0)
    monthly_emi = int(profile.get("monthly_emi") or 0)

    future_expenses = monthly_expenses * ((1.0 + inflation) ** years)
    fire_corpus = (future_expenses * 12.0) / swr

    future_current = total_investments * ((1.0 + equity_return) ** years)
    gap = max(0.0, fire_corpus - future_current)

    r = equity_return
    n = years * 12
    sip_needed = 0.0
    if gap > 0:
        rate_m = r / 12.0
        denom = (1.0 + rate_m) ** n - 1.0
        if denom > 0:
            sip_needed = gap * rate_m / denom

    current_sip = monthly_sip
    sip_gap = max(0.0, sip_needed - float(current_sip))

    available_to_invest = monthly_income - monthly_expenses - monthly_emi
    achievable = available_to_invest >= int(round(sip_needed)) and sip_needed > 0

    # 5-year milestones for charts
    points = []
    steps = [1, 2, 3, 4, 5]
    for i in steps:
        y = min(years, i * 5)  # up to 25 years of preview, clamp to target
        future_need = monthly_expenses * ((1.0 + inflation) ** y) * 12.0 / swr
        current_val = total_investments * ((1.0 + equity_return) ** y) + (
            monthly_sip * 12.0 * ((1.0 + equity_return) ** y - 1.0) / equity_return if equity_return > 0 else 0.0
        )
        points.append(
            {
                "year": y,
                "current": int(round(current_val)),
                "required": int(round(future_need)),
            }
        )

    monthly_expenses_at_retirement = int(round(future_expenses))

    # If we used clamped y for milestones, expose normalized x-axis years 0..?
    chart_data = []
    for idx, p in enumerate(points):
        chart_data.append(
            {
                "t": idx * 5,
                "current": p["current"],
                "required": p["required"],
            }
        )

    return {
        "fire_corpus": int(round(fire_corpus)),
        "sip_needed": int(round(sip_needed)),
        "current_sip": int(current_sip),
        "sip_gap": int(round(sip_gap)),
        "available_to_invest": int(available_to_invest),
        "achievable": bool(achievable),
        "years": years,
        "monthly_expenses_at_retirement": monthly_expenses_at_retirement,
        "chart_data": chart_data,
        "milestones": points,
    }


# ----------------------------
# LOAN (EMI + interest remaining)
# ----------------------------


def calculate_loan(profile: dict) -> dict:
    """
    Personal loan / reducing-balance EMI calculator.

    Inputs expected in `profile`:
      - outstanding_principal: PAISA (int)
      - annual_interest_rate: percent (float, e.g. 18.0)
      - months_remaining: int
      - prepayment_penalty_percent: percent (float, e.g. 2.0) — assumed if not known
    Output values are in PAISA (int) so chat narration can convert to rupees consistently.
    """
    P = int(profile.get("outstanding_principal") or 0)  # paise
    annual_rate = float(profile.get("annual_interest_rate") or 0.0)
    n = int(profile.get("months_remaining") or 0)
    penalty_pct = float(profile.get("prepayment_penalty_percent") or 0.0)

    if P <= 0 or n <= 0:
        return {
            "outstanding_principal": P,
            "annual_interest_rate": annual_rate,
            "months_remaining": n,
            "emi_monthly": 0,
            "total_outflow": 0,
            "interest_remaining": 0,
            "assumed_prepayment_penalty_percent_used": penalty_pct,
            "assumed_prepayment_penalty_cost": 0,
            "net_saving_assuming_penalty": 0,
        }

    r_m = (annual_rate / 100.0) / 12.0
    if r_m <= 0:
        emi = P / n
    else:
        num = P * r_m * ((1.0 + r_m) ** n)
        den = ((1.0 + r_m) ** n) - 1.0
        emi = num / den if den != 0 else 0.0

    total_outflow = emi * n
    interest_remaining = total_outflow - P

    penalty_cost = (P * penalty_pct) / 100.0 if penalty_pct > 0 else 0.0
    net_saving = interest_remaining - penalty_cost

    return {
        "outstanding_principal": int(round(P)),
        "annual_interest_rate": annual_rate,
        "months_remaining": n,
        "emi_monthly": int(round(emi)),
        "total_outflow": int(round(total_outflow)),
        "interest_remaining": int(round(interest_remaining)),
        "assumed_prepayment_penalty_percent_used": penalty_pct,
        "assumed_prepayment_penalty_cost": int(round(penalty_cost)),
        "net_saving_assuming_penalty": int(round(net_saving)),
    }


# ----------------------------
# TAX
# ----------------------------


def _apply_new_slabs(taxable: int) -> int:
    # FY2024-25 new regime
    # 0-3L:0, 3-7:5%, 7-10:10%, 10-12:15%, 12-15:20%, 15+:30%
    slabs = [
        (0, 300000 * 100, 0.0),
        (300000 * 100, 700000 * 100, 0.05),
        (700000 * 100, 1000000 * 100, 0.10),
        (1000000 * 100, 1200000 * 100, 0.15),
        (1200000 * 100, 1500000 * 100, 0.20),
        (1500000 * 100, None, 0.30),
    ]
    tax = 0.0
    for start, end, rate in slabs:
        if taxable <= start:
            break
        effective_end = taxable if end is None else min(taxable, end)
        amount = max(0, effective_end - start)
        tax += amount * rate
    return int(round(tax))


def _apply_old_slabs(taxable: int) -> int:
    # Old regime
    # 0-2.5L:0, 2.5-5:5%, 5-10:20%, 10+:30%
    slabs = [
        (0, 250000 * 100, 0.0),
        (250000 * 100, 500000 * 100, 0.05),
        (500000 * 100, 1000000 * 100, 0.20),
        (1000000 * 100, None, 0.30),
    ]
    tax = 0.0
    for start, end, rate in slabs:
        if taxable <= start:
            break
        effective_end = taxable if end is None else min(taxable, end)
        amount = max(0, effective_end - start)
        tax += amount * rate
    return int(round(tax))


def _marginal_rate_new(taxable: int) -> float:
    if taxable <= 300000 * 100:
        return 0.0
    if taxable <= 700000 * 100:
        return 0.05
    if taxable <= 1000000 * 100:
        return 0.10
    if taxable <= 1200000 * 100:
        return 0.15
    if taxable <= 1500000 * 100:
        return 0.20
    return 0.30


def _marginal_rate_old(taxable: int) -> float:
    if taxable <= 250000 * 100:
        return 0.0
    if taxable <= 500000 * 100:
        return 0.05
    if taxable <= 1000000 * 100:
        return 0.20
    return 0.30


def calculate_tax(profile: dict) -> dict:
    annual_gross = int(profile.get("annual_gross") or 0)
    hra_received = int(profile.get("hra_received") or 0)
    basic = int(profile.get("basic_salary") or 0)
    rent_paid = int(profile.get("rent_paid") or 0)
    is_metro = bool(profile.get("city_type") == "metro" or profile.get("is_metro") is True)
    used_80c = int(profile.get("used_80c") or 0)
    health_premium = int(profile.get("health_premium") or 0)
    nps_tier1 = int(profile.get("nps_tier1") or 0)

    std_deduction_new = 75000 * 100
    std_deduction_old = 50000 * 100

    # calc_hra_exempt
    hra_exempt = 0
    hra_exempt = min(
        hra_received,
        max(0, rent_paid - int(0.1 * basic)),
        int((0.5 if is_metro else 0.4) * basic),
    )
    hra_exempt = max(0, hra_exempt)

    old_deductions = (
        std_deduction_old
        + hra_exempt
        + min(used_80c, 150000 * 100)
        + min(health_premium, 25000 * 100)
        + min(nps_tier1, 50000 * 100)
    )
    old_taxable = max(0, annual_gross - old_deductions)
    old_tax_base = _apply_old_slabs(old_taxable)
    old_tax = int(round(old_tax_base * 1.04))

    new_taxable = max(0, annual_gross - std_deduction_new)
    new_tax_base = _apply_new_slabs(new_taxable)
    new_tax = int(round(new_tax_base * 1.04))

    recommended = "old" if old_tax < new_tax else "new"
    savings = abs(old_tax - new_tax)

    # Missed deductions (potential + saving) in paise
    missed_deductions = []

    nps_gap = max(0, 50000 * 100 - nps_tier1)
    if nps_gap > 0:
        missed_deductions.append(
            {
                "name": "NPS 80CCD(1B)",
                "potential": nps_gap,
                "saving": int(round(nps_gap * 0.30)),
            }
        )

    if used_80c < 150000 * 100:
        potential = 150000 * 100 - used_80c
        marginal = _marginal_rate_old(old_taxable) if recommended == "old" else _marginal_rate_new(new_taxable)
        missed_deductions.append(
            {
                "name": "80C gap",
                "potential": potential,
                "saving": int(round(potential * marginal)),
            }
        )

    missed_deductions.append(
        {
            "name": "Health insurance parents 80D",
            "potential": 50000 * 100,
            "saving": 15000 * 100,
        }
    )

    return {
        "old_tax": int(old_tax),
        "new_tax": int(new_tax),
        "recommended": recommended,
        "savings": int(savings),
        "old_taxable": int(old_taxable),
        "new_taxable": int(new_taxable),
        "missed_deductions": missed_deductions,
        "hra_exempt": int(hra_exempt),
        "used_80c": int(min(used_80c, 150000 * 100)),
    }


# ----------------------------
# XIRR
# ----------------------------


def xirr(cashflows: list, dates: list) -> float:
    """
    cashflows: list of amounts in any currency units (paise ints ok)
               negative = investments, positive = redemptions/current
    dates: list of ISO date strings or datetime objects, same length as cashflows
    Returns: annualized rate (e.g., 0.142 = 14.2%)
    """

    if not cashflows or len(cashflows) != len(dates) or len(cashflows) < 2:
        return 0.0

    parsed_dates = []
    for d in dates:
        if isinstance(d, datetime):
            parsed_dates.append(d)
        else:
            parsed_dates.append(datetime.fromisoformat(str(d)))

    t0 = parsed_dates[0]
    times = [(d - t0).days / 365.0 for d in parsed_dates]

    def npv(rate: float) -> float:
        total = 0.0
        for cf, t in zip(cashflows, times):
            total += cf / ((1.0 + rate) ** t)
        return total

    # Find a bracket where NPV changes sign.
    lo = -0.9
    hi = 5.0
    try:
        flo = npv(lo)
        fhi = npv(hi)
        if flo == 0:
            return lo
        if fhi == 0:
            return hi
        if flo * fhi > 0:
            # Fall back: try a tighter bracket scan
            for mid in [-0.5, 0.0, 0.1, 0.2, 0.3, 0.5, 1.0, 2.0]:
                fm = npv(mid)
                if flo * fm <= 0:
                    hi = mid
                    fhi = fm
                    break
                if fm == 0:
                    return mid
            else:
                return 0.0

        root = brentq(npv, lo, hi, maxiter=200)
        return float(root)
    except Exception:
        return 0.0


# ----------------------------
# Couple optimization
# ----------------------------


def calculate_couple_optimization(partner1: dict, partner2: dict) -> dict:
    # Baseline: taxes under each partner's individually optimal regime.
    tax1 = calculate_tax(partner1)
    tax2 = calculate_tax(partner2)
    tax1_base = tax1["old_tax"] if tax1["recommended"] == "old" else tax1["new_tax"]
    tax2_base = tax2["old_tax"] if tax2["recommended"] == "old" else tax2["new_tax"]
    combined_old = tax1_base + tax2_base

    # HRA optimization: whichever partner is in a higher slab (higher marginal rate) claims rent.
    # We approximate "slab" by marginal rate under their recommended regime.
    p1_marg = _marginal_rate_old(tax1["old_taxable"]) if tax1["recommended"] == "old" else _marginal_rate_new(tax1["new_taxable"])
    p2_marg = _marginal_rate_old(tax2["old_taxable"]) if tax2["recommended"] == "old" else _marginal_rate_new(tax2["new_taxable"])

    p1_claims_hra = p1_marg >= p2_marg

    # SIP / 80C optimization: inverse to income so the lower earner gets more 80C for slab efficiency.
    # We allocate total used_80c between both partners (capped at 1.5L each) based on inverse annual_gross.
    used80c_total = int(partner1.get("used_80c") or 0) + int(partner2.get("used_80c") or 0)
    income1 = max(1, int(partner1.get("annual_gross") or 0))
    income2 = max(1, int(partner2.get("annual_gross") or 0))
    w1 = 1.0 / income1
    w2 = 1.0 / income2
    s = w1 + w2
    w1n = w1 / s
    w2n = w2 / s

    cap = 150000 * 100
    opt_used1 = min(int(round(used80c_total * w1n)), cap)
    opt_used2 = min(int(round(used80c_total * w2n)), cap)
    # If caps clipped, pour the remainder proportionally to remaining headroom.
    remainder = used80c_total - opt_used1 - opt_used2
    if remainder > 0:
        head1 = max(0, cap - opt_used1)
        head2 = max(0, cap - opt_used2)
        denom = head1 + head2
        if denom > 0:
            opt_used1 += int(round(remainder * (head1 / denom)))
            opt_used2 += int(round(remainder * (head2 / denom)))

    p1_opt = dict(partner1)
    p2_opt = dict(partner2)

    if p1_claims_hra:
        p2_opt["hra_received"] = 0
    else:
        p1_opt["hra_received"] = 0

    p1_opt["used_80c"] = opt_used1
    p2_opt["used_80c"] = opt_used2

    tax1_opt = calculate_tax(p1_opt)
    tax2_opt = calculate_tax(p2_opt)
    tax1_opt_final = tax1_opt["old_tax"] if tax1_opt["recommended"] == "old" else tax1_opt["new_tax"]
    tax2_opt_final = tax2_opt["old_tax"] if tax2_opt["recommended"] == "old" else tax2_opt["new_tax"]

    combined_optimized = tax1_opt_final + tax2_opt_final
    annual_saving = combined_old - combined_optimized

    hra_advice = (
        "Higher-slab earner should claim HRA to maximize exemption."
        if p1_claims_hra
        else "Higher-slab earner should claim HRA to maximize exemption."
    )

    sip_split_p1_pct = 0
    sip_split_p2_pct = 0
    if used80c_total > 0:
        sip_split_p1_pct = int(round((opt_used1 / used80c_total) * 100))
        sip_split_p2_pct = max(0, 100 - sip_split_p1_pct)

    return {
        "combined_old_tax": int(combined_old),
        "combined_optimized_tax": int(combined_optimized),
        "annual_saving": int(max(0, annual_saving)),
        "hra_advice": hra_advice,
        "sip_split_p1_pct": int(sip_split_p1_pct),
        "sip_split_p2_pct": int(sip_split_p2_pct),
    }


# ----------------------------
# Karma Score
# ----------------------------


def calculate_karma_score(profile: dict) -> dict:
    # Reuse MHS components for behavior mapping.
    mhs = calculate_mhs(profile)
    dims = mhs["dimensions"]
    weakest = mhs["weakest"]

    monthly_sip = int(profile.get("monthly_sip") or 0)
    monthly_income = int(profile.get("monthly_income") or 0)
    term_cover = int(profile.get("term_cover") or 0)
    monthly_expenses = int(profile.get("monthly_expenses") or 0)
    emergency_fund = int(profile.get("emergency_fund") or 0)

    # discipline: base 100 if SIP>0, plus small bonus if SIP>20% of income
    discipline = 0
    if monthly_sip > 0:
        discipline = 100
        if monthly_income > 0 and monthly_sip > 0.2 * monthly_income:
            discipline = 100

    growth = 0
    if monthly_income > 0:
        growth = min(100, (monthly_sip / monthly_income) * 500.0)
    growth = int(round(growth))

    # family_safety: term cover ratio score (scale to 0-100)
    age = int(profile.get("age") or 30)
    monthly_income_safe = max(1, monthly_income)
    term_needed = monthly_income_safe * 12 * 15
    family_safety = 0
    if term_needed > 0:
        family_safety = int(round(min(100.0, (term_cover / term_needed) * 100.0)))

    protection = int(dims["insurance"])
    debt_health = int(dims["debt"])

    weights = {
        "protection": 0.20,
        "discipline": 0.25,
        "growth": 0.20,
        "family_safety": 0.20,
        "debt_health": 0.15,
    }
    total_100 = (
        protection * weights["protection"]
        + discipline * weights["discipline"]
        + growth * weights["growth"]
        + family_safety * weights["family_safety"]
        + debt_health * weights["debt_health"]
    )
    total = int(round(total_100 * 10))  # 0-1000

    if total >= 900:
        percentile = "Top 1%"
    elif total >= 800:
        percentile = "Top 5%"
    elif total >= 700:
        percentile = "Top 10%"
    elif total >= 600:
        percentile = "Top 20%"
    else:
        percentile = "Top 30%"

    # Map weak dimension to karma narrative
    karma_weakest = weakest
    return {
        "total": int(max(0, min(1000, total))),
        "dimensions": {
            "protection": int(protection),
            "discipline": int(discipline),
            "growth": int(growth),
            "family_safety": int(family_safety),
            "debt_health": int(debt_health),
        },
        "weakest": karma_weakest,
        "percentile": percentile,
    }


# ----------------------------
# Notes / Test values
# ----------------------------
#
# Example profile (rupees shown, convert to paise):
# profile = {
#   "age": 28, "is_salaried": True, "monthly_income": _paise_from_rupees(85000),
#   "monthly_expenses": _paise_from_rupees(50000), "monthly_emi": _paise_from_rupees(8000),
#   "emergency_fund": _paise_from_rupees(300000),
#   "term_cover": 0, "health_cover": _paise_from_rupees(400000),
#   "cc_outstanding": 0, "equity_pct": 0.6, "invested_80c": _paise_from_rupees(92000),
#   "has_nps": True, "total_investments": _paise_from_rupees(600000),
#   "monthly_sip": _paise_from_rupees(20000)
# }
#
# calculate_mhs(profile)
#

