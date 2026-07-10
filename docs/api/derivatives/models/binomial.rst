abaquant.derivatives.models.binomial
====================================

**Import path:** ``abaquant.derivatives.models.binomial``

**Domain:** Derivative pricing, simulation, calibration, diagnostics, and strategy analysis.

Purpose
-------

Cox--Ross--Rubinstein binomial-tree option pricing.

When to use it
--------------

This module implements or supports one derivative model. Read the parameter constraints, pricing measure, numerical method, and limiting cases before comparing outputs across models.

Public objects
--------------

* **class:** ``CoxRossRubinsteinModel`` — Recombining Cox--Ross--Rubinstein lattice model for vanilla options.
  * ``CoxRossRubinsteinModel.price`` — Return the model price of a call or put option.
  * ``CoxRossRubinsteinModel.call_price`` — Return the model price of a European call option.
  * ``CoxRossRubinsteinModel.put_price`` — Return the model price of a European put option.
  * ``CoxRossRubinsteinModel.full_tree`` — Return the displayed portion of the recombining binomial valuation tree.
  * ``CoxRossRubinsteinModel.delta`` — Estimate option delta from the first binomial-tree step.
  * ``CoxRossRubinsteinModel.visualize`` — Return a backend-native visualization of this option-pricing model.
* **function:** ``crr_tree_parameters`` — Compute Cox--Ross--Rubinstein step parameters.

Detailed reference
------------------

.. automodule:: abaquant.derivatives.models.binomial
   :members:
   :show-inheritance:
   :member-order: bysource
