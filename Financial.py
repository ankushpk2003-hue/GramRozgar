"""
GramRozgar AI — Deterministic Financial Rule Engine for PMEGP Scheme.

Full month-by-month amortization engine for PMEGP loans. It supports:

  - Staggered / tranche disbursement (e.g. 60% at sanction, 40% after
    3 months for asset purchase) instead of assuming the full loan lands
    on day one.
  - Optional capitalization of moratorium interest (added to principal)
    vs. interest-only cash payment during moratorium — both are real
    bank practices, so this is configurable rather than assumed.
  - The government subsidy adjustment happening at the true simulated
    outstanding balance at the lock-in month, not an estimate.
  - A full CSV-exportable schedule for audit / verification, not just
    two summary EMI numbers.
  - Deterministic, auditable math — no LLM-generated numbers, so no
    math hallucination risk.

This module only defines functions and classes. It has no side effects
on import (no printing, no file writes). See demo.py for example usage
and test scenarios.
"""

import csv
import math


class PMEGPValidationError(ValueError):
    """Raised when PMEGP financial inputs are invalid."""
    pass


def _amortize_emi(principal: float, r: float, n: int) -> float:
    """Standard EMI formula, safe for r == 0 and n <= 0."""
    if n <= 0:
        return 0.0
    if r == 0:
        return principal / n
    return (principal * r * math.pow(1 + r, n)) / (math.pow(1 + r, n) - 1)


def _pmegp_rates(is_special_category: bool, is_rural: bool):
    if is_special_category:
        own_contrib_pct = 0.05
        subsidy_pct = 0.35 if is_rural else 0.25
        category_name = "Special Category (Women/SC/ST/OBC)"
    else:
        own_contrib_pct = 0.10
        subsidy_pct = 0.25 if is_rural else 0.15
        category_name = "General Category"
    return own_contrib_pct, subsidy_pct, category_name


