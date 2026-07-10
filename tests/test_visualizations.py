"""Deterministic smoke tests for optional figure construction."""

from __future__ import annotations

import os

os.environ.setdefault("MPLBACKEND", "Agg")
import unittest

import pandas as pd
import pytest

from abaquant.credit.fundamentals import (
    BalanceSheetInputs,
    CashFlowInputs,
    CreditAnalysisInputs,
    IncomeStatementInputs,
    calculate_credit_proxy_metrics,
)
from abaquant.derivatives.models import BlackScholesMertonModel, CoxRossRubinsteinModel
from abaquant.portfolio.optimization import PortfolioAllocator


class VisualizationTests(unittest.TestCase):
    """Verify that public analytical visualizations return figure objects."""

    def test_option_model_charts(self) -> None:
        """Build deterministic payoff, price-profile, and tree figures."""
        pytest.importorskip("matplotlib")
        model = BlackScholesMertonModel(100.0, 100.0, 1.0, 0.05, 0.20)
        self.assertIsNotNone(model.visualize(chart="payoff"))
        self.assertIsNotNone(model.visualize(chart="price_profile"))
        lattice = CoxRossRubinsteinModel(100.0, 100.0, 1.0, 0.05, 0.20, number_of_steps=4)
        self.assertIsNotNone(lattice.visualize(chart="tree"))

    def test_option_diagnostics_and_surface_charts(self) -> None:
        """Build diagnostics and surface figures for one scalar option model."""
        pytest.importorskip("matplotlib")
        model = BlackScholesMertonModel(100.0, 105.0, 1.0, 0.05, 0.20)
        report = model.diagnostics(option_type="call")
        self.assertGreater(report.price, 0.0)
        self.assertEqual(report.intrinsic_value, 0.0)
        self.assertGreater(report.extrinsic_value, 0.0)
        self.assertIn("delta", report.greeks)
        self.assertIsNotNone(model.visualize(chart="extrinsic_value", option_type="call"))
        self.assertIsNotNone(
            model.visualize(chart="greeks", option_type="call", greek_scale="standardized")
        )
        self.assertIsNotNone(
            model.visualize(
                chart="price_surface", option_type="call", grid_size=7, volatility_grid_size=5
            )
        )
        self.assertIsNotNone(
            model.visualize(
                chart="delta_surface", option_type="call", grid_size=7, volatility_grid_size=5
            )
        )
        self.assertIsNotNone(
            model.visualize(
                chart="extrinsic_surface", option_type="call", grid_size=7, volatility_grid_size=5
            )
        )

    def test_portfolio_and_credit_charts(self) -> None:
        """Build deterministic portfolio and proxy-assessment figures."""
        pytest.importorskip("matplotlib")
        allocator = PortfolioAllocator(
            pd.DataFrame({"A": [0.01, -0.01, 0.02], "B": [0.0, 0.01, -0.005]})
        )
        self.assertIsNotNone(allocator.visualize(chart="weights"))
        inputs = CreditAnalysisInputs(
            balance_sheet=BalanceSheetInputs(
                total_debt=100.0, total_equity=200.0, current_assets=120.0, current_liabilities=60.0
            ),
            income_statement=IncomeStatementInputs(ebit=50.0, ebitda=60.0, interest_expense=5.0),
            cash_flow_statement=CashFlowInputs(operating_cash_flow=40.0),
        )
        self.assertIsNotNone(calculate_credit_proxy_metrics(inputs).visualize(chart="metrics"))


if __name__ == "__main__":
    unittest.main()
