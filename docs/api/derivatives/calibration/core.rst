abaquant.derivatives.calibration.core
=====================================

**Import path:** ``abaquant.derivatives.calibration.core``

**Domain:** Derivative pricing, simulation, calibration, diagnostics, and strategy analysis.

Purpose
-------

Object-oriented calibration tools for listed and synthetic option smiles.

When to use it
--------------

This module fits model parameters to observations. Inspect convergence status, residual scale, bounds, weighting, and data provenance before treating fitted parameters as stable estimates.

Public objects
--------------

* **class:** ``CalibrationError`` — Raised when option-model calibration inputs are incomplete or invalid.
* **class:** ``CalibrationResult`` — Fitted option-model calibration result.
  * ``CalibrationResult.summary`` — Return compact fit diagnostics and calibrated parameters.
  * ``CalibrationResult.error_table`` — Return the contract-level market-versus-model residual table.
  * ``CalibrationResult.parameter_table`` — Return calibrated parameters as a two-column table.
  * ``CalibrationResult.as_dict`` — Return a serialization-friendly representation of the calibration result.
  * ``CalibrationResult.visualize`` — Visualize model-versus-market fit quality or calibrated parameters.
  * ``CalibrationResult.report`` — Return an exportable report describing the calibration fit.
* **class:** ``BSMFlatVolCalibration`` — Calibrate a single flat Black--Scholes--Merton volatility.
  * ``BSMFlatVolCalibration.fit`` — Fit the flat-volatility model and return a calibration result.
* **class:** ``SABRSmileCalibration`` — Calibrate SABR alpha, rho, and nu against a listed volatility smile.
  * ``SABRSmileCalibration.fit`` — Fit SABR smile parameters and return the calibration diagnostics.
* **class:** ``HestonCalibration`` — Calibrate Heston parameters against option prices or implied volatilities.
  * ``HestonCalibration.fit`` — Fit Heston stochastic-volatility parameters.

Detailed reference
------------------

.. automodule:: abaquant.derivatives.calibration.core
   :members:
   :show-inheritance:
   :member-order: bysource
