Portfolio analytics
===================

The ``abaquant.portfolio`` namespace provides allocation, risk metrics,
efficient frontiers, rebalanced backtests, stress testing, and scenario
analysis.

Input data
----------

Most high-level workflows start from a pandas ``DataFrame`` of periodic
returns:

.. code:: python

   import pandas as pd
   from abaquant.portfolio import PortfolioAllocator

   returns = pd.DataFrame(
       {
           "ALPHA": [0.01, -0.002, 0.006, 0.004],
           "BETA": [0.003, 0.005, -0.001, 0.002],
           "GAMMA": [-0.002, 0.007, 0.004, 0.006],
       }
   )
   allocator = PortfolioAllocator(returns, annual_risk_free_rate=0.02)

Rows are time observations. Columns are assets.

Allocation families
-------------------

.. code:: python

   allocations = {
       "equal_weight": allocator.mean_variance.equal_weight(),
       "minimum_variance": allocator.mean_variance.minimum_variance(),
       "maximum_sharpe": allocator.mean_variance.maximum_sharpe(),
       "risk_parity": allocator.risk_based.risk_parity(),
       "inverse_volatility": allocator.risk_based.inverse_volatility(),
       "minimum_cvar": allocator.downside_risk.minimum_cvar(alpha=0.05),
   }

+-----------------------+-----------------------+-----------------------+
| Family                | Methods               | Objective             |
+=======================+=======================+=======================+
| Mean-variance         | equal weight, min     | Optimize              |
|                       | variance, max Sharpe, | return/variance       |
|                       | max return            | tradeoff.             |
+-----------------------+-----------------------+-----------------------+
| Risk-based            | risk parity, inverse  | Allocate by risk      |
|                       | vol, inverse          | contribution or       |
|                       | variance, max         | covariance geometry.  |
|                       | diversification, HRP  |                       |
+-----------------------+-----------------------+-----------------------+
| Downside-risk         | min CVaR, min CDaR,   | Focus on drawdown or  |
|                       | max Sortino, max      | lower-tail outcomes.  |
|                       | Calmar, max Omega     |                       |
+-----------------------+-----------------------+-----------------------+

Efficient frontier
------------------

.. code:: python

   from abaquant.portfolio import markowitz_frontier, monte_carlo_portfolios

   mean_returns = returns.mean() * 252
   covariance = returns.cov() * 252
   frontier = markowitz_frontier(mean_returns, covariance, n_points=25)
   cloud = monte_carlo_portfolios(mean_returns, covariance, n_portfolios=1000, rf=0.02, seed=42)

The Markowitz frontier solves constrained mean-variance problems across
return targets. Monte Carlo portfolios sample feasible weights and
evaluate risk/return profiles.

Risk metrics
------------

.. code:: python

   from abaquant.portfolio import portfolio_returns, compute_all_metrics

   weights = [0.4, 0.35, 0.25]
   series = portfolio_returns(returns, weights)
   metrics = compute_all_metrics(series, rf=0.02)

Common metrics include:

===================== =============================================
Metric                Interpretation
===================== =============================================
Annualized return     Compounded or scaled return estimate.
Annualized volatility Scaled standard deviation of returns.
Sharpe ratio          Excess return per unit of total volatility.
Sortino ratio         Excess return per unit of downside deviation.
Max drawdown          Worst peak-to-trough decline.
Calmar ratio          Return divided by max drawdown magnitude.
Historical VaR/CVaR   Empirical tail-loss thresholds.
CDaR                  Conditional drawdown-at-risk.
===================== =============================================

Backtesting
-----------

.. code:: python

   backtest = allocator.backtest(
       weights="inverse_volatility",
       rebalance="monthly",
       transaction_cost_bps=5.0,
       slippage_bps=1.0,
       benchmark="equal_weight",
       lookback=10,
   )

   summary = backtest.summary()
   equity_curve = backtest.equity_curve
   report = backtest.report()

Backtests are deterministic historical simulations. They model
rebalancing, turnover, transaction costs, slippage, benchmark
comparison, rolling metrics, and drawdowns.

Stress testing
--------------

.. code:: python

   from abaquant.portfolio import run_all_scenarios

   stress = run_all_scenarios(prices, weights)

Stress testing applies predefined or custom shocks to estimate portfolio
sensitivity under adverse scenarios.

Visualization
-------------

.. code:: python

   fig = allocator.visualize(chart="correlation")
   fig = allocator.visualize(weights=allocations["maximum_sharpe"], chart="weights")

Backtest objects also expose visualization methods for equity curves,
drawdowns, rolling metrics, calendar returns, and contribution
diagnostics.

Failure modes
-------------

Portfolio outputs are highly sensitive to:

-  expected-return estimation error;
-  covariance estimation error;
-  short history length;
-  unstable correlation regimes;
-  constraints and bounds;
-  transaction-cost assumptions;
-  sampling frequency;
-  survivorship and look-ahead bias in input data.
