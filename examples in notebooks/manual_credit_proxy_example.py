"""Minimal manual credit-proxy example using grouped inputs."""

from __future__ import annotations

from _shared.output import print_mapping
from _shared.package_bootstrap import ensure_package_importable

ensure_package_importable()

from abaquant.credit.fundamentals import (
    BalanceSheetInputs,
    CashFlowInputs,
    CreditAnalysisInputs,
    IncomeStatementInputs,
    calculate_credit_proxy_metrics,
)


def build_manual_inputs() -> CreditAnalysisInputs:
    """Declare the minimum accounting inputs needed for several proxy metrics."""
    return CreditAnalysisInputs(
        balance_sheet=BalanceSheetInputs(
            total_debt=120.0,
            total_equity=300.0,
            current_assets=250.0,
            current_liabilities=100.0,
            cash_and_cash_equivalents=50.0,
        ),
        income_statement=IncomeStatementInputs(
            ebit=75.0,
            ebitda=90.0,
            interest_expense=10.0,
        ),
        cash_flow_statement=CashFlowInputs(operating_cash_flow=70.0),
        reporting_currency="USD",
        reporting_period="FY2025",
    )


def run() -> None:
    """Assess manually supplied fundamentals."""
    assessment = calculate_credit_proxy_metrics(build_manual_inputs())
    print_mapping(
        "Manual credit proxy",
        {
            "debt_to_equity": assessment.metrics["debt_to_equity"],
            "current_ratio": assessment.metrics["current_ratio"],
            "interest_coverage": assessment.metrics["interest_coverage"],
            "synthetic_score": assessment.synthetic_credit_proxy_score,
            "synthetic_band": assessment.synthetic_credit_proxy_band,
        },
    )


if __name__ == "__main__":
    run()
