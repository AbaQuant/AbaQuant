abaquant.financial_math.tvm
===========================

**Import path:** ``abaquant.financial_math.tvm``

**Domain:** Time-value, actuarial, fixed-income, corporate-finance, and portfolio mathematics.

Purpose
-------

Time-value-of-money primitives.

When to use it
--------------

Use these functions for deterministic calculations where explicit cash-flow, rate, compounding, sign, and annualization conventions matter.

Public objects
--------------

* **function:** ``future_value`` — Compute the accumulated value of a present amount.
* **function:** ``continuous_future_value`` — Compute accumulated value under a constant force of interest.
* **function:** ``present_value`` — Compute the discounted value of a future amount.
* **function:** ``continuous_present_value`` — Compute discounted value under a constant force of interest.
* **function:** ``number_of_periods`` — Solve for the number of compounding periods needed to reach a target amount.
* **function:** ``rate_of_return`` — Solve for the effective periodic return implied by two values and a horizon.
* **function:** ``decompose_periods`` — Decompose a real-valued period count into its implemented representation.

Detailed reference
------------------

.. automodule:: abaquant.financial_math.tvm
   :members:
   :show-inheritance:
   :member-order: bysource
