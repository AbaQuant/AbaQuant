abaquant.derivatives.models.diagnostics
=======================================

**Import path:** ``abaquant.derivatives.models.diagnostics``

**Domain:** Derivative pricing, simulation, calibration, diagnostics, and strategy analysis.

Purpose
-------

Scalar option diagnostics for AbaQuant pricing models.

When to use it
--------------

This module implements or supports one derivative model. Read the parameter constraints, pricing measure, numerical method, and limiting cases before comparing outputs across models.

Public objects
--------------

* **class:** ``DerivativeDiagnosticsReport`` — Computed scalar diagnostics for one vanilla derivative contract.
  * ``DerivativeDiagnosticsReport.as_dict`` — Return a plain dictionary representation of the diagnostics report.
* **class:** ``DerivativeScenarioGrid`` — Scenario-grid result for one vanilla option model.
  * ``DerivativeScenarioGrid.as_dict`` — Return a serialization-friendly representation of the grid.
  * ``DerivativeScenarioGrid.pivot`` — Return a spot-by-volatility pivot table for one scenario metric.
  * ``DerivativeScenarioGrid.visualize`` — Return a figure for this derivative scenario grid.
* **function:** ``validate_option_type`` — Normalize and validate a vanilla option type label.
* **function:** ``vanilla_intrinsic_value_from_prices`` — Return the current intrinsic value of a vanilla option.
* **function:** ``option_price`` — Return the call or put price from a scalar pricing model.
* **function:** ``current_intrinsic_value`` — Return the current intrinsic value for a scalar pricing model.
* **function:** ``current_extrinsic_value`` — Return the model value in excess of current intrinsic value.
* **function:** ``spot_moneyness`` — Return spot moneyness for a scalar model.
* **function:** ``forward_moneyness`` — Return forward moneyness for a scalar model.
* **function:** ``break_even_price`` — Return a premium-adjusted terminal break-even price.
* **function:** ``select_option_greeks`` — Select option-specific Greek names from a raw model Greek mapping.
* **function:** ``model_greeks`` — Return option-specific Greeks when a model exposes them.
* **function:** ``derivative_scenario_grid`` — Evaluate a vanilla option model over spot and volatility scenarios.
* **function:** ``derivative_diagnostics`` — Build a complete scalar diagnostics report for one vanilla derivative.
* **class:** ``OptionDiagnosticsMixin`` — Mixin adding scalar vanilla diagnostics to pricing model classes.
  * ``OptionDiagnosticsMixin.price`` — Return this model's call or put price.
  * ``OptionDiagnosticsMixin.intrinsic_value`` — Return the current intrinsic value of the option.
  * ``OptionDiagnosticsMixin.extrinsic_value`` — Return the option's model value above intrinsic value.
  * ``OptionDiagnosticsMixin.moneyness`` — Return the current spot-to-strike moneyness ratio.
  * ``OptionDiagnosticsMixin.forward_moneyness`` — Return the forward-to-strike moneyness ratio.
  * ``OptionDiagnosticsMixin.break_even_price`` — Return the premium-adjusted terminal break-even price.
  * ``OptionDiagnosticsMixin.scenario_grid`` — Evaluate this option model over a spot--volatility scenario grid.
  * ``OptionDiagnosticsMixin.report`` — Return an exportable report for this option model.
  * ``OptionDiagnosticsMixin.diagnostics`` — Return a complete scalar derivative diagnostics report.

Detailed reference
------------------

.. automodule:: abaquant.derivatives.models.diagnostics
   :members:
   :show-inheritance:
   :member-order: bysource
