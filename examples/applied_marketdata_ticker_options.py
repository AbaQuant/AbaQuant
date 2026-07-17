"""Single-ticker options workflow with an offline provider."""

from __future__ import annotations

import abaquant as aq
from _shared.deterministic_market_provider import DeterministicMarketDataProvider
from _shared.output import configure_example_visuals, print_mapping, reset_example_visuals


def build_ticker() -> object:
    """Create one deterministic ticker."""
    return aq.get_ticker(
        "DEMO", provider=DeterministicMarketDataProvider(), financial_cache="memory"
    )


def compute_option_workflow(ticker: object) -> dict[str, object]:
    """Run option-chain, BSM, Greeks, and IV examples."""
    return {
        "spot": ticker.spot(),
        "expirations": ticker.options.expirations(),
        "chain_rows": len(ticker.options.chain(expiry="2027-01-15")),
        "listed_iv": ticker.options.listed_implied_volatility(strike=100.0, expiry="2027-01-15"),
        "bsm_call": ticker.options.bsm(
            strike=100.0, maturity=0.5, risk_free_rate=0.04, volatility=0.20
        ),
        "delta": ticker.options.greeks(
            strike=100.0, maturity=0.5, risk_free_rate=0.04, volatility=0.20
        )["delta"],
    }


def create_ticker_figures(ticker: object) -> dict[str, str]:
    """Create the ticker price-history figure."""
    output_directory = configure_example_visuals(subdirectory="ticker_options")
    figure = ticker.visualize(period="1mo", filename="ticker_price_history")
    reset_example_visuals()
    return {"ticker_history": type(figure).__name__, "output_directory": str(output_directory)}


def run() -> None:
    """Run the single-ticker options example."""
    ticker = build_ticker()
    print_mapping("Ticker options workflow", compute_option_workflow(ticker))
    try:
        print_mapping("Ticker figures", create_ticker_figures(ticker))
    except aq.VisualizationError as exc:
        print(f"Visualization skipped: {exc}")


if __name__ == "__main__":
    run()
