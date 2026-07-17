"""Create a deterministic portfolio and credit visual dashboard."""

from __future__ import annotations

import abaquant as aq
from _shared.deterministic_market_provider import DeterministicMarketDataProvider
from _shared.output import configure_example_visuals, print_mapping, reset_example_visuals
from _shared.sample_data import sample_returns


def build_dashboard_objects() -> tuple[aq.PortfolioAllocator, object, object]:
    """Create portfolio, ticker, and universe objects for the dashboard."""
    allocator = aq.PortfolioAllocator(sample_returns(), annual_risk_free_rate=0.02)
    provider = DeterministicMarketDataProvider()
    ticker = aq.get_ticker("DEMO", provider=provider, financial_cache="memory")
    universe = aq.get_tickers(["ALPHA", "BETA", "GAMMA"], provider=provider)
    return allocator, ticker, universe


def compute_dashboard_metrics(
    allocator: aq.PortfolioAllocator, ticker: object, universe: object
) -> dict[str, object]:
    """Compute numerical values shown by the dashboard."""
    allocation = allocator.mean_variance.maximum_sharpe()
    credit_assessment = ticker.credit.assess_from_financials()
    universe_portfolio = universe.portfolio.max_sharpe(period="1mo", risk_free_rate=0.02)
    return {
        "portfolio_alpha_weight": float(allocation[0]),
        "credit_proxy_score": credit_assessment.synthetic_credit_proxy_score,
        "credit_proxy_band": credit_assessment.synthetic_credit_proxy_band,
        "universe_sharpe_ratio": universe_portfolio.sharpe_ratio,
    }


def create_dashboard_figures(
    allocator: aq.PortfolioAllocator, ticker: object, universe: object
) -> dict[str, str]:
    """Save all dashboard charts to one deterministic output directory."""
    output_directory = configure_example_visuals(subdirectory="portfolio_credit_dashboard")
    allocation = allocator.mean_variance.maximum_sharpe()
    credit_assessment = ticker.credit.assess_from_financials()
    figures = {
        "allocation_weights": allocator.visualize(
            weights=allocation, chart="weights", filename="01_allocation_weights"
        ),
        "portfolio_path": allocator.visualize(
            weights=allocation, chart="cumulative_returns", filename="02_portfolio_path"
        ),
        "asset_correlation": allocator.visualize(
            chart="correlation", filename="03_asset_correlation"
        ),
        "ticker_history": ticker.visualize(period="1mo", filename="04_ticker_history"),
        "universe_history": universe.visualize(period="1mo", filename="05_universe_history"),
        "financial_statement": ticker.financials.visualize(
            statement="balance_sheet", filename="06_balance_sheet"
        ),
        "credit_metrics": credit_assessment.visualize(
            chart="metrics", filename="07_credit_metrics"
        ),
        "credit_score": credit_assessment.visualize(chart="score", filename="08_credit_score"),
    }
    reset_example_visuals()
    return {name: type(figure).__name__ for name, figure in figures.items()} | {
        "output_directory": str(output_directory)
    }


def run() -> None:
    """Run the portfolio-credit visual dashboard."""
    try:
        allocator, ticker, universe = build_dashboard_objects()
        print_mapping("Dashboard metrics", compute_dashboard_metrics(allocator, ticker, universe))
        print_mapping("Dashboard figures", create_dashboard_figures(allocator, ticker, universe))
    except aq.VisualizationError as exc:
        print(f"Visualization skipped: {exc}")


if __name__ == "__main__":
    run()
