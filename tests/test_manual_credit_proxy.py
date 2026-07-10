"""Deterministic tests for grouped fundamental credit-proxy inputs."""

from __future__ import annotations

import unittest

from abaquant.credit import (
    BalanceSheetInputs,
    CashFlowInputs,
    CreditAnalysisInputs,
    CreditHistoricalSeries,
    IncomeStatementInputs,
    MarketEquityObservation,
    PriorPeriodInputs,
    calculate_credit_proxy_metrics,
)
from abaquant.marketdata import get_ticker


class FakeProvider:
    """Provider fixture used to verify manual assessment remains provider-free."""

    name = "fake"

    def __init__(self):
        self.call_count = 0

    def fast_info(self, symbol):
        self.call_count += 1
        return {"last_price": 100.0}

    def info(self, symbol):
        self.call_count += 1
        return {}


def complete_inputs() -> CreditAnalysisInputs:
    """Return a complete grouped accounting input fixture."""
    return CreditAnalysisInputs(
        BalanceSheetInputs(
            total_debt=120,
            total_equity=300,
            current_assets=180,
            inventory=30,
            current_liabilities=90,
            cash_and_cash_equivalents=20,
            total_assets=440,
            total_liabilities=190,
            retained_earnings=150,
            long_term_debt=100,
            shares_outstanding=1000,
        ),
        IncomeStatementInputs(
            revenue=400, gross_profit=200, ebit=70, ebitda=85, interest_expense=5, net_income=50
        ),
        CashFlowInputs(64),
        PriorPeriodInputs(
            total_assets=400,
            net_income=40,
            long_term_debt=110,
            current_assets=160,
            current_liabilities=90,
            shares_outstanding=1000,
            gross_profit=180,
            revenue=360,
        ),
        MarketEquityObservation(1000),
        CreditHistoricalSeries((38, 41, 40, 50), (0.70, 0.61, 0.53, 0.40)),
    )


class ManualCreditProxyTests(unittest.TestCase):
    """Verify grouped input metrics and provider independence."""

    def test_manual_ratios_and_scores(self):
        assessment = calculate_credit_proxy_metrics(complete_inputs())
        self.assertAlmostEqual(assessment.metrics["debt_to_equity"], 0.4)
        self.assertEqual(assessment.metrics["piotroski_f_score"], 8)

    def test_missing_values_are_not_imputed(self):
        assessment = calculate_credit_proxy_metrics(
            CreditAnalysisInputs(
                BalanceSheetInputs(total_debt=10, total_equity=20),
                IncomeStatementInputs(),
                CashFlowInputs(),
            )
        )
        self.assertEqual(assessment.metrics["debt_to_equity"], 0.5)
        self.assertIsNone(assessment.metrics["altman_z_score"])

    def test_ticker_credit_namespace_is_provider_free(self):
        provider = FakeProvider()
        ticker = get_ticker(" nvda ", provider=provider)
        assessment = ticker.credit.assess(complete_inputs())
        self.assertEqual(ticker.symbol, "NVDA")
        self.assertEqual(provider.call_count, 0)
        self.assertIsNotNone(assessment.synthetic_credit_proxy_score)
