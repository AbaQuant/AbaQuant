# Calibration tools implementation report

This snapshot adds structured option-model calibration tools to AbaQuant.

## Added APIs

- `CalibrationResult`
- `CalibrationError`
- `BSMFlatVolCalibration`
- `SABRSmileCalibration`
- `HestonCalibration`

## Supported workflows

- BSM flat-volatility calibration to listed premiums or listed implied volatility.
- SABR smile calibration for alpha, rho, and nu with beta fixed.
- Heston stochastic-volatility calibration for kappa, theta, xi, rho, and v0.
- Contract-level model-versus-market error tables.
- Calibration summary and parameter tables.
- Calibration report export through AbaQuant's reporting layer.
- Calibration visualizations for model-vs-market, residuals, and parameters.

## Option-chain integration

`OptionChainAnalytics` now exposes convenience methods:

```python
analytics.calibrate_bsm_flat_vol(option_type="call", risk_free_rate=0.04)
analytics.calibrate_sabr(option_type="call", beta=0.8)
analytics.calibrate_heston(option_type="call", risk_free_rate=0.04)
```

These methods reuse the existing option-chain analytics object while keeping raw provider retrieval separate from numerical calibration.

## Example

Added `examples/22_derivative_calibration.py`, which fits deterministic BSM, SABR, and compact Heston calibrations and saves calibration diagnostic charts.

## Validation

- `python -m compileall -q src examples tests scripts` passed.
- `PYTHONPATH=src python scripts/check_documentation.py` passed.
- `PYTHONPATH=src python -m pytest -q tests` passed: `257 passed`.
- `PYTHONPATH=src python examples/00_import_all_public_modules.py` passed.
- `PYTHONPATH=src python examples/22_derivative_calibration.py` passed.
- `PYTHONPATH=src python examples/run_all_deterministic_examples.py` passed.
- `PYTHONPATH=src python examples/run_all_visual_examples.py` passed.
- `python -m ruff check .` could not run because Ruff is not installed in this execution environment.
