"""Portfolio backtesting example with transparent periodic rebalancing."""

from __future__ import annotations

import abaquant as aq
from examples._shared.output import (
    configure_example_visuals,
    print_frame,
    print_mapping,
    reset_example_visuals,
)
from examples._shared.sample_data import sample_returns


def build_allocator() -> aq.PortfolioAllocator:
    """Create a deterministic allocator from synthetic periodic returns."""
    return aq.PortfolioAllocator(sample_returns(), annual_risk_free_rate=0.02)


def run_core_backtest(allocator: aq.PortfolioAllocator):
    """Run the object-oriented backtest from a portfolio allocator."""
    return allocator.backtest(
        weights="inverse_volatility",
        rebalance="monthly",
        transaction_cost_bps=5.0,
        slippage_bps=1.0,
        fixed_transaction_cost=1.0,
        initial_capital=100_000.0,
        benchmark="equal_weight",
        lookback=4,
    )


def run_functional_backtest():
    """Run the same backtest through the functional helper."""
    return aq.run_rebalanced_backtest(
        sample_returns(),
        weights={"ALPHA": 0.45, "BETA": 0.35, "GAMMA": 0.20},
        rebalance="monthly",
        transaction_cost_bps=5.0,
        slippage_bps=1.0,
        fixed_transaction_cost=1.0,
        initial_capital=100_000.0,
        annual_risk_free_rate=0.02,
        benchmark="equal_weight",
    )


def create_backtest_visualizations(backtest) -> dict[str, str]:
    """Create and save the core and extended backtest diagnostic figures."""
    output_directory = configure_example_visuals(subdirectory="portfolio_backtesting")
    figures = {
        "equity_curve": backtest.visualize(chart="equity_curve", filename="backtest_equity_curve"),
        "benchmark": backtest.visualize(chart="benchmark", filename="backtest_benchmark"),
        "drawdown": backtest.visualize(chart="drawdown", filename="backtest_drawdown"),
        "weights": backtest.visualize(chart="weights", filename="backtest_weights"),
        "turnover": backtest.visualize(chart="turnover", filename="backtest_turnover"),
        "transaction_costs": backtest.visualize(
            chart="transaction_costs", filename="backtest_transaction_costs"
        ),
        "rolling_sharpe": backtest.visualize(
            chart="rolling_sharpe", rolling_window=4, filename="backtest_rolling_sharpe"
        ),
        "rolling_volatility": backtest.visualize(
            chart="rolling_volatility", rolling_window=4, filename="backtest_rolling_volatility"
        ),
        "return_heatmap": backtest.visualize(
            chart="return_heatmap", filename="backtest_return_heatmap"
        ),
        "contributions": backtest.visualize(
            chart="contributions", filename="backtest_contributions"
        ),
        "trade_weights": backtest.visualize(
            chart="trade_weights", filename="backtest_trade_weights"
        ),
    }
    reset_example_visuals()
    return {name: type(figure).__name__ for name, figure in figures.items()} | {
        "output_directory": str(output_directory)
    }


def run() -> None:
    """Run the deterministic portfolio backtesting example."""
    allocator = build_allocator()
    allocator_backtest = run_core_backtest(allocator)
    functional_backtest = run_functional_backtest()
    print_mapping("Allocator backtest summary", allocator_backtest.summary())
    print_mapping("Functional backtest summary", functional_backtest.summary())
    print_mapping("Backtest cost summary", allocator_backtest.cost_summary())
    print_frame("Backtest monthly return table", allocator_backtest.return_table())
    print_frame("Backtest drawdown events", allocator_backtest.drawdown_events(top=3))
    print_frame("Backtest contribution summary", allocator_backtest.contribution_summary())
    print_frame("Backtest trade summary", allocator_backtest.trade_summary())
    print_frame("Backtest rolling metrics", allocator_backtest.rolling_metrics(window=4).tail())
    try:
        print_mapping(
            "Created backtest figures", create_backtest_visualizations(allocator_backtest)
        )
    except aq.VisualizationError as exc:
        print(f"Visualization skipped: {exc}")


if __name__ == "__main__":
    run()
