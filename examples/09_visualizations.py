"""Focused overview of every supported ``visualize()`` family."""

from __future__ import annotations

import pandas as pd

from _shared.deterministic_market_provider import DeterministicMarketDataProvider
from _shared.output import configure_example_visuals, print_mapping, reset_example_visuals
from _shared.package_bootstrap import ensure_package_importable

ensure_package_importable()

from abaquant.credit.fundamentals import (
    BalanceSheetInputs,
    CashFlowInputs,
    CreditAnalysisInputs,
    IncomeStatementInputs,
    calculate_credit_proxy_metrics,
)
from abaquant.derivatives import OptionStrategy
from abaquant.derivatives.models import BlackScholesMertonModel, CoxRossRubinsteinModel
from abaquant.marketdata import get_ticker, get_tickers
from abaquant.portfolio.optimization import PortfolioAllocator
from abaquant.visualization import VisualizationError


def build_option_figures() -> dict[str, object]:
    """Create option-model payoff, profile, and lattice figures."""
    model = BlackScholesMertonModel(100.0, 105.0, 1.0, 0.05, 0.20)
    lattice = CoxRossRubinsteinModel(100.0, 105.0, 1.0, 0.05, 0.20, number_of_steps=6)
    return {
        "call_payoff": model.visualize(
            chart="payoff", option_type="call", filename="overview_call_payoff"
        ),
        "put_profile": model.visualize(
            chart="price_profile", option_type="put", filename="overview_put_profile"
        ),
        "call_extrinsic": model.visualize(
            chart="extrinsic_value", option_type="call", filename="overview_call_extrinsic"
        ),
        "call_greeks": model.visualize(
            chart="greeks",
            option_type="call",
            greek_scale="standardized",
            filename="overview_call_greeks",
        ),
        "call_price_surface": model.visualize(
            chart="price_surface",
            option_type="call",
            grid_size=31,
            volatility_grid_size=15,
            filename="overview_call_price_surface",
        ),
        "call_vega_surface": model.visualize(
            chart="vega_surface",
            option_type="call",
            grid_size=31,
            volatility_grid_size=15,
            filename="overview_call_vega_surface",
        ),
        "put_lattice": lattice.visualize(
            chart="tree", option_type="put", filename="overview_put_lattice"
        ),
        "strategy_payoff": OptionStrategy.bull_call_spread(
            lower_strike=100.0,
            upper_strike=115.0,
            lower_premium=6.0,
            upper_premium=2.0,
        ).visualize(chart="payoff", filename="overview_strategy_payoff"),
    }


def build_portfolio_figures() -> dict[str, object]:
    """Create portfolio path, weights, and correlation figures."""
    returns = pd.DataFrame(
        {"ALPHA": [0.01, -0.02, 0.03, 0.02], "BETA": [0.005, 0.01, -0.005, 0.003]}
    )
    allocator = PortfolioAllocator(returns, annual_risk_free_rate=0.02)
    weights = allocator.mean_variance.equal_weight()
    return {
        "weights": allocator.visualize(
            weights=weights, chart="weights", filename="overview_weights"
        ),
        "cumulative_returns": allocator.visualize(
            weights=weights, chart="cumulative_returns", filename="overview_cumulative"
        ),
        "correlation": allocator.visualize(chart="correlation", filename="overview_correlation"),
    }


def build_credit_figures() -> dict[str, object]:
    """Create credit metrics and score figures."""
    inputs = CreditAnalysisInputs(
        balance_sheet=BalanceSheetInputs(
            total_debt=100.0, total_equity=200.0, current_assets=120.0, current_liabilities=60.0
        ),
        income_statement=IncomeStatementInputs(ebit=50.0, ebitda=60.0, interest_expense=5.0),
        cash_flow_statement=CashFlowInputs(operating_cash_flow=40.0),
    )
    assessment = calculate_credit_proxy_metrics(inputs)
    return {
        "credit_metrics": assessment.visualize(chart="metrics", filename="overview_credit_metrics"),
        "credit_score": assessment.visualize(chart="score", filename="overview_credit_score"),
    }


def build_marketdata_figures() -> dict[str, object]:
    """Create ticker, statement, and universe figures with an offline provider."""
    provider = DeterministicMarketDataProvider()
    ticker = get_ticker("DEMO", provider=provider, financial_cache="memory")
    universe = get_tickers(["ALPHA", "BETA", "GAMMA"], provider=provider)
    chain_analytics = ticker.options.analytics("2027-01-15")
    return {
        "ticker_history": ticker.visualize(period="1mo", filename="overview_ticker"),
        "financial_statement": ticker.financials.visualize(
            statement="balance_sheet", filename="overview_balance_sheet"
        ),
        "option_chain_iv_smile": chain_analytics.visualize(
            chart="iv_smile", option_type="call", filename="overview_option_chain_iv_smile"
        ),
        "option_chain_open_interest": chain_analytics.visualize(
            chart="open_interest_heatmap", option_type="put", filename="overview_option_chain_oi"
        ),
        "universe_history": universe.visualize(period="1mo", filename="overview_universe"),
    }


def run() -> None:
    """Build all overview figures and print their types."""
    try:
        output_directory = configure_example_visuals(subdirectory="visualization_overview")
        all_figures = {}
        for figure_group in (
            build_option_figures(),
            build_portfolio_figures(),
            build_credit_figures(),
            build_marketdata_figures(),
        ):
            all_figures.update(figure_group)
        reset_example_visuals()
        print_mapping(
            "Visualization overview",
            {name: type(fig).__name__ for name, fig in all_figures.items()}
            | {"output_directory": str(output_directory)},
        )
    except VisualizationError as exc:
        print(f"Visualization skipped: {exc}")


if __name__ == "__main__":
    run()
