"""Portfolio-optimization examples with separated allocation families."""

from __future__ import annotations

import numpy as np
import pandas as pd

import abaquant as aq
from examples._shared.output import (
    configure_example_visuals,
    print_mapping,
    print_section,
    reset_example_visuals,
)
from examples._shared.sample_data import sample_prices, sample_returns


def build_allocator() -> aq.PortfolioAllocator:
    """Create the core allocator from deterministic periodic returns."""
    return aq.PortfolioAllocator(sample_returns(), annual_risk_free_rate=0.02)


def calculate_allocation_families(allocator: aq.PortfolioAllocator) -> dict[str, object]:
    """Run mean-variance, risk-based, and downside-risk allocations."""
    return {
        "equal_weight": allocator.mean_variance.equal_weight(),
        "minimum_variance": allocator.mean_variance.minimum_variance(),
        "maximum_sharpe": allocator.mean_variance.maximum_sharpe(),
        "risk_parity": allocator.risk_based.risk_parity(),
        "inverse_volatility": allocator.risk_based.inverse_volatility(),
        "minimum_cvar": allocator.downside_risk.minimum_cvar(alpha=0.05),
    }


def summarize_allocations(allocations: dict[str, object]) -> dict[str, float]:
    """Extract one compact value from each allocation result."""
    summary = {}
    for name, result in allocations.items():
        weights = getattr(result, "weights", result)
        if hasattr(weights, "iloc"):
            summary[f"{name}_alpha_weight"] = float(weights.iloc[0])
        else:
            summary[f"{name}_alpha_weight"] = float(np.asarray(weights)[0])
    return summary


def calculate_frontier_and_risk() -> dict[str, object]:
    """Create frontier, Monte Carlo, and risk-metric summaries."""
    returns = sample_returns()
    mean_returns = returns.mean() * 252
    covariance = returns.cov() * 252
    frontier = aq.markowitz_frontier(mean_returns, covariance, n_points=8)
    cloud = aq.monte_carlo_portfolios(mean_returns, covariance, n_portfolios=250, rf=0.02, seed=42)
    weights = np.array([0.4, 0.35, 0.25])
    portfolio_series = aq.portfolio_returns(returns, weights)
    metrics = aq.compute_all_metrics(portfolio_series, rf=0.02)
    return {
        "frontier_rows": len(frontier),
        "cloud_rows": len(cloud),
        "sharpe_ratio": metrics["Sharpe Ratio"],
        "max_drawdown": metrics["Max Drawdown"],
    }


def run_backtest_and_stress_tests() -> dict[str, object]:
    """Run compact backtest and stress-test examples on synthetic prices."""
    prices = sample_prices()
    backtest = aq.run_backtest(
        prices, strategy_name="equal_weight", rebalance_freq="monthly", lookback_days=8
    )
    weights = pd.Series([0.4, 0.35, 0.25], index=prices.columns)
    stress = aq.run_all_scenarios(prices, weights)
    return {
        "backtest_available": backtest is not None,
        "stress_scenarios": len(stress),
    }


def create_portfolio_visualizations(
    allocator: aq.PortfolioAllocator, allocations: dict[str, object]
) -> dict[str, str]:
    """Create and save portfolio weights, path, and correlation charts."""
    output_directory = configure_example_visuals(subdirectory="portfolio_optimization")
    max_sharpe_weights = allocations["maximum_sharpe"]
    figures = {
        "weights": allocator.visualize(
            weights=max_sharpe_weights, chart="weights", filename="maximum_sharpe_weights"
        ),
        "cumulative_returns": allocator.visualize(
            weights=max_sharpe_weights,
            chart="cumulative_returns",
            filename="portfolio_cumulative_returns",
        ),
        "correlation": allocator.visualize(chart="correlation", filename="asset_correlation"),
    }
    reset_example_visuals()
    return {name: type(figure).__name__ for name, figure in figures.items()} | {
        "output_directory": str(output_directory)
    }


def run() -> None:
    """Run portfolio optimization and visualization examples."""
    allocator = build_allocator()
    allocations = calculate_allocation_families(allocator)
    print_mapping("Allocation family summary", summarize_allocations(allocations))
    print_section("Frontier and risk diagnostics")
    for key, value in calculate_frontier_and_risk().items():
        print(f"{key}: {value}")
    print_mapping("Backtest and stress tests", run_backtest_and_stress_tests())
    try:
        print_mapping(
            "Created portfolio figures", create_portfolio_visualizations(allocator, allocations)
        )
    except aq.VisualizationError as exc:
        print(f"Visualization skipped: {exc}")


if __name__ == "__main__":
    run()
