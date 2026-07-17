"""Provider-fed financial-statement cache example using an offline provider."""

from __future__ import annotations

import abaquant as aq
from _shared.deterministic_market_provider import DeterministicMarketDataProvider
from _shared.output import print_mapping


def build_cached_ticker() -> object:
    """Create a ticker backed by deterministic statement fixtures."""
    return aq.get_ticker(
        "DEMO", provider=DeterministicMarketDataProvider(), financial_cache="memory"
    )


def run() -> None:
    """Read statement line items and derive credit-proxy metrics."""
    ticker = build_cached_ticker()
    snapshot = ticker.financials.snapshot(period="annual")
    assessment = ticker.credit.assess_from_financials(period="annual")
    print_mapping(
        "Cached financial statements",
        {
            "statement_provider": snapshot.provider_name,
            "total_debt": ticker.financials.total_debt(),
            "ebitda": ticker.financials.ebitda(),
            "operating_cash_flow": ticker.financials.operating_cash_flow(),
            "credit_proxy_score": assessment.synthetic_credit_proxy_score,
        },
    )


if __name__ == "__main__":
    run()
