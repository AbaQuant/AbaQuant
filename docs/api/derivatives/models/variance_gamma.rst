abaquant.derivatives.models.variance_gamma
==========================================

**Import path:** ``abaquant.derivatives.models.variance_gamma``

**Domain:** Derivative pricing, simulation, calibration, diagnostics, and strategy analysis.

Purpose
-------

Variance-Gamma option pricing model.

When to use it
--------------

This module implements or supports one derivative model. Read the parameter constraints, pricing measure, numerical method, and limiting cases before comparing outputs across models.

Public objects
--------------

* **class:** ``VarianceGammaProcessModel`` — Variance-gamma process model for European option valuation.
  * ``VarianceGammaProcessModel.characteristic_function`` — Evaluate the model characteristic function at the supplied Fourier argument.
  * ``VarianceGammaProcessModel.call_price`` — Return the model price of a European call option.
  * ``VarianceGammaProcessModel.put_price`` — Return the model price of a European put option.
  * ``VarianceGammaProcessModel.implied_vol`` — Return the Black--Scholes--Merton implied volatility associated with the model price.
  * ``VarianceGammaProcessModel.vol_smile`` — Evaluate the model-implied volatility across the supplied strike grid.
  * ``VarianceGammaProcessModel.visualize`` — Return a backend-native visualization of this option-pricing model.

Detailed reference
------------------

.. automodule:: abaquant.derivatives.models.variance_gamma
   :members:
   :show-inheritance:
   :member-order: bysource
