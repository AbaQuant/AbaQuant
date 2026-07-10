"""Listed-option-chain analytics with deterministic offline data.

The example connects a normalized option chain to model analytics: implied-
volatility smiles, term structures, rich/cheap comparisons, and open-interest
heatmaps. It uses the deterministic example provider, so it does not require
Yahoo, yfinance, or network access.
"""

from __future__ import annotations

from _shared.deterministic_market_provider import DeterministicMarketDataProvider
from _shared.output import configure_example_visuals, print_mapping, reset_example_visuals
from _shared.package_bootstrap import ensure_package_importable

ensure_package_importable()

from abaquant.marketdata import get_ticker
from abaquant.visualization import VisualizationError


def build_option_chain_analytics() -> object:
    """Create a deterministic ticker and return one option-chain analytics object."""
    provider = DeterministicMarketDataProvider()
    ticker = get_ticker("DEMO", provider=provider, financial_cache="memory")
    return ticker.options.analytics(expiry="2027-01-15")


def inspect_chain_analytics(analytics: object) -> dict[str, object]:
    """Compute IV smile, skew, term structure, and rich/cheap summaries."""
    call_smile = analytics.iv_smile(option_type="call")
    put_skew = analytics.skew(option_type="put")
    term_structure = analytics.term_structure(
        option_type="call", strike=100.0, expiries=["2027-01-15", "2027-06-18", "2028-01-21"]
    )
    rich_cheap = analytics.rich_cheap_table(model="bsm", risk_free_rate=0.04, option_type="call")
    open_interest = analytics.open_interest_grid(
        option_type="put", expiries=["2027-01-15", "2027-06-18", "2028-01-21"]
    )
    return {
        "call_smile_rows": len(call_smile),
        "put_skew_slope": put_skew.slope,
        "term_structure_rows": len(term_structure),
        "largest_rich_strike": float(rich_cheap.iloc[0]["strike"]),
        "total_put_open_interest": float(open_interest["open_interest"].sum()),
    }


def create_chain_visualizations(analytics: object) -> dict[str, str]:
    """Create and save the listed-option-chain analytics figures."""
    output_directory = configure_example_visuals(subdirectory="option_chain_analytics")
    figures = {
        "iv_smile": analytics.visualize(chart="iv_smile", option_type="call", filename="iv_smile"),
        "iv_surface": analytics.visualize(
            chart="iv_surface", option_type="call", filename="iv_surface"
        ),
        "term_structure": analytics.visualize(
            chart="term_structure", option_type="call", strike=100.0, filename="term_structure"
        ),
        "rich_cheap": analytics.visualize(
            chart="rich_cheap",
            option_type="call",
            risk_free_rate=0.04,
            filename="rich_cheap",
        ),
        "open_interest_heatmap": analytics.visualize(
            chart="open_interest_heatmap",
            option_type="put",
            filename="open_interest_heatmap",
        ),
    }
    reset_example_visuals()
    return {name: type(figure).__name__ for name, figure in figures.items()} | {
        "output_directory": str(output_directory)
    }


def run() -> None:
    """Run the deterministic option-chain analytics workflow."""
    analytics = build_option_chain_analytics()
    print_mapping("Option-chain analytics", inspect_chain_analytics(analytics))
    try:
        print_mapping("Created option-chain figures", create_chain_visualizations(analytics))
    except VisualizationError as exc:
        print(f"Visualization skipped: {exc}")


if __name__ == "__main__":
    run()
