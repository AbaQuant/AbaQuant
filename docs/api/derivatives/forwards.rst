abaquant.derivatives.forwards
=============================

**Import path:** ``abaquant.derivatives.forwards``

**Domain:** Derivative pricing, simulation, calibration, diagnostics, and strategy analysis.

Purpose
-------

Forward, futures-style carry, foreign-exchange forward, and FRA valuation.

When to use it
--------------

Use this package when valuing contingent claims, calculating Greeks, building option strategies, simulating stochastic processes, or fitting models to market observations.

Public objects
--------------

* **function:** ``forward_price`` — Compute the no-arbitrage forward price under the stated carry convention.
* **function:** ``forward_price_with_yield`` — Compute a forward price with continuous or periodic yield carry.
* **function:** ``forward_contract_value`` — Compute the value of an existing long or short forward contract.
* **function:** ``simple_forward_price`` — Compute the forward price with financing carry only.
* **function:** ``forward_price_with_continuous_dividend`` — Compute an equity forward price with continuous dividend yield.
* **function:** ``forward_price_with_discrete_dividends`` — Compute an equity forward price after subtracting present-value discrete dividends.
* **function:** ``commodity_forward_price`` — Compute a commodity forward price with deterministic storage cost.
* **function:** ``fx_forward_price`` — Compute a foreign-exchange forward price from domestic and foreign rates.
* **function:** ``live_forward_value`` — Compute the current value of a forward with a fixed delivery price.
* **function:** ``fra`` — Value the forward-rate-agreement cash-flow relationship implemented by this routine.

Detailed reference
------------------

.. automodule:: abaquant.derivatives.forwards
   :members:
   :show-inheritance:
   :member-order: bysource
