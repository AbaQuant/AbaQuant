abaquant.portfolio.solvers
==========================

**Import path:** ``abaquant.portfolio.solvers``

**Domain:** Portfolio construction, optimization, backtesting, risk metrics, and stress testing.

Purpose
-------

Shared constrained numerical solvers for portfolio weights.

When to use it
--------------

Use this package to transform return histories and covariance estimates into weights, then evaluate those weights out of sample and under explicit scenarios.

Public objects
--------------

* **function:** ``normalize_weights`` — Clip weights to bounds and normalize them to sum to one.
* **function:** ``solve_slsqp_weights`` — Solve a constrained portfolio-weight problem using SciPy SLSQP.

Detailed reference
------------------

.. automodule:: abaquant.portfolio.solvers
   :members:
   :show-inheritance:
   :member-order: bysource
