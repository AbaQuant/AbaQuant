abaquant.financial_math.corporate
=================================

**Import path:** ``abaquant.financial_math.corporate``

**Domain:** Time-value, actuarial, fixed-income, corporate-finance, and portfolio mathematics.

Purpose
-------

Corporate-finance valuation, CAPM, and discounted-cash-flow helpers.

When to use it
--------------

Use these functions for deterministic calculations where explicit cash-flow, rate, compounding, sign, and annualization conventions matter.

Public objects
--------------

* **function:** ``capm_cost_of_equity`` — Compute the CAPM required return on equity.
* **function:** ``weighted_average_cost_of_capital`` — Compute after-tax weighted average cost of capital.
* **function:** ``dcf_valuation`` — Estimate enterprise and equity value from a deterministic discounted-cash-flow model.
* **function:** ``dcf_sensitivity_matrix`` — Evaluate DCF output across terminal-growth and discount-rate scenarios.
* **function:** ``beta_alpha_from_returns`` — Estimate beta and alpha from paired asset and market return series.

Detailed reference
------------------

.. automodule:: abaquant.financial_math.corporate
   :members:
   :show-inheritance:
   :member-order: bysource
