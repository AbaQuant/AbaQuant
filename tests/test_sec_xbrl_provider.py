"""Deterministic tests for the SEC EDGAR/XBRL fundamentals provider."""

from __future__ import annotations

import gzip
import zlib
from typing import Any

import pandas as pd
import pytest

from abaquant.marketdata import get_ticker
from abaquant.marketdata.providers import SecCompanyFacts, SecXbrlProvider
from abaquant.marketdata.providers.sec import (
    _decode_sec_response_body,
    _statement_from_company_facts,
)


def _fact(
    value: float, end: str, *, fp: str = "FY", form: str = "10-K", filed: str = "2026-03-01"
) -> dict[str, Any]:
    """Build one minimal SEC Company Facts record for tests."""
    return {"val": value, "end": end, "fp": fp, "form": form, "filed": filed}


def _company_facts_payload() -> dict[str, Any]:
    """Return a compact Company Facts payload covering all credit line items."""

    def usd(*records: dict[str, Any]) -> dict[str, Any]:
        return {"units": {"USD": list(records)}}

    def shares(*records: dict[str, Any]) -> dict[str, Any]:
        return {"units": {"shares": list(records)}}

    current = "2026-01-31"
    prior = "2025-01-31"
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


def test_sec_response_body_decoder_handles_plain_gzip_and_deflate_payloads() -> None:
    """Decode SEC JSON responses whether the server sends plain or compressed bytes."""
    payload = b'{"entityName":"NVIDIA CORP"}'

    assert (
        _decode_sec_response_body(payload, content_encoding=None, charset="utf-8")
        == '{"entityName":"NVIDIA CORP"}'
    )
    assert (
        _decode_sec_response_body(gzip.compress(payload), content_encoding="gzip", charset="utf-8")
        == '{"entityName":"NVIDIA CORP"}'
    )
    assert (
        _decode_sec_response_body(
            zlib.compress(payload), content_encoding="deflate", charset="utf-8"
        )
        == '{"entityName":"NVIDIA CORP"}'
    )


class OfflineSecProvider(SecXbrlProvider):
    """SEC provider test double returning fixture Company Facts without network."""

    def __init__(self) -> None:
        """Create a test provider with a fixed CIK mapping."""
        super().__init__(cik_by_symbol={"NVDA": "1045810"})
        self.requests = 0

    def company_facts(self, symbol: str, **kwargs) -> SecCompanyFacts:
        """Return fixture facts and record calls."""
        clean_symbol = symbol.upper()
        cached = self._company_facts_cache.get(clean_symbol)
        if cached is not None:
            return cached
        self.requests += 1
        facts = SecCompanyFacts(clean_symbol, "0001045810", _company_facts_payload())
        self._company_facts_cache[clean_symbol] = facts
        return facts


class QuoteProvider:
    """Minimal quote provider used beside SEC fundamentals in ticker tests."""

    name = "quote-fixture"

    def fast_info(self, symbol: str) -> dict[str, float]:
        """Return one deterministic spot price."""
        return {"last_price": 100.0}

    def info(self, symbol: str) -> dict[str, float]:
        """Return deterministic market-cap metadata."""
        return {"marketCap": 1000.0}


def test_sec_company_facts_normalize_to_statement_frames() -> None:
    """Build SEC-backed statement frames with canonical AbaQuant labels."""
    payload = _company_facts_payload()

    balance = _statement_from_company_facts(
        payload, statement_type="balance_sheet", period="annual"
    )
    income = _statement_from_company_facts(
        payload, statement_type="income_statement", period="annual"
    )
    cash_flow = _statement_from_company_facts(
        payload, statement_type="cash_flow_statement", period="annual"
    )

    assert isinstance(balance, pd.DataFrame)
    assert balance.loc["Total Assets", "2026-01-31"] == pytest.approx(440.0)
    assert balance.loc["Total Debt", "2026-01-31"] == pytest.approx(120.0)
    assert income.loc["Net Income", "2026-01-31"] == pytest.approx(50.0)
    assert cash_flow.loc["Operating Cash Flow", "2026-01-31"] == pytest.approx(64.0)


