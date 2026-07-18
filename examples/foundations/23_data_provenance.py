"""Show provider-neutral data provenance attached to AbaQuant results.

The example is fully deterministic and offline. It demonstrates the same
``.provenance`` pattern on derivative diagnostics, rate curves, portfolio
backtests, credit assessments, risk dashboards, and reports.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import abaquant as aq


def deterministic_returns() -> pd.DataFrame:
    """Return a small deterministic return panel for provenance examples."""
    index = pd.date_range("2026-01-01", periods=24, freq="D")
    step = np.arange(len(index), dtype=float)
    return pd.DataFrame(
        {
            "NVDA": 0.0010 + np.sin(step / 3.0) * 0.0015,
            "MSFT": 0.0007 + np.cos(step / 4.0) * 0.0010,
            "AAPL": 0.0008 + np.sin(step / 5.0) * 0.0009,
        },
        index=index,
    )


def deterministic_credit_assessment():
    """Return a deterministic manual credit-proxy assessment."""
    inputs = aq.CreditAnalysisInputs(
        balance_sheet=aq.BalanceSheetInputs(
            total_debt=120.0,
            total_equity=260.0,
            current_assets=190.0,
            inventory=30.0,
            current_liabilities=85.0,
            cash_and_cash_equivalents=45.0,
            total_assets=640.0,
            total_liabilities=300.0,
            retained_earnings=105.0,
            long_term_debt=100.0,
        ),
        income_statement=aq.IncomeStatementInputs(
            revenue=520.0,
            gross_profit=270.0,
            ebit=85.0,
            ebitda=100.0,
            interest_expense=10.0,
            net_income=60.0,
        ),
        cash_flow_statement=aq.CashFlowInputs(operating_cash_flow=82.0),
        reporting_currency="USD",
        reporting_period="FY2026",
    )
    return aq.calculate_credit_proxy_metrics(inputs)


def summarize_provenance(label: str, provenance) -> None:
    """Print a compact one-line provenance summary."""
    payload = provenance.as_dict()
    print(
        f"{label}: provider={payload['provider']}, dataset={payload['dataset']}, "
        f"reporting_date={payload['reporting_date']}, steps={len(payload['transformation_steps'])}"
    )


def run() -> dict[str, object]:
    """Run the deterministic data-provenance demonstration."""
    option = aq.BlackScholesMertonModel(100.0, 105.0, 1.0, 0.04, 0.22)
    diagnostics = option.diagnostics("call")
    curve = aq.RateCurve.from_rates({0.5: 0.04, 1.0: 0.045, 2.0: 0.05})

    allocator = aq.PortfolioAllocator(
        deterministic_returns(), annual_risk_free_rate=curve.zero_rate(1.0)
    )
    backtest = allocator.backtest(
        weights="equal_weight", rebalance="weekly", benchmark="equal_weight"
    )
    credit = deterministic_credit_assessment()
    dashboard = aq.RiskDashboard(
        allocator,
        credit_assessments={"NVDA": credit},
        weights={"NVDA": 1 / 3, "MSFT": 1 / 3, "AAPL": 1 / 3},
        backtest=backtest,
    )
    report = dashboard.report()

    summarize_provenance("option diagnostics", diagnostics.provenance)
    summarize_provenance("manual rate curve", curve.provenance)
    summarize_provenance("portfolio inputs", allocator.context.provenance)
    summarize_provenance("backtest", backtest.provenance)
    summarize_provenance("credit assessment", credit.provenance)
    summarize_provenance("risk dashboard", dashboard.provenance)
    summarize_provenance("dashboard report", report.provenance)

    return {
        "option_diagnostics": diagnostics.provenance.as_dict(),
        "rate_curve": curve.provenance.as_dict(),
        "portfolio_inputs": allocator.context.provenance.as_dict(),
        "backtest": backtest.provenance.as_dict(),
        "credit": credit.provenance.as_dict(),
        "dashboard": dashboard.provenance.as_dict(),
        "report": report.provenance.as_dict(),
    }


if __name__ == "__main__":
    run()
