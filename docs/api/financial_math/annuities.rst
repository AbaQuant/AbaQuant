abaquant.financial_math.annuities
=================================

**Import path:** ``abaquant.financial_math.annuities``

**Domain:** Time-value, actuarial, fixed-income, corporate-finance, and portfolio mathematics.

Purpose
-------

Annuity, perpetuity, and gradient cash-flow valuation.

When to use it
--------------

Use these functions for deterministic calculations where explicit cash-flow, rate, compounding, sign, and annualization conventions matter.

Public objects
--------------

* **function:** ``effective_annuity_future_value`` — Compute accumulated value of a level annuity under an effective period rate.
* **function:** ``nominal_annuity_future_value`` — Compute accumulated value of a level annuity under nominal compounding.
* **function:** ``continuous_annuity_future_value`` — Compute accumulated value of a continuous cash-flow annuity.
* **function:** ``effective_annuity_present_value`` — Compute present value of a level annuity under an effective period rate.
* **function:** ``nominal_annuity_present_value`` — Compute present value of a level annuity under nominal compounding.
* **function:** ``continuous_annuity_present_value`` — Compute present value of a continuous cash-flow annuity.
* **function:** ``perpetuity_present_value`` — Compute the present value of a level perpetuity.
* **function:** ``geometric_gradient_future_value`` — Compute accumulated value of a geometric-gradient payment stream.
* **function:** ``geometric_gradient_present_value`` — Compute present value of a geometric-gradient payment stream.
* **function:** ``periods_for_annuity_future_value`` — Solve the period count for a level-annuity accumulated-value target.
* **function:** ``periods_for_annuity_present_value`` — Solve the period count for a level-annuity present-value target.
* **function:** ``periods_for_geometric_gradient_future_value`` — Solve the period count for a geometric-gradient accumulated-value target.
* **function:** ``periods_for_geometric_gradient_present_value`` — Solve the period count for a geometric-gradient present-value target.
* **function:** ``arithmetic_gradient_present_value`` — Compute present value of an arithmetic-gradient payment stream.
* **function:** ``arithmetic_gradient_future_value`` — Compute accumulated value of an arithmetic-gradient payment stream.
* **function:** ``periods_for_arithmetic_gradient_future_value`` — Solve the period count for an arithmetic-gradient accumulated-value target.
* **function:** ``periods_for_arithmetic_gradient_present_value`` — Solve the period count for an arithmetic-gradient present-value target.

Detailed reference
------------------

.. automodule:: abaquant.financial_math.annuities
   :members:
   :show-inheritance:
   :member-order: bysource
