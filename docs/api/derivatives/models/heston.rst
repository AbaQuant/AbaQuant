abaquant.derivatives.models.heston
==================================

**Import path:** ``abaquant.derivatives.models.heston``

**Domain:** Derivative pricing, simulation, calibration, diagnostics, and strategy analysis.

Purpose
-------

Heston stochastic-volatility option pricing model.

When to use it
--------------

This module implements or supports one derivative model. Read the parameter constraints, pricing measure, numerical method, and limiting cases before comparing outputs across models.

Public objects
--------------

* **class:** ``HestonStochasticVolatilityModel`` — Heston stochastic-volatility model for European options.
  * ``HestonStochasticVolatilityModel.call_price`` — Return the model price of a European call option.
  * ``HestonStochasticVolatilityModel.put_price`` — Return the model price of a European put option.
  * ``HestonStochasticVolatilityModel.vol_smile`` — Evaluate the model-implied volatility across the supplied strike grid.
  * ``HestonStochasticVolatilityModel.visualize`` — Return a backend-native visualization of this option-pricing model.

Detailed reference
------------------

.. automodule:: abaquant.derivatives.models.heston
   :members:
   :show-inheritance:
   :member-order: bysource
