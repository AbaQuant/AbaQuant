"""Deterministic tests for cached provider-fed statement snapshots."""

from __future__ import annotations

import tempfile
import unittest

import pandas as pd

from abaquant.marketdata import get_ticker
from abaquant.marketdata.errors import MarketDataProviderError


class StatementProvider:
    """Deterministic provider exposing all three statement families."""

    name = "fixture"

    def __init__(self) -> None:
        """Initialize call counters for financial-statement retrieval."""
        self.statement_calls = 0
        self.info_calls = 0

    def income_statement(self, symbol: str, *, period: str = "annual") -> pd.DataFrame:
        """Return a two-year fixture income statement."""
        self.statement_calls += 1
        return pd.DataFrame(
            {
                "2025-01-31": [400.0, 80.0, 70.0, 90.0, 5.0, 50.0],
                "2024-01-31": [360.0, 72.0, 60.0, 80.0, 6.0, 40.0],
            },
            index=[
                "Total Revenue",
                "Gross Profit",
                "Operating Income",
                "EBITDA",
                "Interest Expense",
                "Net Income",
            ],
        )

    def balance_sheet(self, symbol: str, *, period: str = "annual") -> pd.DataFrame:
        """Return a two-year fixture balance sheet."""
        self.statement_calls += 1
        return pd.DataFrame(
            {
                "2025-01-31": [
                    120.0,
                    300.0,
                    180.0,
                    30.0,
                    90.0,
                    20.0,
                    440.0,
                    190.0,
                    150.0,
                    100.0,
                    1000.0,
                ],
                "2024-01-31": [
                    130.0,
                    270.0,
                    160.0,
                    40.0,
                    90.0,
                    18.0,
                    400.0,
                    200.0,
                    130.0,
                    110.0,
                    1000.0,
                ],
            },
            index=[
                "Total Debt",
                "Stockholders Equity",
                "Current Assets",
                "Inventory",
                "Current Liabilities",
                "Cash And Cash Equivalents",
                "Total Assets",
                "Total Liabilities",
                "Retained Earnings",
                "Long Term Debt",
                "Ordinary Shares Number",
            ],
        )

    def cash_flow_statement(self, symbol: str, *, period: str = "annual") -> pd.DataFrame:
        """Return a two-year fixture cash-flow statement."""
        self.statement_calls += 1
        return pd.DataFrame(
            {"2025-01-31": [64.0], "2024-01-31": [55.0]}, index=["Operating Cash Flow"]
        )

    def info(self, symbol: str) -> dict:
        """Return provider metadata including market capitalization."""
        self.info_calls += 1
        return {"marketCap": 1000.0}


class FinancialStatementCacheTests(unittest.TestCase):
    """Verify one-bundle retrieval, canonical accessors, and disk reuse."""

    def test_line_items_share_one_memory_snapshot(self) -> None:
        """Fetch three statements once and reuse them across convenience methods."""
        provider = StatementProvider()
        ticker = get_ticker(" nvda ", provider=provider)
        self.assertEqual(ticker.financials.total_debt(), 120.0)
        self.assertEqual(ticker.financials.ebitda(), 90.0)
        self.assertEqual(ticker.financials.operating_cash_flow(), 64.0)
        self.assertEqual(provider.statement_calls, 3)
        self.assertTrue(ticker.financials.cache_status()["in_memory"])

    def test_credit_inputs_reuse_snapshot_and_preserve_manual_model(self) -> None:
        """Build complete credit inputs without a second statement retrieval."""
        provider = StatementProvider()
        ticker = get_ticker("NVDA", provider=provider)
        inputs = ticker.financials.credit_inputs()
        assessment = ticker.credit.assess_from_financials()
        self.assertEqual(provider.statement_calls, 3)
        self.assertEqual(inputs.total_debt, 120.0)
        self.assertEqual(inputs.previous_total_assets, 400.0)
        self.assertEqual(inputs.earnings_history, (40.0, 50.0))
        self.assertIsNotNone(assessment.metrics["debt_to_equity"])

    def test_disk_cache_reuses_saved_snapshot_in_second_ticker(self) -> None:
        """Read a disk snapshot without provider calls after the first retrieval."""
        with tempfile.TemporaryDirectory() as directory:
            first_provider = StatementProvider()
            first_ticker = get_ticker(
                "NVDA", provider=first_provider, financial_cache="disk", cache_directory=directory
            )
            self.assertEqual(first_ticker.financials.total_debt(), 120.0)
            self.assertEqual(first_provider.statement_calls, 3)

            second_provider = StatementProvider()
            second_ticker = get_ticker(
                "NVDA", provider=second_provider, financial_cache="disk", cache_directory=directory
            )
            self.assertEqual(
                second_ticker.financials.total_debt(refresh_policy="cache_only"), 120.0
            )
            self.assertEqual(second_provider.statement_calls, 0)
            self.assertTrue(second_ticker.financials.cache_status()["on_disk"])

    def test_cache_only_without_snapshot_fails(self) -> None:
        """Reject cache-only requests when no eligible disk or memory snapshot exists."""
        ticker = get_ticker("NVDA", provider=StatementProvider())
        with self.assertRaises(MarketDataProviderError):
            ticker.financials.snapshot(refresh_policy="cache_only")


if __name__ == "__main__":
    unittest.main()
