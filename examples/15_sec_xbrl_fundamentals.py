"""SEC EDGAR/XBRL financial-statement provider example.

This deterministic example demonstrates the same user workflow as the live SEC
provider without making a network request. The fixture mimics the official SEC
Company Facts JSON shape and lets the example show the full pipeline:

SEC Company Facts -> canonical statement tables -> credit inputs -> proxy metrics.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import abaquant as aq
from _shared.output import print_mapping, print_section


def _fact(value: float, end: str, *, fp: str = "FY", form: str = "10-K") -> dict[str, Any]:
    """Build a compact SEC fact record for the offline example."""
    return {"val": value, "end": end, "fp": fp, "form": form, "filed": "2026-03-01"}


def _sec_company_facts_fixture() -> dict[str, Any]:
    """Return a small SEC Company Facts fixture with US-GAAP and DEI tags."""
    current = "2026-01-31"
    prior = "2025-01-31"

    def usd(*records: dict[str, Any]) -> dict[str, Any]:
        return {"units": {"USD": list(records)}}

    def shares(*records: dict[str, Any]) -> dict[str, Any]:
        return {"units": {"shares": list(records)}}

    return {
        "cik": 1045810,
        "entityName": "NVIDIA CORP",
        "facts": {
            "us-gaap": {
                "RevenueFromContractWithCustomerExcludingAssessedTax": usd(
                    _fact(400.0, current), _fact(360.0, prior)
                ),
                "GrossProfit": usd(_fact(200.0, current), _fact(180.0, prior)),
                "OperatingIncomeLoss": usd(_fact(80.0, current), _fact(70.0, prior)),
                "InterestExpenseNonOperating": usd(_fact(5.0, current), _fact(6.0, prior)),
                "NetIncomeLoss": usd(_fact(50.0, current), _fact(40.0, prior)),
                "EarningsBeforeInterestTaxesDepreciationAmortization": usd(
                    _fact(95.0, current), _fact(80.0, prior)
                ),
                "Assets": usd(_fact(440.0, current), _fact(400.0, prior)),
                "AssetsCurrent": usd(_fact(180.0, current), _fact(160.0, prior)),
                "InventoryNet": usd(_fact(30.0, current), _fact(40.0, prior)),
                "LiabilitiesCurrent": usd(_fact(90.0, current), _fact(90.0, prior)),
                "CashAndCashEquivalentsAtCarryingValue": usd(
                    _fact(25.0, current), _fact(20.0, prior)
                ),
                "Liabilities": usd(_fact(190.0, current), _fact(200.0, prior)),
                "StockholdersEquity": usd(_fact(300.0, current), _fact(270.0, prior)),
                "RetainedEarningsAccumulatedDeficit": usd(
                    _fact(150.0, current), _fact(130.0, prior)
                ),
                "DebtAndFinanceLeaseObligations": usd(_fact(120.0, current), _fact(130.0, prior)),
                "LongTermDebtAndFinanceLeaseObligationsNoncurrent": usd(
                    _fact(100.0, current), _fact(110.0, prior)
                ),
                "NetCashProvidedByUsedInOperatingActivities": usd(
                    _fact(64.0, current), _fact(55.0, prior)
                ),
            },
            "dei": {
                "EntityCommonStockSharesOutstanding": shares(
                    _fact(1000.0, current), _fact(1000.0, prior)
                )
            },
        },
    }


class OfflineSecProvider(aq.marketdata.providers.SecXbrlProvider):
    """SEC provider variant that serves fixture Company Facts instead of HTTP."""

    def __init__(self) -> None:
        """Create a provider with a fixed ticker-to-CIK map."""
        super().__init__(cik_by_symbol={"NVDA": "1045810"})

    def company_facts(self, symbol: str, **kwargs) -> aq.marketdata.providers.SecCompanyFacts:
        """Return fixture Company Facts with the same shape as SEC JSON."""
        clean_symbol = symbol.upper()
        cached = self._company_facts_cache.get(clean_symbol)
        if cached is not None:
            return cached
        facts = aq.marketdata.providers.SecCompanyFacts(
            clean_symbol, "0001045810", _sec_company_facts_fixture()
        )
        self._company_facts_cache[clean_symbol] = facts
        return facts


class CachedOfflineSecProvider(aq.marketdata.providers.SecXbrlProvider):
    """SEC provider variant that demonstrates persistent raw JSON caching."""

    def __init__(self, cache_directory: str | Path) -> None:
        """Create a provider using a disk cache and fixture HTTP responses."""
        super().__init__(cache_mode="disk", cache_directory=cache_directory)
        self.request_count = 0

    def _request_json(self, url: str) -> dict[str, Any]:
        """Return fixture JSON while recording requests that would have used SEC."""
        self.request_count += 1
        if url.endswith("company_tickers.json"):
            return {"0": {"ticker": "NVDA", "cik_str": 1045810, "title": "NVIDIA CORP"}}
        return _sec_company_facts_fixture()


class OfflineQuoteProvider:
    """Minimal quote provider used beside SEC fundamentals."""

    name = "offline-quotes"

    def fast_info(self, symbol: str) -> dict[str, float]:
        """Return a deterministic spot-like quote."""
        return {"last_price": 100.0}

    def info(self, symbol: str) -> dict[str, float]:
        """Return deterministic market-cap metadata for Altman Z-score inputs."""
        return {"marketCap": 1000.0}


def build_ticker():
    """Create a ticker that uses offline quotes and SEC-style fundamentals."""
    return aq.get_ticker(
        "NVDA",
        provider=OfflineQuoteProvider(),
        fundamentals_provider=OfflineSecProvider(),
    )


def inspect_raw_sec_facts(ticker) -> None:
    """Print raw SEC Company Facts metadata exposed by the financial facade."""
    facts = ticker.financials.sec_facts()
    print_mapping(
        "Raw SEC Company Facts metadata",
        {
            "entityName": facts.get("entityName"),
            "cik": facts.get("cik"),
            "taxonomies": sorted(facts.get("facts", {})),
        },
    )


def inspect_statement_tables(ticker) -> None:
    """Print the SEC-derived statement tables used by the credit bridge."""
    print_section("SEC-derived balance sheet")
    print(ticker.financials.balance_sheet(source="sec").head())
    print_section("SEC-derived income statement")
    print(ticker.financials.income_statement(source="sec").head())
    print_section("SEC-derived cash-flow statement")
    print(ticker.financials.cash_flow_statement(source="sec").head())


def inspect_credit_bridge(ticker) -> None:
    """Print credit inputs and proxy metrics built from SEC-derived statements."""
    inputs = ticker.financials.credit_inputs(source="sec")
    assessment = ticker.credit.assess_from_financials(source="sec")
    print_mapping(
        "Credit inputs resolved from SEC-style facts",
        {
            "total_debt": inputs.total_debt,
            "total_equity": inputs.total_equity,
            "revenue": inputs.revenue,
            "operating_cash_flow": inputs.operating_cash_flow,
            "previous_total_assets": inputs.previous_total_assets,
        },
    )
    print_mapping(
        "Credit proxy metrics from SEC-style facts",
        {
            "debt_to_equity": assessment.metrics["debt_to_equity"],
            "net_debt_to_ebitda": assessment.metrics["net_debt_to_ebitda"],
            "altman_z_score": assessment.metrics["altman_z_score"],
            "piotroski_f_score": assessment.metrics["piotroski_f_score"],
            "synthetic_credit_proxy_score": assessment.synthetic_credit_proxy_score,
        },
    )


def demonstrate_sec_disk_cache() -> None:
    """Show that SEC raw facts and normalized statements persist across instances."""
    with TemporaryDirectory() as directory:
        first_sec_provider = CachedOfflineSecProvider(directory)
        first_ticker = aq.get_ticker(
            "NVDA",
            provider=OfflineQuoteProvider(),
            fundamentals_provider=first_sec_provider,
            financial_cache="disk",
            cache_directory=directory,
        )
        first_total_debt = first_ticker.financials.total_debt(source="sec")

        second_sec_provider = CachedOfflineSecProvider(directory)
        second_ticker = aq.get_ticker(
            "NVDA",
            provider=OfflineQuoteProvider(),
            fundamentals_provider=second_sec_provider,
            financial_cache="disk",
            cache_directory=directory,
        )
        second_total_debt = second_ticker.financials.total_debt(
            source="sec", refresh_policy="cache_only"
        )
        raw_facts = second_ticker.financials.sec_facts(refresh_policy="cache_only")

        print_mapping(
            "SEC disk-cache reuse",
            {
                "first_total_debt": first_total_debt,
                "second_total_debt_from_cache": second_total_debt,
                "second_raw_entity_from_cache": raw_facts.get("entityName"),
                "first_provider_json_requests": first_sec_provider.request_count,
                "second_provider_json_requests": second_sec_provider.request_count,
                "normalized_snapshot_on_disk": second_ticker.financials.cache_status(source="sec")[
                    "on_disk"
                ],
                "raw_company_facts_on_disk": second_ticker.financials.sec_cache_status()[
                    "company_facts"
                ]["on_disk"],
            },
        )


def run() -> None:
    """Run the offline SEC/XBRL fundamentals demonstration."""
    print_section("SEC EDGAR/XBRL fundamentals workflow")
    ticker = build_ticker()
    inspect_raw_sec_facts(ticker)
    inspect_statement_tables(ticker)
    inspect_credit_bridge(ticker)
    demonstrate_sec_disk_cache()


if __name__ == "__main__":
    run()
