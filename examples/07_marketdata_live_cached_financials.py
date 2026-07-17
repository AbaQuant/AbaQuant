"""Optional live Yahoo/yfinance financial-statement cache example.

This example is intentionally not part of the deterministic runner. It can make
network requests and requires the optional market-data dependency.
"""

from __future__ import annotations

from pathlib import Path

import abaquant as aq
from _shared.output import configure_example_visuals, print_mapping, reset_example_visuals


def build_live_ticker(symbol: str = "NVDA") -> object:
    """Create one Yahoo-backed ticker with disk financial-statement caching."""
    return aq.get_ticker(
        symbol,
        provider="yahoo",
        financial_cache="disk",
        cache_directory=Path(".qa_example_cache"),
    )


def download_or_reuse_snapshot(ticker: object) -> object:
    """Retrieve a cached or fresh annual statement snapshot."""
    return ticker.financials.snapshot(period="annual", refresh_policy="if_stale", max_age_days=7)


def summarize_live_financials(ticker: object) -> dict[str, object]:
    """Read major line items and credit proxies from the snapshot."""
    assessment = ticker.credit.assess_from_financials(period="annual")
    return {
        "symbol": ticker.symbol,
        "total_debt": ticker.financials.total_debt(period="annual"),
        "ebitda": ticker.financials.ebitda(period="annual"),
        "operating_cash_flow": ticker.financials.operating_cash_flow(period="annual"),
        "synthetic_score": assessment.synthetic_credit_proxy_score,
        "synthetic_band": assessment.synthetic_credit_proxy_band,
    }


def create_live_visualizations(ticker: object) -> dict[str, str]:
    """Create optional live statement and credit charts."""
    output_directory = configure_example_visuals(subdirectory="marketdata_live")
    assessment = ticker.credit.assess_from_financials(period="annual")
    figures = {
        "balance_sheet": ticker.financials.visualize(
            statement="balance_sheet", filename="live_balance_sheet"
        ),
        "credit_score": assessment.visualize(chart="score", filename="live_credit_score"),
    }
    reset_example_visuals()
    return {name: type(figure).__name__ for name, figure in figures.items()} | {
        "output_directory": str(output_directory)
    }


def run() -> None:
    """Run the optional live workflow and handle unavailable providers cleanly."""
    ticker = build_live_ticker("NVDA")
    try:
        download_or_reuse_snapshot(ticker)
        print_mapping("Live cached financials", summarize_live_financials(ticker))
        try:
            print_mapping("Live financial figures", create_live_visualizations(ticker))
        except aq.VisualizationError as exc:
            print(f"Visualization skipped: {exc}")
    except aq.MarketDataError as exc:
        print("Live Yahoo example skipped.")
        print(exc)


if __name__ == "__main__":
    run()
