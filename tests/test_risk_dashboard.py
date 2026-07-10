"""Deterministic tests for the integrated risk dashboard."""

from __future__ import annotations

import os

os.environ.setdefault("MPLBACKEND", "Agg")

import pandas as pd
import pytest

from abaquant import RiskDashboard
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
from abaquant.portfolio import PortfolioAllocator


def sample_returns() -> pd.DataFrame:
    """Return a deterministic three-asset return panel."""
    return pd.DataFrame(
        {
            "NVDA": [0.02, -0.01, 0.03, 0.01, -0.02, 0.04],
            "MSFT": [0.01, 0.00, 0.02, -0.01, 0.01, 0.02],
            "AAPL": [0.00, 0.01, -0.01, 0.02, 0.01, 0.00],
        },
        index=pd.date_range("2025-01-31", periods=6, freq=pd.offsets.MonthEnd()),
    )


def credit_assessment(debt: float = 120.0, ebitda: float = 85.0):
    """Return a complete deterministic credit-proxy assessment."""
    inputs = CreditAnalysisInputs(
        BalanceSheetInputs(
            total_debt=debt,
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
            revenue=400, gross_profit=200, ebit=70, ebitda=ebitda, interest_expense=5, net_income=50
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
    return calculate_credit_proxy_metrics(inputs)


def test_risk_dashboard_combines_portfolio_credit_and_correlation() -> None:
    """Dashboard summaries combine portfolio, risk, credit, and correlation sections."""
    allocator = PortfolioAllocator(sample_returns(), annual_risk_free_rate=0.02)
    dashboard = RiskDashboard(
        allocator,
        credit_assessments={"NVDA": credit_assessment(), "MSFT": credit_assessment(debt=90.0)},
        weights={"NVDA": 0.5, "MSFT": 0.3, "AAPL": 0.2},
    )
    summary = dashboard.summary()

    assert set(summary) == {"portfolio", "risk_contribution", "credit", "correlation"}
    assert "sharpe_ratio" in summary["portfolio"]
    assert summary["credit"]["assessment_count"] == 2
    assert dashboard.risk_contribution()["percent_risk_contribution"].sum() == pytest.approx(1.0)
    assert dashboard.credit_scores().loc["NVDA", "synthetic_credit_proxy_score"] is not None
    assert dashboard.correlation().shape == (3, 3)


def test_risk_dashboard_accepts_precomputed_backtest() -> None:
    """A dashboard can use a precomputed backtest result for drawdowns and summaries."""
    allocator = PortfolioAllocator(sample_returns(), annual_risk_free_rate=0.02)
    backtest = allocator.backtest(
        weights="equal_weight", rebalance="monthly", transaction_cost_bps=2.0
    )
    dashboard = RiskDashboard(allocator, backtest=backtest)

    assert dashboard.equity_curve().equals(backtest.equity_curve())
    assert dashboard.drawdown().equals(backtest.drawdowns())
    assert dashboard.portfolio_summary()["source"] == "backtest"


def test_risk_dashboard_visualizations_return_figures() -> None:
    """All dashboard chart types return backend-native figures."""
    pytest.importorskip("matplotlib")
    allocator = PortfolioAllocator(sample_returns(), annual_risk_free_rate=0.02)
    dashboard = RiskDashboard(allocator, credit_assessments={"NVDA": credit_assessment()})

    assert dashboard.visualize(chart="risk_contribution") is not None
    assert dashboard.visualize(chart="drawdown") is not None
    assert dashboard.visualize(chart="credit_scores") is not None
    assert dashboard.visualize(chart="correlation") is not None
    assert set(dashboard.visual_report()) == {
        "risk_contribution",
        "drawdown",
        "credit_scores",
        "correlation",
    }


def test_risk_dashboard_rejects_bad_weights() -> None:
    """Dashboard construction rejects invalid static weights."""
    with pytest.raises(ValueError):
        RiskDashboard(sample_returns(), weights={"NVDA": 0.6, "MSFT": 0.6})
