# Backtesting Layer Report

## Summary

This release adds a compact deterministic portfolio backtesting layer to AbaQuant.
It is intentionally not an event-driven trading simulator. It evaluates periodic
simple return panels, applies transparent target weights, rebalances on a fixed
calendar schedule, and reports performance, drawdown, turnover, and transaction
cost diagnostics.

## Public API

```python
from abaquant.portfolio import PortfolioAllocator, run_rebalanced_backtest

allocator = PortfolioAllocator(returns, annual_risk_free_rate=0.02)
backtest = allocator.backtest(
    weights="equal_weight",
    rebalance="monthly",
    transaction_cost_bps=5,
    initial_capital=100_000,
)

backtest.equity_curve()
backtest.drawdowns()
backtest.summary()
backtest.visualize(chart="equity_curve")
backtest.visualize(chart="drawdown")
backtest.visualize(chart="weights")
backtest.visualize(chart="turnover")
```

`UniversePortfolioAnalytics.backtest(...)` provides the same workflow for
market-data universes by requesting aligned return panels through the existing
universe history namespace.

## Metrics

The summary contains:

- CAGR
- annualized volatility
- Sharpe ratio
- Sortino ratio
- maximum drawdown
- Calmar ratio
- total turnover
- average turnover
- transaction-cost drag
- total transaction cost
- ending value

## Spanish-to-English cleanup

Spanish prose and user-facing labels in source, examples, tests, and generated
fixtures were translated to English. The CDS output schema, frontier labels,
portfolio strategy labels, stress-scenario names, and risk-metric labels now use
English names.

## Validation

- `python -m compileall -q src examples tests scripts`: passed
- `python scripts/check_documentation.py`: passed
- `python -m pytest -q tests`: passed (`241 passed`)
- `python examples/00_import_all_public_modules.py`: passed
- `python examples/19_portfolio_backtesting.py`: passed
- `python examples/run_all_deterministic_examples.py`: passed
- `python examples/run_all_visual_examples.py`: passed
