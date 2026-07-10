"""Deterministic scenario-analysis tests for derivatives, portfolios, and credit."""

from __future__ import annotations

import os

os.environ.setdefault("MPLBACKEND", "Agg")

import pandas as pd
import pytest

from abaquant.credit import (
    BalanceSheetInputs,
    CashFlowInputs,
    CreditAnalysisInputs,
    CreditHistoricalSeries,
    IncomeStatementInputs,
    calculate_credit_proxy_metrics,
)
from abaquant.derivatives.models import BlackScholesMertonModel
from abaquant.portfolio import PortfolioAllocator


def test_derivative_scenario_grid_contains_prices_and_greeks() -> None:
    """Derivative scenario grids include decomposition and selected Greeks."""
    model = BlackScholesMertonModel(100.0, 105.0, 1.0, 0.05, 0.20)
    grid = model.scenario_grid(
        spot_prices=[90.0, 100.0, 110.0],
        volatilities=[0.15, 0.25],
        option_type="call",
    )

    assert len(grid.data) == 6
    assert {"price", "intrinsic_value", "extrinsic_value", "delta", "gamma"}.issubset(
        grid.data.columns
    )
    assert grid.pivot("price").shape == (2, 3)
    assert float(grid.data["extrinsic_value"].min()) >= -1e-10


def test_derivative_scenario_grid_visualizes() -> None:
    """Derivative scenario grids return figure objects for heatmap charts."""
    pytest.importorskip("matplotlib")
    model = BlackScholesMertonModel(100.0, 105.0, 1.0, 0.05, 0.20)
    grid = model.scenario_grid(
        spot_prices=[90.0, 100.0, 110.0],
        volatilities=[0.15, 0.25],
        option_type="put",
    )

    assert grid.visualize(metric="price", chart="heatmap") is not None


def test_portfolio_scenario_analysis_computes_contributions() -> None:
    """Portfolio scenarios multiply shocks by aligned weights."""
    allocator = PortfolioAllocator(
        pd.DataFrame({"NVDA": [0.01, 0.02], "MSFT": [0.0, 0.01], "AAPL": [0.02, -0.01]})
    )
    scenario = allocator.scenario_analysis(
        shocks={"NVDA": -0.20, "MSFT": -0.10, "AAPL": -0.15},
        weights={"NVDA": 0.5, "MSFT": 0.3, "AAPL": 0.2},
        base_value=1000.0,
    )

    assert scenario.portfolio_return == pytest.approx(-0.16)
    assert scenario.ending_value == pytest.approx(840.0)
    assert scenario.as_frame().loc["NVDA", "contribution"] == pytest.approx(-0.10)


def test_portfolio_scenario_visualizes() -> None:
    """Portfolio scenario objects expose contribution visualizations."""
    pytest.importorskip("matplotlib")
    allocator = PortfolioAllocator(pd.DataFrame({"A": [0.01, 0.02], "B": [0.0, 0.01]}))
    scenario = allocator.scenario_analysis(shocks={"A": -0.1, "B": -0.05})

    assert scenario.visualize(chart="contributions") is not None


def test_credit_scenario_analysis_recomputes_proxy_scores() -> None:
    """Credit scenarios retain input provenance and recalculate metrics."""
    assessment = calculate_credit_proxy_metrics(
        CreditAnalysisInputs(
            balance_sheet=BalanceSheetInputs(
                total_debt=100.0,
                total_equity=250.0,
                current_assets=180.0,
                current_liabilities=75.0,
                cash_and_cash_equivalents=30.0,
                total_assets=500.0,
                total_liabilities=210.0,
                retained_earnings=120.0,
            ),
            income_statement=IncomeStatementInputs(
                revenue=600.0,
                ebit=80.0,
                ebitda=100.0,
                interest_expense=8.0,
                net_income=55.0,
            ),
            cash_flow_statement=CashFlowInputs(operating_cash_flow=70.0),
            historical_series=CreditHistoricalSeries(
                earnings_history=(45.0, 50.0, 55.0),
                leverage_history=(0.5, 0.45, 0.4),
            ),
        )
    )

    scenario = assessment.scenario_analysis(
        debt_multiplier=[1.0, 1.5],
        ebitda_multiplier=[1.0, 0.75],
    )

    assert len(scenario.data) == 4
    assert "synthetic_credit_proxy_score" in scenario.data.columns
    assert scenario.data["net_debt_to_ebitda"].notna().all()


def test_credit_scenario_visualizes() -> None:
    """Credit scenario grids expose heatmap visualizations."""
    pytest.importorskip("matplotlib")
    assessment = calculate_credit_proxy_metrics(
        CreditAnalysisInputs(
            balance_sheet=BalanceSheetInputs(total_debt=100.0, total_equity=250.0),
            income_statement=IncomeStatementInputs(ebitda=100.0),
            cash_flow_statement=CashFlowInputs(),
        )
    )
    scenario = assessment.scenario_analysis(debt_multiplier=[1.0, 1.2], ebitda_multiplier=[1.0])

    assert scenario.visualize(chart="bar") is not None
