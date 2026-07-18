"""Minimal manual credit-proxy example using grouped inputs."""

from __future__ import annotations

import abaquant as aq
from examples._shared.output import print_mapping


def build_manual_inputs() -> aq.CreditAnalysisInputs:
    """Declare the minimum accounting inputs needed for several proxy metrics."""
    return aq.CreditAnalysisInputs(
        balance_sheet=aq.BalanceSheetInputs(
            total_debt=120.0,
            total_equity=300.0,
            current_assets=250.0,
            current_liabilities=100.0,
            cash_and_cash_equivalents=50.0,
        ),
        income_statement=aq.IncomeStatementInputs(
            ebit=75.0,
            ebitda=90.0,
            interest_expense=10.0,
        ),
        cash_flow_statement=aq.CashFlowInputs(operating_cash_flow=70.0),
        reporting_currency="USD",
        reporting_period="FY2025",
    )


def run() -> None:
    """Assess manually supplied fundamentals."""
    assessment = aq.calculate_credit_proxy_metrics(build_manual_inputs())
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
