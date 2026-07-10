abaquant.derivatives.exotics
============================

**Import path:** ``abaquant.derivatives.exotics``

**Domain:** Derivative pricing, simulation, calibration, diagnostics, and strategy analysis.

Purpose
-------

Exotic-option formulas and closed-form approximations.

When to use it
--------------

Use this package when valuing contingent claims, calculating Greeks, building option strategies, simulating stochastic processes, or fitting models to market observations.

Public objects
--------------

* **function:** ``gap_options`` — Price a gap option under the Black--Scholes--Merton closed-form convention.
* **function:** ``cash_or_nothing_options`` — Price a cash-or-nothing digital option under Black--Scholes--Merton.
* **function:** ``asset_or_nothing_options`` — Price an asset-or-nothing digital option under Black--Scholes--Merton.
* **function:** ``down_and_out_barrier_option`` — Price the implemented down-and-out barrier option formula.
* **function:** ``arithmetic_asian_options`` — Price an arithmetic-average Asian option using the module approximation.
* **function:** ``geometric_asian_options`` — Price a geometric-average Asian option using its closed-form lognormal reduction.
* **function:** ``floating_lookback_options`` — Price the implemented floating-strike lookback option formula.
* **function:** ``compound_options`` — Price an option on an option using the implemented compound-option formula.
* **function:** ``exchange_options`` — Price an option to exchange one risky asset for another under the Margrabe-style formula.
* **function:** ``exotic_payoff_leg`` — Evaluate terminal payoff and profit for an exotic option leg.
* **function:** ``simple_chooser_option`` — Price a simple chooser option under the implemented Black--Scholes--Merton relation.
* **function:** ``perpetual_option`` — Price the implemented perpetual American-style option formula.

Detailed reference
------------------

.. automodule:: abaquant.derivatives.exotics
   :members:
   :show-inheritance:
   :member-order: bysource
