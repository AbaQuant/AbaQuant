abaquant.derivatives.models.black_scholes
=========================================

**Import path:** ``abaquant.derivatives.models.black_scholes``

**Domain:** Derivative pricing, simulation, calibration, diagnostics, and strategy analysis.

Purpose
-------

Black--Scholes--Merton analytical option pricing model.

When to use it
--------------

This module implements or supports one derivative model. Read the parameter constraints, pricing measure, numerical method, and limiting cases before comparing outputs across models.

Public objects
--------------

* **class:** ``BlackScholesMertonModel`` — Analytical Black--Scholes--Merton model for European vanilla options.
  * ``BlackScholesMertonModel.call_price`` — Return the model price of a European call option.
  * ``BlackScholesMertonModel.put_price`` — Return the model price of a European put option.
  * ``BlackScholesMertonModel.greeks`` — Return the model sensitivities implemented by this model.
  * ``BlackScholesMertonModel.implied_vol`` — Return the Black--Scholes--Merton implied volatility associated with the model price.
  * ``BlackScholesMertonModel.vol_smile_surface`` — Evaluate the model-implied volatility across strike and maturity grids.
  * ``BlackScholesMertonModel.visualize`` — Return a backend-native visualization of this option-pricing model.
* **function:** ``bsm_d1_d2_summary`` — Compute the result defined by ''bsm_d1_d2_summary'' under this module's documented convention.

Detailed reference
------------------

.. automodule:: abaquant.derivatives.models.black_scholes
   :members:
   :show-inheritance:
   :member-order: bysource
