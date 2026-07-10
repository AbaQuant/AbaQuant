abaquant.derivatives.models.sabr
================================

**Import path:** ``abaquant.derivatives.models.sabr``

**Domain:** Derivative pricing, simulation, calibration, diagnostics, and strategy analysis.

Purpose
-------

SABR implied-volatility approximation and option pricing.

When to use it
--------------

This module implements or supports one derivative model. Read the parameter constraints, pricing measure, numerical method, and limiting cases before comparing outputs across models.

Public objects
--------------

* **class:** ``SABRVolatilityModel`` — SABR implied-volatility model using the Hagan approximation.
  * ``SABRVolatilityModel.implied_vol`` — Return the Black--Scholes--Merton implied volatility associated with the model price.
  * ``SABRVolatilityModel.call_price`` — Return the model price of a European call option.
  * ``SABRVolatilityModel.put_price`` — Return the model price of a European put option.
  * ``SABRVolatilityModel.vol_smile`` — Evaluate the model-implied volatility across the supplied strike grid.
  * ``SABRVolatilityModel.visualize`` — Return a backend-native visualization of this option-pricing model.

Detailed reference
------------------

.. automodule:: abaquant.derivatives.models.sabr
   :members:
   :show-inheritance:
   :member-order: bysource