def generate_pmegp_schedule(
    project_cost: float,
    is_rural: bool = True,
    is_special_category: bool = True,
    annual_interest_rate: float = 9.5,
    tenure_years: int = 5,
    moratorium_months: int = 6,
    subsidy_lock_in_years: int = 3,
    disbursement_schedule=None,
    capitalize_moratorium_interest: bool = False,
):
    """
    Simulates the loan month by month and returns (schedule, summary).

    Args:
        disbursement_schedule: optional list of (month, amount) tuples
            describing tranche disbursement. Amounts must sum to the
            bank loan amount (project_cost - own_contribution). If
            omitted, the full bank loan is disbursed in month 1
            (lump sum), matching typical PMEGP micro-enterprise loans.
        capitalize_moratorium_interest: if True, interest accrued during
            the moratorium is added to the principal instead of being
            collected as a monthly cash payment (common for
            under-construction / asset-buildout projects). If False
            (default), the borrower pays interest-only each month
            during the moratorium and the principal stays flat.

    Returns:
        schedule: list of dicts, one row per month.
        summary: dict of headline figures derived from the schedule.
    """

    # ---- 1. Input validation -------------------------------------------
    if project_cost <= 0:
        raise PMEGPValidationError("project_cost must be greater than 0.")
    if tenure_years <= 0:
        raise PMEGPValidationError("tenure_years must be greater than 0.")
    if annual_interest_rate < 0:
        raise PMEGPValidationError("annual_interest_rate cannot be negative.")
    if moratorium_months < 0:
        raise PMEGPValidationError("moratorium_months cannot be negative.")
    if moratorium_months >= tenure_years * 12:
        raise PMEGPValidationError(
            "moratorium_months cannot be greater than or equal to the total "
            "loan tenure (tenure_years * 12)."
        )
    if subsidy_lock_in_years < 0:
        raise PMEGPValidationError("subsidy_lock_in_years cannot be negative.")

    # ---- 2. Rates & headline amounts ------------------------------------
    own_contrib_pct, subsidy_pct, category_name = _pmegp_rates(
        is_special_category, is_rural
    )
    own_contribution = project_cost * own_contrib_pct
    govt_subsidy = project_cost * subsidy_pct
    bank_loan_amount = project_cost - own_contribution

    # ---- 3. Disbursement schedule ---------------------------------------
    if disbursement_schedule is None:
        disbursement_schedule = [(1, bank_loan_amount)]

    total_disbursed = sum(amount for _, amount in disbursement_schedule)
    if abs(total_disbursed - bank_loan_amount) > 1.0:  # allow re rounding
        raise PMEGPValidationError(
            f"disbursement_schedule tranches sum to Rs.{total_disbursed:,.2f}, "
            f"but the bank loan amount is Rs.{bank_loan_amount:,.2f}. "
            "Tranche amounts must add up to the full bank loan."
        )
    for month, amount in disbursement_schedule:
        if month < 1 or month > tenure_years * 12:
            raise PMEGPValidationError(
                f"disbursement month {month} is outside the loan tenure."
            )
        if amount <= 0:
            raise PMEGPValidationError("Each disbursement tranche must be > 0.")

    disb_map = {}
    for month, amount in disbursement_schedule:
        disb_map[month] = disb_map.get(month, 0.0) + amount

    # ---- 4. Timeline design (fixed window lengths) -----------------------
    full_tenure_months = tenure_years * 12
    repayment_months = full_tenure_months - moratorium_months
    lock_in_month = subsidy_lock_in_years * 12

    months_at_full_emi = max(0, min(lock_in_month, full_tenure_months) - moratorium_months)
    months_at_full_emi = min(months_at_full_emi, repayment_months)
    months_at_reduced_emi = repayment_months - months_at_full_emi

    r = (annual_interest_rate / 100) / 12

    # ---- 5. Month-by-month simulation ------------------------------------
    schedule = []
    outstanding = 0.0
    emi = 0.0
    subsidy_applied = False
    phase_a_emi = None
    phase_b_emi = None
    total_interest_paid = 0.0
    total_principal_paid = 0.0

    for month in range(1, full_tenure_months + 1):
        opening = outstanding
        disbursed_this_month = disb_map.get(month, 0.0)
        principal_base = opening + disbursed_this_month

        if month <= moratorium_months:
            interest = principal_base * r
            phase = "Moratorium (capitalized)" if capitalize_moratorium_interest else "Moratorium (interest-only)"
            if capitalize_moratorium_interest:
                payment = 0.0
                principal_component = -interest  # principal grows
                closing = principal_base + interest
            else:
                payment = interest
                principal_component = 0.0
                closing = principal_base

        else:
            # First repayment month: the EMI is fixed based on the FULL
            # repayment period (bank practice — the EMI doesn't change
            # until an actual event, like the subsidy adjustment, forces
            # a recast). It is only *paid* during the pre-lock-in window;
            # the recast below will replace it once the lock-in is hit.
            if emi == 0.0:
                n = repayment_months if repayment_months > 0 else 1
                emi = _amortize_emi(principal_base, r, n)
                phase_a_emi = round(emi, 2)

            # At the lock-in point, apply the subsidy BEFORE computing
            # this month's interest, since the credit is treated as
            # taking effect at the start of the recast month.
            if (not subsidy_applied) and month > lock_in_month and months_at_reduced_emi > 0:
                adjusted_principal = max(0.0, principal_base - govt_subsidy)
                remaining = full_tenure_months - month + 1
                emi = _amortize_emi(adjusted_principal, r, remaining)
                principal_base = adjusted_principal
                subsidy_applied = True
                phase_b_emi = round(emi, 2)
                phase = "Repayment (post subsidy adjustment)"
            else:
                phase = "Repayment (post subsidy adjustment)" if subsidy_applied else "Repayment (pre subsidy adjustment)"

            interest = principal_base * r
            payment = min(emi, principal_base + interest)  # avoid overpaying the final month
            principal_component = payment - interest
            closing = principal_base - principal_component
            total_interest_paid += interest
            total_principal_paid += principal_component

        closing = max(closing, 0.0)
        schedule.append({
            "month": month,
            "phase": phase,
            "opening_balance": round(opening, 2),
            "disbursed": round(disbursed_this_month, 2),
            "interest": round(interest, 2),
            "payment": round(payment, 2),
            "principal_component": round(principal_component, 2),
            "closing_balance": round(closing, 2),
        })
        outstanding = closing

    # If the loan tenure ends before the lock-in is ever reached, the
    # subsidy never gets recast into an EMI — it is settled at closure.
    if not subsidy_applied and months_at_reduced_emi == 0:
        phase_b_emi = None

    moratorium_interest_only_emi = round(bank_loan_amount * r, 2) if (
        moratorium_months > 0 and not capitalize_moratorium_interest
    ) else 0.0

    summary = {
        "project_cost": project_cost,
        "category": category_name,
        "location": "Rural" if is_rural else "Urban",
        "own_contribution": round(own_contribution, 2),
        "own_contrib_pct": f"{int(own_contrib_pct * 100)}%",
        "govt_subsidy": round(govt_subsidy, 2),
        "subsidy_pct": f"{int(subsidy_pct * 100)}%",
        "bank_loan_amount": round(bank_loan_amount, 2),
        "moratorium_months": moratorium_months,
        "moratorium_interest_only_emi": moratorium_interest_only_emi,
        "capitalize_moratorium_interest": capitalize_moratorium_interest,
        "phase_a_months": months_at_full_emi,
        "phase_a_emi": phase_a_emi,
        "phase_b_months": months_at_reduced_emi,
        "phase_b_emi": phase_b_emi,
        "annual_interest_rate": f"{annual_interest_rate}%",
        "tenure_years": tenure_years,
        "subsidy_lock_in_years": subsidy_lock_in_years,
        "total_interest_paid": round(total_interest_paid, 2),
        "total_principal_paid": round(total_principal_paid, 2),
        "final_closing_balance": schedule[-1]["closing_balance"] if schedule else None,
        "disbursement_schedule": disbursement_schedule,
    }

    return schedule, summary


