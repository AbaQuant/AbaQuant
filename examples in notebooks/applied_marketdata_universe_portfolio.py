"""Multi-ticker universe and portfolio workflow with an offline provider."""

from __future__ import annotations

from _shared.deterministic_market_provider import DeterministicMarketDataProvider
from _shared.output import configure_example_visuals, print_mapping, reset_example_visuals
from _shared.package_bootstrap import ensure_package_importable

ensure_package_importable()

from abaquant.marketdata import get_tickers
from abaquant.visualization import VisualizationError


def build_universe() -> object:
    """Create a deterministic three-asset universe."""
    return get_tickers(["ALPHA", "BETA", "GAMMA"], provider=DeterministicMarketDataProvider())


def compute_universe_workflow(universe: object) -> dict[str, object]:
    """Run price, return, statistic, and portfolio examples."""
    portfolio = universe.portfolio.max_sharpe(period="1mo", risk_free_rate=0.02)
    return {
        "symbols": universe.symbols,
        "price_shape": universe.history.prices(period="1mo").shape,
        "return_shape": universe.history.returns(period="1mo").shape,
        "statistics_rows": len(universe.statistics.summary(period="1mo")),
        "max_sharpe_alpha_weight": float(next(iter(portfolio.weights.values()))),
        "max_sharpe_ratio": portfolio.sharpe_ratio,
    }


def create_universe_figures(universe: object) -> dict[str, str]:
    """Create a universe price-history visualization."""
    output_directory = configure_example_visuals(subdirectory="universe_portfolio")
    figure = universe.visualize(period="1mo", filename="universe_price_history")
    reset_example_visuals()
    return {"universe_history": type(figure).__name__, "output_directory": str(output_directory)}


def run() -> None:
    """Run the universe-portfolio example."""
    universe = build_universe()
    print_mapping("Universe portfolio workflow", compute_universe_workflow(universe))
    try:
        print_mapping("Universe figures", create_universe_figures(universe))
    except VisualizationError as exc:
        print(f"Visualization skipped: {exc}")


if __name__ == "__main__":
    run()
