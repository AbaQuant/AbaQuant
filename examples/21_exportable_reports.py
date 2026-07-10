"""Create Markdown, HTML, and PDF reports from core AbaQuant objects."""

from __future__ import annotations

from pathlib import Path

from _shared.output import EXAMPLE_ROOT, print_mapping
from _shared.package_bootstrap import ensure_package_importable
from _shared.sample_data import sample_credit_input_values, sample_returns

ensure_package_importable()

from abaquant import RiskDashboard
from abaquant.credit import (
    BalanceSheetInputs,
    CashFlowInputs,
    CreditAnalysisInputs,
    CreditHistoricalSeries,
    IncomeStatementInputs,
    MarketEquityObservation,
    PriorPeriodInputs,
    calculate_credit_proxy_metrics,
)
from abaquant.derivatives.models import BlackScholesMertonModel
from abaquant.portfolio import PortfolioAllocator

REPORT_DIR = EXAMPLE_ROOT / "generated_reports"


def build_option_model() -> BlackScholesMertonModel:
    """Create a deterministic Black--Scholes--Merton option model."""
    return BlackScholesMertonModel(
        spot_price=100.0,
        strike_price=105.0,
        maturity_years=1.0,
        risk_free_rate=0.04,
        volatility=0.22,
        dividend_yield=0.01,
    )


def build_credit_assessment():
    """Create one deterministic credit-proxy assessment."""
    values = sample_credit_input_values()
    inputs = CreditAnalysisInputs(
        balance_sheet=BalanceSheetInputs(
            total_debt=values["total_debt"],
            total_equity=values["total_equity"],
            current_assets=values["current_assets"],
            inventory=values["inventory"],
            current_liabilities=values["current_liabilities"],
            cash_and_cash_equivalents=values["cash_and_cash_equivalents"],
            total_assets=values["total_assets"],
            total_liabilities=values["total_liabilities"],
            retained_earnings=values["retained_earnings"],
            long_term_debt=values["long_term_debt"],
        ),
        income_statement=IncomeStatementInputs(
            revenue=values["revenue"],
            gross_profit=values["gross_profit"],
            ebit=values["ebit"],
            ebitda=values["ebitda"],
            interest_expense=values["interest_expense"],
            net_income=values["net_income"],
        ),
        cash_flow_statement=CashFlowInputs(operating_cash_flow=values["operating_cash_flow"]),
        prior_period=PriorPeriodInputs(
            total_assets=values["previous_total_assets"],
            net_income=values["previous_net_income"],
            long_term_debt=values["previous_long_term_debt"],
            current_assets=values["previous_current_assets"],
            current_liabilities=values["previous_current_liabilities"],
            shares_outstanding=values["previous_shares_outstanding"],
            gross_profit=values["previous_gross_profit"],
            revenue=values["previous_revenue"],
        ),
        market_equity=MarketEquityObservation(market_value_equity=650.0),
        historical_series=CreditHistoricalSeries(
            earnings_history=(42.0, 47.0, 53.0, 60.0),
            leverage_history=(0.60, 0.54, 0.48, 0.42),
        ),
        reporting_currency="USD",
        reporting_period="FY2025",
    )
    return calculate_credit_proxy_metrics(inputs)


def build_portfolio_allocator() -> PortfolioAllocator:
    """Create a deterministic portfolio allocator for report examples."""
    return PortfolioAllocator(sample_returns(), annual_risk_free_rate=0.02)


def export_reports(output_directory: Path = REPORT_DIR) -> dict[str, str]:
    """Export representative reports and return the written file paths."""
    output_directory.mkdir(parents=True, exist_ok=True)
    option_model = build_option_model()
    credit_assessment = build_credit_assessment()
    allocator = build_portfolio_allocator()
    backtest = allocator.backtest(
        weights="inverse_volatility",
        rebalance="monthly",
        transaction_cost_bps=5.0,
        slippage_bps=1.0,
        benchmark="equal_weight",
        lookback=10,
    )
    dashboard = RiskDashboard(
        allocator,
        credit_assessments={"ALPHA": credit_assessment},
        weights=backtest.weights_history.iloc[-1],
        backtest=backtest,
    )
    reports = {
        "option_markdown": option_model.report(option_type="call").save(
            output_directory, "option_report", formats=("markdown",)
        )["markdown"],
        "option_html": option_model.report(option_type="call").save(
            output_directory, "option_report", formats=("html",)
        )["html"],
        "option_pdf": option_model.report(option_type="call").save(
            output_directory, "option_report", formats=("pdf",)
        )["pdf"],
        "portfolio_html": allocator.report().save(
            output_directory, "portfolio_report", formats=("html",)
        )["html"],
        "backtest_markdown": backtest.report().save(
            output_directory, "backtest_report", formats=("markdown",)
        )["markdown"],
        "credit_markdown": credit_assessment.report().save(
            output_directory, "credit_proxy_report", formats=("markdown",)
        )["markdown"],
        "risk_dashboard_html": dashboard.report().save(
            output_directory, "risk_dashboard_report", formats=("html",)
        )["html"],
    }
    return {name: str(path) for name, path in reports.items()}


def run() -> None:
    """Run the exportable-report example."""
    print_mapping("Exportable report files", export_reports())


if __name__ == "__main__":
    run()
