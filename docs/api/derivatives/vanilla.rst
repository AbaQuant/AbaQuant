abaquant.derivatives.vanilla
============================

**Import path:** ``abaquant.derivatives.vanilla``

**Domain:** Derivative pricing, simulation, calibration, diagnostics, and strategy analysis.

Purpose
-------

Vanilla option pricing and Greeks under Black--Scholes--Merton and Black--76.

When to use it
--------------

Use this package when valuing contingent claims, calculating Greeks, building option strategies, simulating stochastic processes, or fitting models to market observations.

Public objects
--------------

* **function:** ``bsm_option_prices`` — Compute Black--Scholes-style call and put prices and the intermediate d statistics.
* **function:** ``bsm_greeks`` — Compute first-order Black--Scholes-style Greeks for calls and puts.
* **function:** ``black_scholes`` — Price a European option under the Black--Scholes--Merton model.
* **function:** ``vanilla_intrinsic_value`` — Return the immediate-exercise value of a vanilla option.
* **function:** ``vanilla_extrinsic_value`` — Return option value in excess of immediate-exercise value.
* **function:** ``black_76`` — Price a European option on a forward or futures price under Black--76.
* **function:** ``bsm_d1_d2`` — Compute the Black--Scholes--Merton d1 and d2 statistics.
* **function:** ``calculate_greeks`` — Return the standard Black--Scholes--Merton Greeks for one option type.
* **function:** ``second_order_greeks`` — Compute selected second-order Black--Scholes--Merton sensitivity measures.
* **function:** ``implied_volatility_bsm`` — Solve for Black--Scholes--Merton implied volatility with Brent root finding.

Detailed reference
------------------

.. automodule:: abaquant.derivatives.vanilla
   :members:
   :show-inheritance:
   :member-order: bysource
