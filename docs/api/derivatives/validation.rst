abaquant.derivatives.validation
===============================

**Import path:** ``abaquant.derivatives.validation``

**Domain:** Derivative pricing, simulation, calibration, diagnostics, and strategy analysis.

Purpose
-------

Input-validation helpers for advanced derivatives.

When to use it
--------------

Centralizes input validation and error messages used by public calculations. Use this package when valuing contingent claims, calculating Greeks, building option strategies, simulating stochastic processes, or fitting models to market observations.

Public objects
--------------

* **function:** ``validate_positive`` — Require a strictly positive numeric input.
* **function:** ``validate_nonnegative`` — Require a numeric input greater than or equal to zero.
* **function:** ``validate_between`` — Require a numeric input to lie strictly inside an open interval.
* **function:** ``validate_positive_integer`` — Require a positive integer input.
* **function:** ``validate_option_type`` — Require an option type supported by vanilla call/put routines.

Detailed reference
------------------

.. automodule:: abaquant.derivatives.validation
   :members:
   :show-inheritance:
   :member-order: bysource
