"""
Demo / manual test runner for financial_engine.py.

Run this file directly (python3 demo.py) to see:
  - Scenario 1: standard lump-sum PMEGP loan, full terminal report + SMS mockup.
  - Scenario 2: staggered disbursement + capitalized moratorium interest.
  - A 0% interest rate check (should not crash).
  - Invalid-input checks (should raise clear errors, not crash or lie).

This file has no functions other people should import — it's a script,
not a module. The actual reusable logic lives in financial_engine.py.
"""

from financial_engine import (
    generate_pmegp_schedule,
    export_schedule_csv,
    print_terminal_output,
    generate_sms_mockup,
    PMEGPValidationError,
)


def run_scenario_1():
    print("#" * 70)
    print("# SCENARIO 1: Lump-sum disbursement (standard PMEGP micro-loan) #")
    print("#" * 70)
    schedule, summary = generate_pmegp_schedule(
        project_cost=500000,
        is_rural=True,
        is_special_category=True,
        annual_interest_rate=9.5,
        tenure_years=5,
        moratorium_months=6,
        subsidy_lock_in_years=3,
    )
    print_terminal_output(summary, schedule)
    print("\n--- INCOMING SMS MOCKUP CARD ---")
    print(generate_sms_mockup(summary))
    export_schedule_csv(schedule, "pmegp_schedule_scenario1.csv")
    print("\n[Saved full 60-month schedule to pmegp_schedule_scenario1.csv]")


def run_scenario_2():
    print("\n\n" + "#" * 70)
    print("# SCENARIO 2: Staggered disbursement (60% Month 1, 40% Month 4) #")
    print("#" * 70)
    schedule, summary = generate_pmegp_schedule(
        project_cost=500000,
        is_rural=True,
        is_special_category=True,
        annual_interest_rate=9.5,
        tenure_years=5,
        moratorium_months=6,
        subsidy_lock_in_years=3,
        disbursement_schedule=[(1, 475000 * 0.6), (4, 475000 * 0.4)],
        capitalize_moratorium_interest=True,
    )
    print_terminal_output(summary, schedule)
    export_schedule_csv(schedule, "pmegp_schedule_scenario2.csv")
    print("\n[Saved full 60-month schedule to pmegp_schedule_scenario2.csv]")


def run_zero_interest_check():
    print("\n\n--- TEST: 0% INTEREST RATE ---")
    _, summary = generate_pmegp_schedule(
        project_cost=200000,
        is_rural=True,
        is_special_category=False,
        annual_interest_rate=0,
        tenure_years=3,
        moratorium_months=6,
        subsidy_lock_in_years=3,
    )
    print(f" [OK] No crash. Phase A EMI at 0% interest: Rs.{summary['phase_a_emi']:,.2f}/month")


def run_invalid_input_checks():
    print("\n\n--- TEST: INVALID INPUT ---")
    try:
        generate_pmegp_schedule(project_cost=-50000)
    except PMEGPValidationError as e:
        print(f" [OK] Rejected cleanly: {e}")

    try:
        generate_pmegp_schedule(
            project_cost=500000,
            disbursement_schedule=[(1, 100000), (2, 100000)],  # doesn't sum to loan amount
        )
    except PMEGPValidationError as e:
        print(f" [OK] Rejected cleanly: {e}")


if __name__ == "__main__":
    run_scenario_1()
    run_scenario_2()
    run_zero_interest_check()
    run_invalid_input_checks()