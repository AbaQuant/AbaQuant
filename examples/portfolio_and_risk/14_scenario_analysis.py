"""Run first-class scenario analysis across derivatives, portfolios, and credit."""

from __future__ import annotations

import abaquant as aq
from examples._shared.output import configure_example_visuals, print_mapping, reset_example_visuals
from examples._shared.sample_data import sample_returns


def derivative_scenarios() -> object:
    """Build a spot--volatility scenario grid for a call option."""
    option_model = aq.BlackScholesMertonModel(
        spot_price=100.0,
        strike_price=105.0,
        maturity_years=1.0,
        risk_free_rate=0.05,
        volatility=0.22,
    )
    return option_model.scenario_grid(
        spot_prices=[80.0, 90.0, 100.0, 110.0, 120.0],
        volatilities=[0.15, 0.20, 0.25, 0.30],
        option_type="call",
    )


def portfolio_scenarios() -> object:
    """Build a one-period asset-shock scenario for a static allocation."""
    allocator = aq.PortfolioAllocator(sample_returns(), annual_risk_free_rate=0.02)
    weights = allocator.mean_variance.maximum_sharpe()
    return allocator.scenario_analysis(
        shocks={"ALPHA": -0.20, "BETA": -0.10, "GAMMA": -0.15},
        weights=weights,
        base_value=1_000_000.0,
    )


def credit_scenarios() -> object:
    """Build a debt and EBITDA multiplier grid for a credit-proxy assessment."""
    assessment = aq.calculate_credit_proxy_metrics(
        aq.CreditAnalysisInputs(
            balance_sheet=aq.BalanceSheetInputs(
                total_debt=120.0,
                total_equity=300.0,
                current_assets=180.0,
                inventory=20.0,
                current_liabilities=90.0,
                cash_and_cash_equivalents=35.0,
                total_assets=520.0,
                total_liabilities=220.0,
                retained_earnings=125.0,
                long_term_debt=105.0,
                shares_outstanding=100.0,
            ),
            income_statement=aq.IncomeStatementInputs(
                revenue=700.0,
                gross_profit=310.0,
                ebit=90.0,
                ebitda=115.0,
                interest_expense=9.0,
                net_income=62.0,
            ),
            cash_flow_statement=aq.CashFlowInputs(operating_cash_flow=78.0),
            prior_period=aq.PriorPeriodInputs(
                total_assets=500.0,
                net_income=55.0,
                long_term_debt=112.0,
                current_assets=170.0,
                current_liabilities=95.0,
                shares_outstanding=100.0,
                gross_profit=290.0,
                revenue=660.0,
            ),
            market_equity=aq.MarketEquityObservation(market_value_equity=950.0),
            historical_series=aq.CreditHistoricalSeries(
                earnings_history=(46.0, 51.0, 55.0, 62.0),
                leverage_history=(0.54, 0.48, 0.43, 0.40),
            ),
        )
    )
    return assessment.scenario_analysis(
        debt_multiplier=[1.0, 1.25, 1.50],
        ebitda_multiplier=[1.0, 0.75, 0.50],
    )


def summarize_scenarios(
    derivative_grid: object, portfolio_scenario: object, credit_grid: object
) -> dict[str, object]:
    """Return compact scalar highlights from the three scenario families."""
    derivative_high_price = derivative_grid.data["price"].max()
    derivative_low_delta = derivative_grid.data["delta"].min()
    credit_worst_score = credit_grid.data["synthetic_credit_proxy_score"].min()
    return {
        "derivative_highest_call_price": float(derivative_high_price),
        "derivative_lowest_delta": float(derivative_low_delta),
        "portfolio_scenario_return": portfolio_scenario.portfolio_return,
        "portfolio_ending_value": portfolio_scenario.ending_value,
        "credit_lowest_proxy_score": float(credit_worst_score),
    }


def create_scenario_figures(
    derivative_grid: object, portfolio_scenario: object, credit_grid: object
) -> dict[str, str]:
    """Save scenario charts for each domain into one output directory."""
    output_directory = configure_example_visuals(subdirectory="scenario_analysis")
    figures = {
        "derivative_price_surface": derivative_grid.visualize(
            metric="price", chart="surface", filename="01_derivative_price_surface"
        ),
        "derivative_delta_heatmap": derivative_grid.visualize(
            metric="delta", chart="heatmap", filename="02_derivative_delta_heatmap"
        ),
        "portfolio_contributions": portfolio_scenario.visualize(
            chart="contributions", filename="03_portfolio_contributions"
        ),
        "portfolio_shocks": portfolio_scenario.visualize(
            chart="shocks", filename="04_portfolio_shocks"
        ),
        "credit_score_heatmap": credit_grid.visualize(
            metric="synthetic_credit_proxy_score",
            chart="heatmap",
            filename="05_credit_score_heatmap",
        ),
        "credit_net_debt_curves": credit_grid.visualize(
            metric="net_debt_to_ebitda", chart="curves", filename="06_credit_net_debt_curves"
        ),
    }
    reset_example_visuals()
    return {name: type(figure).__name__ for name, figure in figures.items()} | {
        "output_directory": str(output_directory)
    }


def run() -> None:
    """Run derivative, portfolio, and credit scenario examples."""
    try:
        derivative_grid = derivative_scenarios()
        portfolio_scenario = portfolio_scenarios()
        credit_grid = credit_scenarios()
        print_mapping(
            "Scenario highlights",
            summarize_scenarios(derivative_grid, portfolio_scenario, credit_grid),
        )
        print_mapping(
            "Scenario figures",
            create_scenario_figures(derivative_grid, portfolio_scenario, credit_grid),
        )
    except aq.VisualizationError as exc:
        print(f"Visualization skipped: {exc}")


if __name__ == "__main__":
    run()
