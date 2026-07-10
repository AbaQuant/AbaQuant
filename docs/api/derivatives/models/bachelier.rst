abaquant.derivatives.models.bachelier
=====================================

**Import path:** ``abaquant.derivatives.models.bachelier``

**Domain:** Derivative pricing, simulation, calibration, diagnostics, and strategy analysis.

Purpose
-------

Bachelier normal-volatility option pricing.

When to use it
--------------

This module implements or supports one derivative model. Read the parameter constraints, pricing measure, numerical method, and limiting cases before comparing outputs across models.

Public objects
--------------

* **class:** ``NormalBachelierModel`` — Bachelier normal-volatility model for European vanilla options.
  * ``NormalBachelierModel.call_price`` — Return the model price of a European call option.
  * ``NormalBachelierModel.put_price`` — Return the model price of a European put option.
  * ``NormalBachelierModel.greeks`` — Return the model sensitivities implemented by this model.
  * ``NormalBachelierModel.implied_normal_vol`` — Return the Bachelier normal implied volatility associated with the model price.
  * ``NormalBachelierModel.lognormal_vol`` — Compute the result defined by ''lognormal_vol'' under this module's documented convention.
  * ``NormalBachelierModel.vol_smile`` — Evaluate the model-implied volatility across the supplied strike grid.
  * ``NormalBachelierModel.visualize`` — Return a backend-native visualization of this option-pricing model.

Detailed reference
------------------

.. automodule:: abaquant.derivatives.models.bachelier
   :members:
   :show-inheritance:
   :member-order: bysource
