"""Deterministic tests for the transparent portfolio backtesting layer."""

from __future__ import annotations

import os

os.environ.setdefault("MPLBACKEND", "Agg")

import pandas as pd
import pytest

from abaquant.portfolio import PortfolioAllocator, run_rebalanced_backtest


def sample_return_panel() -> pd.DataFrame:
    """Return a compact deterministic return panel with monthly dates."""
    return pd.DataFrame(
        {
            "NVDA": [0.02, -0.01, 0.03, 0.01, -0.02, 0.04],
            "MSFT": [0.01, 0.00, 0.02, -0.01, 0.01, 0.02],
            "AAPL": [0.00, 0.01, -0.01, 0.02, 0.01, 0.00],
        },
        index=pd.date_range("2025-01-31", periods=6, freq=pd.offsets.MonthEnd()),
    )


def test_rebalanced_backtest_returns_core_metrics() -> None:
    """Backtest summaries include performance, risk, cost, and turnover metrics."""
    result = run_rebalanced_backtest(
        sample_return_panel(),
        weights="equal_weight",
        rebalance="monthly",
        transaction_cost_bps=5.0,
        initial_capital=1000.0,
        annual_risk_free_rate=0.02,
    )
    summary = result.summary()

    assert result.equity_curve().iloc[0] == pytest.approx(1000.0)
    assert result.equity_curve().iloc[-1] > 0.0
    assert result.drawdowns().min() <= 0.0
    assert "cagr" in summary
    assert "annualized_volatility" in summary
    assert "sharpe_ratio" in summary
    assert "sortino_ratio" in summary
    assert "max_drawdown" in summary
    assert "calmar_ratio" in summary
    assert "transaction_cost_drag" in summary
    assert "total_turnover" in summary


def test_allocator_backtest_delegates_to_return_panel() -> None:
    """PortfolioAllocator exposes the object-oriented backtest API."""
    allocator = PortfolioAllocator(sample_return_panel(), annual_risk_free_rate=0.02)
    result = allocator.backtest(
        weights={"NVDA": 0.5, "MSFT": 0.3, "AAPL": 0.2},
        rebalance="monthly",
        transaction_cost_bps=2.0,
        initial_capital=500.0,
    )

    assert result.equity_curve().iloc[0] == pytest.approx(500.0)
    assert list(result.weights_history.columns) == ["NVDA", "MSFT", "AAPL"]
    assert result.transaction_cost_bps == pytest.approx(2.0)


def test_benchmark_hit_rate_treats_roundoff_as_a_tie() -> None:
    """Numerical noise cannot turn equal strategy and benchmark returns into wins."""
    result = run_rebalanced_backtest(
        sample_return_panel(),
        weights="equal_weight",
        rebalance="daily",
        benchmark="equal_weight",
    )

    assert result.summary()["hit_rate_vs_benchmark"] == 0.0


def test_backtest_visualizations_return_figures() -> None:
    """Backtest result objects expose themed visualization methods."""
    pytest.importorskip("matplotlib")
    result = run_rebalanced_backtest(sample_return_panel(), weights="equal_weight")

    assert result.visualize(chart="equity_curve") is not None
    assert result.visualize(chart="drawdown") is not None
    assert result.visualize(chart="weights") is not None
    assert result.visualize(chart="turnover") is not None


def test_backtest_rejects_bad_weights() -> None:
    """Invalid target allocations fail before simulation begins."""
    with pytest.raises(ValueError):
        run_rebalanced_backtest(
            sample_return_panel(),
            weights={"NVDA": 0.5, "MSFT": 0.3, "UNKNOWN": 0.2},
        )


def test_backtest_exposes_extended_diagnostics() -> None:
    """Backtest results include benchmark, rolling, return-table, contribution, and trade diagnostics."""
    result = run_rebalanced_backtest(
        sample_return_panel(),
        weights="inverse_volatility",
        rebalance="monthly",
        transaction_cost_bps=3.0,
        slippage_bps=1.0,
        fixed_transaction_cost=0.25,
        initial_capital=1000.0,
        benchmark="equal_weight",
        lookback=3,
    )
    summary = result.summary()

    assert result.benchmark_returns() is not None
    assert result.benchmark_equity_curve() is not None
    assert result.active_returns() is not None
    assert "tracking_error" in summary
    assert "information_ratio" in summary
    assert "omega_ratio" in summary
    assert "value_at_risk_95" in summary
    assert not result.rolling_metrics(window=3).empty
    assert not result.return_table().empty
    assert not result.drawdown_events(top=3).empty or result.drawdown_events(top=3).empty
    assert "total_return_contribution" in result.contribution_summary().columns
    assert "transaction_cost" in result.trade_summary().columns
    assert result.cost_summary()["total_transaction_cost"] >= 0.0
    assert "benchmark_equity" in result.as_frame().columns


def test_buy_and_hold_rebalances_only_once() -> None:
    """The none rebalance policy applies the initial weights and then lets weights drift."""
    result = run_rebalanced_backtest(
        sample_return_panel(),
        weights="buy_and_hold",
        rebalance="none",
        initial_capital=1000.0,
    )

    assert len(result.weights_history) == 1
    assert result.rebalance == "none"
    assert result.weight_policy == "buy_and_hold"


def test_callable_weight_policy_is_supported() -> None:
    """A callable may resolve target weights from historical data and a rebalance date."""

    def policy(history: pd.DataFrame, rebalance_date: pd.Timestamp) -> dict[str, float]:
        del history, rebalance_date
        return {"NVDA": 0.4, "MSFT": 0.4, "AAPL": 0.2}

    result = run_rebalanced_backtest(sample_return_panel(), weights=policy, rebalance="monthly")

    assert result.weight_policy == "policy"
    assert result.weights_history.iloc[0]["NVDA"] == pytest.approx(0.4)


def test_extended_backtest_visualizations_return_figures() -> None:
    """Extended backtest charts return backend-native figures."""
    pytest.importorskip("matplotlib")
    result = run_rebalanced_backtest(sample_return_panel(), weights="equal_weight")

    assert result.visualize(chart="benchmark") is not None
    assert result.visualize(chart="transaction_costs") is not None
    assert result.visualize(chart="rolling_sharpe", rolling_window=3) is not None
    assert result.visualize(chart="rolling_volatility", rolling_window=3) is not None
    assert result.visualize(chart="return_heatmap") is not None
    assert result.visualize(chart="contributions") is not None
    assert result.visualize(chart="trade_weights") is not None
