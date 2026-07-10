# FRED Rate Curve Provider Report

## Summary

This update adds an applied risk-free-rate curve layer to AbaQuant. The new API
is provider-neutral, but includes a built-in FRED provider that retrieves U.S.
Treasury constant-maturity series, converts percentage yields to annual decimal
rates, caches observations, interpolates rates by maturity, and computes discount
factors.

## Public API

```python
from abaquant.rates import get_rate_curve

curve = get_rate_curve(provider="fred", date="latest", api_key="...")
curve.zero_rate(maturity=1.0)
curve.discount_factor(maturity=2.0)
```

Deterministic/manual usage is also supported:

```python
from abaquant.rates import ManualRateProvider, get_rate_curve

curve = get_rate_curve(provider=ManualRateProvider({1.0: 0.04, 2.0: 0.05}))
```

## Added objects

- `RateCurve`
- `FredObservation`
- `FredRateProvider`
- `FredJsonCacheStore`
- `ManualRateProvider`
- `RatesProviderError`
- `RatesValidationError`
- `get_rate_curve`

## Cache behavior

FRED observations support:

- `refresh_policy="cache_only"`
- `refresh_policy="if_missing"`
- `refresh_policy="if_stale"`
- `refresh_policy="refresh"`

Disk cache files are schema-versioned, checksum-validated, and written through
atomic temporary-file replacement.

## Curve conventions

- FRED percentages are converted to decimal rates.
- Maturities are in years.
- `zero_rate()` uses linear interpolation and flat endpoint extrapolation by default.
- `discount_factor()` uses continuous compounding by default.
- The implementation treats Treasury constant-maturity yields as a practical
  risk-free proxy, not as a bootstrapped zero-coupon curve.

## Examples

Added `examples/16_fred_rate_curve.py`, which demonstrates:

- deterministic manual curve construction;
- zero-rate interpolation;
- discount-factor calculation;
- use of a curve-derived rate inside `BlackScholesMertonModel`;
- rate-curve visualization;
- optional live FRED branch when `FRED_API_KEY` exists.

## Validation

- `python -m compileall -q src examples tests scripts` passed.
- `python scripts/check_documentation.py` passed.
- `python -m pytest -q tests` passed: 229 passed.
- `python examples/00_import_all_public_modules.py` passed.
- `python examples/16_fred_rate_curve.py` passed.
- `python examples/run_all_deterministic_examples.py` passed.
- `python examples/run_all_visual_examples.py` passed.

`ruff` was not available in the execution environment, so it could not be run.
