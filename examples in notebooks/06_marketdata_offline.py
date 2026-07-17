"""Applied market-data examples using a deterministic offline provider."""

from __future__ import annotations

from _shared.deterministic_market_provider import DeterministicMarketDataProvider
from _shared.output import (
    configure_example_visuals,
    print_mapping,
    reset_example_visuals,
)
from _shared.package_bootstrap import ensure_package_importable

ensure_package_importable()

from abaquant.marketdata import get_ticker, get_tickers
from abaquant.visualization import VisualizationError


def build_ticker_and_universe() -> tuple[object, object]:
    """Create one ticker and one universe without Yahoo or network access."""
    provider = DeterministicMarketDataProvider()
    ticker = get_ticker("DEMO", provider=provider, financial_cache="memory")
    universe = get_tickers(["ALPHA", "BETA", "GAMMA"], provider=provider)
    return ticker, universe


def inspect_ticker(ticker: object) -> dict[str, object]:
    """Call quote, history, option, and financial-statement methods."""
    option_value = ticker.options.bsm(
        strike=100.0,
        maturity=0.5,
        risk_free_rate=0.04,
        volatility=0.20,
        option_type="call",
    )
    greeks = ticker.options.greeks(
        strike=100.0,
        maturity=0.5,
        risk_free_rate=0.04,
        volatility=0.20,
        option_type="call",
    )
    chain_analytics = ticker.options.analytics("2027-01-15")
    iv_smile = chain_analytics.iv_smile(option_type="call")
    rich_cheap = chain_analytics.rich_cheap_table(risk_free_rate=0.04, option_type="call")
    return {
        "symbol": ticker.symbol,
        "spot": ticker.spot(),
        "history_rows": len(ticker.history.prices(period="1mo")),
        "listed_option_expiries": ticker.options.expirations(),
        "option_chain_rows": len(ticker.options.chain(expiry="2027-01-15")),
        "iv_smile_rows": len(iv_smile),
        "largest_rich_contract_strike": float(rich_cheap.iloc[0]["strike"]),
        "bsm_call": option_value,
        "delta": greeks["delta"],
        "total_debt": ticker.financials.total_debt(),
        "ebitda": ticker.financials.ebitda(),
    }


def assess_credit_from_cached_financials(ticker: object) -> dict[str, object]:
    """Build credit inputs from cached statement fixtures and assess them."""
    inputs = ticker.financials.credit_inputs()
    assessment = ticker.credit.assess(inputs)
    from_financials = ticker.credit.assess_from_financials()
    return {
        "input_currency": inputs.reporting_currency,
        "synthetic_score": assessment.synthetic_credit_proxy_score,
        "synthetic_band": assessment.synthetic_credit_proxy_band,
        "convenience_score": from_financials.synthetic_credit_proxy_score,
    }


def inspect_universe(universe: object) -> dict[str, object]:
    """Call universe prices, returns, statistics, and portfolio methods."""
    prices = universe.history.prices(period="1mo")
    returns = universe.history.returns(period="1mo")
    summary = universe.statistics.summary(period="1mo")
    portfolio = universe.portfolio.max_sharpe(period="1mo", risk_free_rate=0.02)
    return {
        "symbols": universe.symbols,
        "price_shape": prices.shape,
        "return_shape": returns.shape,
        "summary_rows": len(summary),
        "max_sharpe_alpha_weight": float(next(iter(portfolio.weights.values()))),
        "max_sharpe_ratio": portfolio.sharpe_ratio,
    }


def create_marketdata_visualizations(ticker: object, universe: object) -> dict[str, str]:
    """Create and save ticker, universe, statement, and credit figures."""
    output_directory = configure_example_visuals(subdirectory="marketdata_offline")
    assessment = ticker.credit.assess_from_financials()
    option_analytics = ticker.options.analytics("2027-01-15")
    figures = {
        "ticker_history": ticker.visualize(period="1mo", filename="ticker_history"),
        "income_statement": ticker.financials.visualize(
            statement="income_statement", filename="income_statement"
        ),
        "option_iv_smile": option_analytics.visualize(
            chart="iv_smile", option_type="call", filename="option_iv_smile"
        ),
        "option_rich_cheap": option_analytics.visualize(
            chart="rich_cheap",
            option_type="call",
            risk_free_rate=0.04,
            filename="option_rich_cheap",
        ),
        "option_open_interest": option_analytics.visualize(
            chart="open_interest_heatmap", option_type="call", filename="option_open_interest"
        ),
        "credit_metrics": assessment.visualize(chart="metrics", filename="credit_metrics"),
        "credit_score": assessment.visualize(chart="score", filename="credit_score"),
        "universe_history": universe.visualize(period="1mo", filename="universe_history"),
    }
    reset_example_visuals()
    return {name: type(figure).__name__ for name, figure in figures.items()} | {
        "output_directory": str(output_directory)
    }


def run() -> None:
    """Run the offline applied market-data workflow."""
    ticker, universe = build_ticker_and_universe()
    print_mapping("Ticker workflow", inspect_ticker(ticker))
    print_mapping("Credit from cached financials", assess_credit_from_cached_financials(ticker))
    print_mapping("Universe workflow", inspect_universe(universe))
    try:
        print_mapping(
            "Created market-data figures", create_marketdata_visualizations(ticker, universe)
        )
    except VisualizationError as exc:
        print(f"Visualization skipped: {exc}")


if __name__ == "__main__":
    run()
