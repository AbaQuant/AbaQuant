"""Gallery of supported domain-specific ``visualize()`` methods."""

from __future__ import annotations

import abaquant as aq
from examples._shared.deterministic_market_provider import DeterministicMarketDataProvider
from examples._shared.output import configure_example_visuals, print_mapping, reset_example_visuals
from examples._shared.sample_data import sample_returns


def build_option_gallery() -> dict[str, object]:
    """Return the option-model portion of the visualization gallery."""
    option = aq.BlackScholesMertonModel(100.0, 105.0, 1.0, 0.05, 0.20)
    lattice = aq.CoxRossRubinsteinModel(100.0, 105.0, 1.0, 0.05, 0.20, number_of_steps=6)
    sabr = aq.SABRVolatilityModel(100.0, 100.0, 1.0, 0.20, 0.5, -0.3, 0.4)
    return {
        "option_payoff": option.visualize(chart="payoff", filename="gallery_option_payoff"),
        "option_profile": option.visualize(
            chart="price_profile", filename="gallery_option_profile"
        ),
        "option_extrinsic": option.visualize(
            chart="extrinsic_value", filename="gallery_option_extrinsic"
        ),
        "option_greeks": option.visualize(
            chart="greeks", greek_scale="standardized", filename="gallery_option_greeks"
        ),
        "option_price_surface": option.visualize(
            chart="price_surface",
            grid_size=31,
            volatility_grid_size=15,
            filename="gallery_option_price_surface",
        ),
        "option_gamma_surface": option.visualize(
            chart="gamma_surface",
            grid_size=31,
            volatility_grid_size=15,
            filename="gallery_option_gamma_surface",
        ),
        "lattice_tree": lattice.visualize(chart="tree", filename="gallery_lattice_tree"),
        "sabr_smile": sabr.visualize(chart="volatility_smile", filename="gallery_sabr_smile"),
        "strategy_payoff": aq.OptionStrategy.bull_call_spread(
            lower_strike=100.0,
            upper_strike=115.0,
            lower_premium=6.0,
            upper_premium=2.0,
        ).visualize(chart="payoff", filename="gallery_strategy_payoff"),
        "strategy_components": aq.OptionStrategy.bull_call_spread(
            lower_strike=100.0,
            upper_strike=115.0,
            lower_premium=6.0,
            upper_premium=2.0,
        ).visualize(chart="components", filename="gallery_strategy_components"),
    }


def build_portfolio_gallery() -> dict[str, object]:
    """Return the portfolio portion of the visualization gallery."""
    allocator = aq.PortfolioAllocator(sample_returns(), annual_risk_free_rate=0.02)
    weights = allocator.mean_variance.maximum_sharpe()
    return {
        "portfolio_weights": allocator.visualize(
            weights=weights, chart="weights", filename="gallery_portfolio_weights"
        ),
        "portfolio_cumulative": allocator.visualize(
            weights=weights, chart="cumulative_returns", filename="gallery_portfolio_cumulative"
        ),
        "portfolio_correlation": allocator.visualize(
            chart="correlation", filename="gallery_portfolio_correlation"
        ),
    }


def build_market_gallery() -> dict[str, object]:
    """Return the market-data portion of the visualization gallery."""
    provider = DeterministicMarketDataProvider()
    ticker = aq.get_ticker("DEMO", provider=provider, financial_cache="memory")
    universe = aq.get_tickers(["ALPHA", "BETA", "GAMMA"], provider=provider)
    assessment = ticker.credit.assess_from_financials()
    chain_analytics = ticker.options.analytics("2027-01-15")
    return {
        "ticker_prices": ticker.visualize(period="1mo", filename="gallery_ticker_prices"),
        "universe_prices": universe.visualize(period="1mo", filename="gallery_universe_prices"),
        "statement": ticker.financials.visualize(
            statement="balance_sheet", filename="gallery_statement"
        ),
        "option_chain_iv_surface": chain_analytics.visualize(
            chart="iv_surface", option_type="call", filename="gallery_option_chain_iv_surface"
        ),
        "option_chain_rich_cheap": chain_analytics.visualize(
            chart="rich_cheap",
            option_type="call",
            risk_free_rate=0.04,
            filename="gallery_option_chain_rich_cheap",
        ),
        "credit_metrics": assessment.visualize(chart="metrics", filename="gallery_credit_metrics"),
        "credit_score": assessment.visualize(chart="score", filename="gallery_credit_score"),
    }


def run() -> None:
    """Create the complete visualization gallery."""
    try:
        output_directory = configure_example_visuals(subdirectory="visualize_method_gallery")
        figures = {}
        figures.update(build_option_gallery())
        figures.update(build_portfolio_gallery())
        figures.update(build_market_gallery())
        reset_example_visuals()
        print_mapping(
            "Visualize method gallery",
            {key: type(value).__name__ for key, value in figures.items()}
            | {"output_directory": str(output_directory)},
        )
    except aq.VisualizationError as exc:
        print(f"Visualization skipped: {exc}")


if __name__ == "__main__":
    run()