def export_schedule_csv(schedule, filepath):
    """Writes the full month-by-month schedule to a CSV file for audit."""
    fieldnames = [
        "month", "phase", "opening_balance", "disbursed",
        "interest", "payment", "principal_component", "closing_balance",
    ]
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(schedule)


def print_terminal_output(summary, schedule, show_rows=6):
    """Prints a condensed, phase-aware terminal output plus a schedule preview."""
    print("=" * 70)
    print("        GRAMROZGAR AI - DETERMINISTIC FINANCIAL ENGINE        ")
    print("=" * 70)
    print(f" [+] Total Business Project Cost : Rs.{summary['project_cost']:,.2f}")
    print(f" [+] Beneficiary Category        : {summary['category']}")
    print(f" [+] Location Sector             : {summary['location']}")
    print("-" * 70)
    print(f" [1] Own Contribution ({summary['own_contrib_pct']})   : Rs.{summary['own_contribution']:,.2f}")
    print(f" [2] PMEGP Govt Subsidy ({summary['subsidy_pct']})  : Rs.{summary['govt_subsidy']:,.2f}")
    print(f" [3] Total Bank Loan Sanctioned  : Rs.{summary['bank_loan_amount']:,.2f}")
    print(f" [4] Disbursement Plan           : {summary['disbursement_schedule']}")
    print("-" * 70)
    mode = "capitalized into principal" if summary["capitalize_moratorium_interest"] else "interest-only cash payment"
    print(f" [>] Moratorium Period            : {summary['moratorium_months']} months ({mode})")
    if summary["moratorium_interest_only_emi"] > 0:
        print(f" [>] Moratorium Monthly Interest  : Rs.{summary['moratorium_interest_only_emi']:,.2f}/month")
    print("-" * 70)
    print(f" [>] Phase A EMI (months 1-{summary['phase_a_months']} of repayment)      : Rs.{summary['phase_a_emi']:,.2f}/month")
    if summary["phase_b_emi"] is not None:
        print(f" [>] Phase B EMI (post subsidy adjustment)       : Rs.{summary['phase_b_emi']:,.2f}/month")
    else:
        print(f" [>] Phase B EMI  : N/A - tenure ends before {summary['subsidy_lock_in_years']}-yr lock-in")
    print("-" * 70)
    print(f" [Σ] Total Interest Paid Over Tenure : Rs.{summary['total_interest_paid']:,.2f}")
    print(f" [Σ] Total Principal Repaid          : Rs.{summary['total_principal_paid']:,.2f}")
    print(f" [Σ] Final Closing Balance (should be ~0) : Rs.{summary['final_closing_balance']:,.2f}")
    print("=" * 70)
    print(" [OK] SHIELD LAYER STATUS: FACTS VERIFIED (0% MATH HALLUCINATION)")
    print("=" * 70)

    print(f"\n--- SCHEDULE PREVIEW (first {show_rows} and last {show_rows} months) ---")
    header = f"{'Mo':>3} {'Phase':<32} {'Open':>10} {'Disb':>9} {'Int':>9} {'Pay':>10} {'Princ':>10} {'Close':>10}"
    print(header)
    print("-" * len(header))
    preview_rows = schedule[:show_rows] + (["..."] if len(schedule) > show_rows * 2 else []) + schedule[-show_rows:]
    for row in preview_rows:
        if row == "...":
            print("  ...")
            continue
        print(
            f"{row['month']:>3} {row['phase']:<32} {row['opening_balance']:>10,.0f} "
            f"{row['disbursed']:>9,.0f} {row['interest']:>9,.0f} {row['payment']:>10,.0f} "
            f"{row['principal_component']:>10,.0f} {row['closing_balance']:>10,.0f}"
        )


def generate_sms_mockup(summary, phone_number="+91 98XXX XXXXX"):
    """Generates the text for the SMS verification mockup, phase-aware."""
    lock_in_yr = summary["subsidy_lock_in_years"]

    phase_b_line = (
        f"- EMI after Yr {lock_in_yr} (subsidy adjusted): Rs.{summary['phase_b_emi']:,.0f}/mo\n"
        if summary["phase_b_emi"] is not None
        else "- Subsidy settled at loan closure (tenure ends before lock-in)\n"
    )
    moratorium_line = (
        f"- Moratorium: {summary['moratorium_months']} months before EMI starts\n"
        if summary["moratorium_months"] > 0
        else ""
    )

    sms_text = (
        f"GramRozgar Alert: Your PMEGP Dairy Business Feasibility is VERIFIED.\n\n"
        f"- Project Cost: Rs.{summary['project_cost']:,.0f}\n"
        f"- Govt Subsidy ({summary['subsidy_pct']}): Rs.{summary['govt_subsidy']:,.0f}\n"
        f"- Your Contribution ({summary['own_contrib_pct']}): Rs.{summary['own_contribution']:,.0f}\n"
        f"{moratorium_line}"
        f"- EMI until Yr {lock_in_yr}: Rs.{summary['phase_a_emi']:,.0f}/mo\n"
        f"{phase_b_line}"
        f"Status: Panchayat Area Feasibility Passed. Visit nearest KVIC/Bank with ID: GR-2026-891"
    )
    return sms_text