abaquant.derivatives.models.nig
===============================

**Import path:** ``abaquant.derivatives.models.nig``

**Domain:** Derivative pricing, simulation, calibration, diagnostics, and strategy analysis.

Purpose
-------

Normal-inverse-Gaussian option pricing model.

When to use it
--------------

This module implements or supports one derivative model. Read the parameter constraints, pricing measure, numerical method, and limiting cases before comparing outputs across models.

Public objects
--------------

* **class:** ``NormalInverseGaussianModel`` — Normal-inverse-Gaussian process model for European option valuation.
  * ``NormalInverseGaussianModel.characteristic_function`` — Evaluate the model characteristic function at the supplied Fourier argument.
  * ``NormalInverseGaussianModel.call_price`` — Return the model price of a European call option.
  * ``NormalInverseGaussianModel.put_price`` — Return the model price of a European put option.
  * ``NormalInverseGaussianModel.implied_vol`` — Return the Black--Scholes--Merton implied volatility associated with the model price.
  * ``NormalInverseGaussianModel.vol_smile`` — Evaluate the model-implied volatility across the supplied strike grid.
  * ``NormalInverseGaussianModel.visualize`` — Return a backend-native visualization of this option-pricing model.

Detailed reference
------------------

.. automodule:: abaquant.derivatives.models.nig
   :members:
   :show-inheritance:
   :member-order: bysource