def test_get_ticker_uses_sec_provider_for_financials_only() -> None:
    """Use SEC fundamentals while retaining a separate quote provider."""
    sec_provider = OfflineSecProvider()
    ticker = get_ticker("NVDA", provider=QuoteProvider(), fundamentals_provider=sec_provider)

    assert ticker.spot() == 100.0
    assert ticker.financials.total_debt(source="sec") == pytest.approx(120.0)
    assert ticker.financials.revenue(source="sec") == pytest.approx(400.0)
    inputs = ticker.financials.credit_inputs(source="sec")
    assessment = ticker.credit.assess_from_financials(source="sec")

    assert inputs.total_debt == pytest.approx(120.0)
    assert inputs.previous_total_assets == pytest.approx(400.0)
    assert inputs.earnings_history == (40.0, 50.0)
    assert assessment.metrics["debt_to_equity"] == pytest.approx(0.4)
    assert sec_provider.requests == 1


def test_sec_facts_method_returns_raw_company_facts() -> None:
    """Expose raw SEC Company Facts through the financial statement facade."""
    ticker = get_ticker(
        "NVDA", provider=QuoteProvider(), fundamentals_provider=OfflineSecProvider()
    )

    facts = ticker.financials.sec_facts()

    assert facts["entityName"] == "NVIDIA CORP"
    assert "us-gaap" in facts["facts"]


def test_sec_provider_disk_cache_reuses_ticker_mapping_and_company_facts(tmp_path) -> None:
    """Persist raw SEC ticker mappings and Company Facts across provider instances."""
    requests: list[str] = []

    class CachedSecProvider(SecXbrlProvider):
        """SEC provider test double that records network-intended URL requests."""

        def _request_json(self, url: str) -> dict[str, Any]:
            """Return fixture SEC JSON payloads without network access."""
            requests.append(url)
            if url.endswith("company_tickers.json"):
                return {"0": {"ticker": "NVDA", "cik_str": 1045810, "title": "NVIDIA CORP"}}
            return _company_facts_payload()

    first_provider = CachedSecProvider(cache_mode="disk", cache_directory=tmp_path)
    first_facts = first_provider.company_facts("NVDA")
    assert first_facts.payload["entityName"] == "NVIDIA CORP"
    assert len(requests) == 2
    assert first_provider.cache_status("NVDA")["company_facts"]["on_disk"] is True

    second_provider = CachedSecProvider(cache_mode="disk", cache_directory=tmp_path)
    second_facts = second_provider.company_facts("NVDA", refresh_policy="cache_only")
    assert second_facts.payload["entityName"] == "NVIDIA CORP"
    assert len(requests) == 2
    assert second_provider.cache_status("NVDA")["company_facts"]["on_disk"] is True


def test_get_ticker_sec_provider_disk_cache_can_reuse_raw_and_normalized_snapshots(
    tmp_path,
) -> None:
    """Use get_ticker disk cache to reuse SEC raw facts and normalized statements."""
    requests: list[str] = []

    class CachedSecProvider(SecXbrlProvider):
        """SEC provider test double using the same disk cache as the ticker."""

        def _request_json(self, url: str) -> dict[str, Any]:
            """Return fixture SEC JSON payloads without network access."""
            requests.append(url)
            if url.endswith("company_tickers.json"):
                return {"0": {"ticker": "NVDA", "cik_str": 1045810, "title": "NVIDIA CORP"}}
            return _company_facts_payload()

    first_provider = CachedSecProvider(cache_mode="disk", cache_directory=tmp_path)
    first = get_ticker(
        "NVDA",
        provider=QuoteProvider(),
        fundamentals_provider=first_provider,
        financial_cache="disk",
        cache_directory=tmp_path,
    )
    assert first.financials.total_debt(source="sec") == pytest.approx(120.0)
    assert len(requests) == 2
    assert first.financials.cache_status(source="sec")["on_disk"] is True
    assert first.financials.sec_cache_status()["company_facts"]["on_disk"] is True

    second_provider = CachedSecProvider(cache_mode="disk", cache_directory=tmp_path)
    second = get_ticker(
        "NVDA",
        provider=QuoteProvider(),
        fundamentals_provider=second_provider,
        financial_cache="disk",
        cache_directory=tmp_path,
    )
    assert second.financials.total_debt(source="sec", refresh_policy="cache_only") == pytest.approx(
        120.0
    )
    assert second.financials.sec_facts(refresh_policy="cache_only")["entityName"] == "NVIDIA CORP"
    assert len(requests) == 2
