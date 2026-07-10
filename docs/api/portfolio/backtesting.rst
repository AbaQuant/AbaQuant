abaquant.portfolio.backtesting
==============================

**Import path:** ``abaquant.portfolio.backtesting``

**Domain:** Portfolio construction, optimization, backtesting, risk metrics, and stress testing.

Purpose
-------

Deterministic portfolio backtesting with transparent periodic rebalancing.

When to use it
--------------

Use this package to transform return histories and covariance estimates into weights, then evaluate those weights out of sample and under explicit scenarios.

Public objects
--------------

* **class:** ``PortfolioBacktestResult`` — Result of a deterministic periodically rebalanced portfolio backtest.
  * ``PortfolioBacktestResult.equity_curve`` — Return the simulated portfolio value path.
  * ``PortfolioBacktestResult.returns`` — Return realized periodic portfolio returns after transaction costs.
  * ``PortfolioBacktestResult.drawdowns`` — Return realized portfolio drawdowns.
  * ``PortfolioBacktestResult.benchmark_returns`` — Return benchmark returns when a benchmark was supplied.
  * ``PortfolioBacktestResult.benchmark_equity_curve`` — Return the benchmark value path when a benchmark was supplied.
  * ``PortfolioBacktestResult.active_returns`` — Return strategy returns minus benchmark returns when available.
  * ``PortfolioBacktestResult.summary`` — Return scalar performance, risk, benchmark, turnover, and cost diagnostics.
  * ``PortfolioBacktestResult.benchmark_summary`` — Return benchmark-relative statistics when a benchmark is available.
  * ``PortfolioBacktestResult.rolling_metrics`` — Return rolling annualized return, volatility, Sharpe, Sortino, and drawdown metrics.
  * ``PortfolioBacktestResult.monthly_returns`` — Return calendar-month compounded strategy returns.
  * ``PortfolioBacktestResult.annual_returns`` — Return calendar-year compounded strategy returns.
  * ``PortfolioBacktestResult.return_table`` — Return a year-by-month table of compounded strategy returns.
  * ``PortfolioBacktestResult.drawdown_events`` — Return the largest drawdown episodes sorted by trough drawdown.
  * ``PortfolioBacktestResult.contribution_summary`` — Return asset-level cumulative contribution and share diagnostics.
  * ``PortfolioBacktestResult.trade_summary`` — Return rebalance-date turnover, cost, and largest-trade diagnostics.
  * ``PortfolioBacktestResult.cost_summary`` — Return transaction-cost totals and averages.
  * ``PortfolioBacktestResult.as_frame`` — Return a compact tabular summary of the simulated path.
  * ``PortfolioBacktestResult.to_frame`` — Alias for :meth:'as_frame' for pandas-style workflows.
  * ``PortfolioBacktestResult.report`` — Return an exportable report for this portfolio backtest result.
  * ``PortfolioBacktestResult.visualize`` — Return a figure for a backtest diagnostic.
* **function:** ``rebalance_dates`` — Select the first available observation in each rebalance period.
* **function:** ``coerce_backtest_weights`` — Validate and align a target-weight specification.
* **function:** ``inverse_volatility_weights`` — Return inverse-volatility weights estimated from a historical return window.
* **function:** ``run_rebalanced_backtest`` — Run a deterministic periodically rebalanced portfolio backtest.
* **function:** ``run_backtest`` — Run the legacy dictionary backtest wrapper with English labels.

Detailed reference
------------------

.. automodule:: abaquant.portfolio.backtesting
   :members:
   :show-inheritance:
   :member-order: bysource
