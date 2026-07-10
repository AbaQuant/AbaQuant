abaquant.derivatives.analytics.parity
=====================================

**Import path:** ``abaquant.derivatives.analytics.parity``

**Domain:** Derivative pricing, simulation, calibration, diagnostics, and strategy analysis.

Purpose
-------

Parity and deterministic option-pricing analytics.

When to use it
--------------

This module computes derived diagnostics from prices, returns, or model outputs. Ensure inputs use the frequency and units stated by each function.

Public objects
--------------

* **function:** ``parity_check`` — Evaluate put--call parity and report the residual under continuous carry.
* **function:** ``intrinsic_time_value`` — Decompose an option premium into intrinsic value and non-negative time value.
* **function:** ``forward_price_continuous`` — Compute a continuously compounded cost-of-carry forward price.

Detailed reference
------------------

.. automodule:: abaquant.derivatives.analytics.parity
   :members:
   :show-inheritance:
   :member-order: bysource
