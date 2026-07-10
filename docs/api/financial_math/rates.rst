abaquant.financial_math.rates
=============================

**Import path:** ``abaquant.financial_math.rates``

**Domain:** Time-value, actuarial, fixed-income, corporate-finance, and portfolio mathematics.

Purpose
-------

Interest-rate conversion and reinvestment calculations.

When to use it
--------------

Use these functions for deterministic calculations where explicit cash-flow, rate, compounding, sign, and annualization conventions matter.

Public objects
--------------

* **function:** ``nominal_to_effective_rate`` — Convert a nominal annual rate to an effective annual rate.
* **function:** ``effective_to_nominal_rate`` — Convert an effective annual rate to a nominal annual rate.
* **function:** ``nominal_to_continuous_rate`` — Convert a nominal annual rate to a constant force of interest.
* **function:** ``continuous_to_effective_rate`` — Convert a constant force of interest to an effective annual rate.
* **function:** ``continuous_to_nominal_rate`` — Convert a constant force of interest to a nominal annual rate.
* **function:** ``convert_nominal_frequency`` — Convert a nominal annual rate between compounding frequencies.
* **function:** ``reinvestment_table`` — Build the deterministic year-by-year reinvestment table.

Detailed reference
------------------

.. automodule:: abaquant.financial_math.rates
   :members:
   :show-inheritance:
   :member-order: bysource
