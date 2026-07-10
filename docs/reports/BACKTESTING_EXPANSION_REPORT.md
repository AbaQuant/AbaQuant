# AbaQuant backtesting expansion report

This update expands the simple deterministic backtesting layer into a richer but still transparent portfolio-analysis workflow.

## Added capabilities

- Rebalance schedules: `none`, `daily`, `weekly`, `monthly`, `quarterly`, and `annual`.
- Weight policies: static custom weights, `equal_weight`, `buy_and_hold`, `inverse_volatility`, and callable policies.
- Explicit transaction modeling: transaction-cost basis points, slippage basis points, and fixed rebalance costs.
- Benchmark support: benchmark returns from an equal-weight portfolio, custom benchmark weights, or a precomputed pandas Series.
- Extended summaries: total return, CAGR, annualized return, volatility, downside deviation, Sharpe, Sortino, Calmar, Omega, VaR, CVaR, skewness, kurtosis, win rate, best/worst return, turnover, costs, beta, alpha, tracking error, information ratio, capture ratios, and benchmark hit rate.
- Path diagnostics: equity curve, returns, drawdowns, active returns, benchmark equity, transaction-cost series, turnover series, target weights, drifted weights, trade weights, and asset return contributions.
- Analysis methods: `rolling_metrics()`, `monthly_returns()`, `annual_returns()`, `return_table()`, `drawdown_events()`, `contribution_summary()`, `trade_summary()`, `cost_summary()`, `benchmark_summary()`, `as_frame()`, and `to_frame()`.
- Visualizations: `equity_curve`, `benchmark`, `drawdown`, `weights`, `turnover`, `transaction_costs`, `rolling_sharpe`, `rolling_volatility`, `return_heatmap`, `contributions`, and `trade_weights`.

## Example usage

```python
from abaquant.portfolio import PortfolioAllocator

allocator = PortfolioAllocator(returns, annual_risk_free_rate=0.02)

backtest = allocator.backtest(
    weights="inverse_volatility",
    rebalance="monthly",
    transaction_cost_bps=5,
    slippage_bps=1,
    fixed_transaction_cost=1,
    initial_capital=100_000,
    benchmark="equal_weight",
    lookback=63,
)

summary = backtest.summary()
rolling = backtest.rolling_metrics(window=63)
return_table = backtest.return_table()
drawdowns = backtest.drawdown_events(top=5)
contributions = backtest.contribution_summary()
trades = backtest.trade_summary()

backtest.visualize(chart="benchmark")
backtest.visualize(chart="rolling_sharpe")
backtest.visualize(chart="return_heatmap")
```

## Compatibility notes

- The legacy `run_backtest(...)` wrapper remains available.
- `run_rebalanced_backtest(...)` remains the functional API and now returns the richer `PortfolioBacktestResult`.
- The implementation remains deterministic and close-to-close. It does not model intraday execution, taxes, financing, or market impact beyond the explicit slippage parameter.
