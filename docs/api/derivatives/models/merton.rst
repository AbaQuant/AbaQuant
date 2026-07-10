abaquant.derivatives.models.merton
==================================

**Import path:** ``abaquant.derivatives.models.merton``

**Domain:** Derivative pricing, simulation, calibration, diagnostics, and strategy analysis.

Purpose
-------

Merton jump-diffusion option pricing model.

When to use it
--------------

This module implements or supports one derivative model. Read the parameter constraints, pricing measure, numerical method, and limiting cases before comparing outputs across models.

Public objects
--------------

* **class:** ``MertonJumpDiffusionModel`` — Merton jump-diffusion model for European vanilla options.
  * ``MertonJumpDiffusionModel.price`` — Return the model price of a call or put option.
  * ``MertonJumpDiffusionModel.call_price`` — Return the model price of a European call option.
  * ``MertonJumpDiffusionModel.put_price`` — Return the model price of a European put option.
  * ``MertonJumpDiffusionModel.vol_smile`` — Evaluate the model-implied volatility across the supplied strike grid.
  * ``MertonJumpDiffusionModel.visualize`` — Return a backend-native visualization of this option-pricing model.
* **function:** ``merton_jump_statistics`` — Compute summary statistics implied by the Merton jump-diffusion parameters.

Detailed reference
------------------

.. automodule:: abaquant.derivatives.models.merton
   :members:
   :show-inheritance:
   :member-order: bysource
