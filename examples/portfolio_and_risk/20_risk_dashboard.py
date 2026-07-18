"""Build an integrated portfolio and credit risk dashboard."""

from __future__ import annotations

import abaquant as aq
from examples._shared.output import configure_example_visuals, print_mapping, reset_example_visuals
from examples._shared.sample_data import sample_credit_input_values, sample_returns


def build_credit_assessment(debt_multiplier: float = 1.0):
    """Create one deterministic credit-proxy assessment for the dashboard."""
    values = sample_credit_input_values()
    inputs = aq.CreditAnalysisInputs(
        balance_sheet=aq.BalanceSheetInputs(
            total_debt=values["total_debt"] * debt_multiplier,
            total_equity=values["total_equity"],
            current_assets=values["current_assets"],
            inventory=values["inventory"],
            current_liabilities=values["current_liabilities"],
            cash_and_cash_equivalents=values["cash_and_cash_equivalents"],
            total_assets=values["total_assets"],
            total_liabilities=values["total_liabilities"],
            retained_earnings=values["retained_earnings"],
            long_term_debt=values["long_term_debt"] * debt_multiplier,
        ),
        income_statement=aq.IncomeStatementInputs(
            revenue=values["revenue"],
            gross_profit=values["gross_profit"],
            ebit=values["ebit"],
            ebitda=values["ebitda"],
            interest_expense=values["interest_expense"],
            net_income=values["net_income"],
        ),
        cash_flow_statement=aq.CashFlowInputs(operating_cash_flow=values["operating_cash_flow"]),
        prior_period=aq.PriorPeriodInputs(
            total_assets=values["previous_total_assets"],
            net_income=values["previous_net_income"],
            long_term_debt=values["previous_long_term_debt"],
            current_assets=values["previous_current_assets"],
            current_liabilities=values["previous_current_liabilities"],
            shares_outstanding=values["previous_shares_outstanding"],
            gross_profit=values["previous_gross_profit"],
            revenue=values["previous_revenue"],
        ),
        market_equity=aq.MarketEquityObservation(market_value_equity=650.0),
        historical_series=aq.CreditHistoricalSeries(
            earnings_history=(42.0, 47.0, 53.0, 60.0),
            leverage_history=(0.60, 0.54, 0.48, 0.42),
        ),
        reporting_currency="USD",
        reporting_period="FY2025",
    )
    return aq.calculate_credit_proxy_metrics(inputs)


def build_dashboard() -> aq.RiskDashboard:
    """Create one deterministic integrated risk dashboard."""
    allocator = aq.PortfolioAllocator(sample_returns(), annual_risk_free_rate=0.02)
    backtest = allocator.backtest(
        weights="inverse_volatility",
        rebalance="monthly",
        transaction_cost_bps=5.0,
        slippage_bps=1.0,
        benchmark="equal_weight",
        lookback=10,
    )
    return aq.RiskDashboard(
        allocator,
        credit_assessments={
            "ALPHA": build_credit_assessment(0.85),
            "BETA": build_credit_assessment(1.00),
            "GAMMA": build_credit_assessment(1.20),
        },
        weights=backtest.weights_history.iloc[-1],
        backtest=backtest,
    )


def compute_dashboard_outputs(dashboard: aq.RiskDashboard) -> dict[str, object]:
    """Return selected dashboard outputs for deterministic examples."""
    summary = dashboard.summary()
    risk_table = dashboard.risk_contribution()
    credit_table = dashboard.credit_scores()
    return {
        "portfolio_source": summary["portfolio"].get("source"),
        "portfolio_sharpe_ratio": summary["portfolio"].get("sharpe_ratio"),
        "largest_risk_contributor": summary["risk_contribution"].get("largest_risk_contributor"),
        "average_credit_score": summary["credit"].get("average_score"),
        "average_pairwise_correlation": summary["correlation"].get("average_pairwise_correlation"),
        "risk_contribution_rows": len(risk_table),
        "credit_score_rows": len(credit_table),
    }


def create_dashboard_figures(dashboard: aq.RiskDashboard) -> dict[str, str]:
    """Save the main dashboard charts to the deterministic example directory."""
    output_directory = configure_example_visuals(subdirectory="risk_dashboard")
    figures = {
        "risk_contribution": dashboard.visualize(
            chart="risk_contribution", filename="01_risk_contribution"
        ),
        "drawdown": dashboard.visualize(chart="drawdown", filename="02_drawdown"),
        "credit_scores": dashboard.visualize(chart="credit_scores", filename="03_credit_scores"),
        "correlation": dashboard.visualize(chart="correlation", filename="04_correlation"),
    }
    reset_example_visuals()
    return {name: type(figure).__name__ for name, figure in figures.items()} | {
        "output_directory": str(output_directory)
    }


def run() -> None:
    """Run the integrated risk-dashboard example."""
    dashboard = build_dashboard()
    print_mapping("Risk dashboard outputs", compute_dashboard_outputs(dashboard))
    try:
        print_mapping("Risk dashboard figures", create_dashboard_figures(dashboard))
    except aq.VisualizationError as exc:
        print(f"Visualization skipped: {exc}")


if __name__ == "__main__":
    run()
