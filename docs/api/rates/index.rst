abaquant.rates
==============

**Import path:** ``abaquant.rates``

**Domain:** Interest-rate curves, interpolation, discounting, and FRED/manual providers.

Package purpose
---------------

Rate curves, FRED integration, and pure interest-rate helpers.

How to use this package
-----------------------

Defines the package facade and supported import surface. Use this package when a workflow needs tenor-dependent rates or discount factors rather than one scalar risk-free-rate assumption.

Facade objects
--------------

* **class:** ``RatesProviderError`` — Raised when an applied rate provider cannot supply usable data.
* **class:** ``RatesValidationError`` — Raised when a rate-curve request violates a domain constraint.
* **class:** ``FredObservation`` — One FRED observation converted to an annual decimal rate.
* **class:** ``RateCurve`` — Provider-neutral annual decimal rate curve.
  * ``RateCurve.from_rates`` — Create a curve from manually supplied decimal annual rates.
  * ``RateCurve.maturities`` — Return curve maturities in ascending order.
  * ``RateCurve.rates`` — Return annual decimal rates in ascending maturity order.
  * ``RateCurve.as_frame`` — Return the curve points as a tidy DataFrame.
  * ``RateCurve.zero_rate`` — Interpolate an annual decimal zero-rate proxy for one maturity.
  * ``RateCurve.discount_factor`` — Convert the interpolated annual rate into a discount factor.
  * ``RateCurve.visualize`` — Return a themed figure of the annual decimal rate curve.
* **class:** ``FredJsonCacheStore`` — Versioned, checksum-protected disk cache for FRED curve inputs.
  * ``FredJsonCacheStore.observation_path`` — Return the deterministic cache path for one series/date request.
  * ``FredJsonCacheStore.load_observation`` — Load one cached observation when it is present, valid, and fresh.
  * ``FredJsonCacheStore.save_observation`` — Persist one FRED observation through atomic temporary-file replacement.
  * ``FredJsonCacheStore.observation_status`` — Return cache availability metadata for one observation request.
  * ``FredJsonCacheStore.clear_observation`` — Remove one cached observation if it exists.
* **class:** ``FredRateProvider`` — FRED Treasury constant-maturity provider with optional disk caching.
  * ``FredRateProvider.rate_curve`` — Return a Treasury-rate curve from FRED observations.
  * ``FredRateProvider.cache_status`` — Return memory and disk cache status for all configured FRED series.
  * ``FredRateProvider.clear_cache`` — Clear memory and disk observations for the configured date label.
* **class:** ``ManualRateProvider`` — Provider object that returns a manually supplied curve without network access.
  * ``ManualRateProvider.rate_curve`` — Return the configured manual curve for tests and examples.
* **function:** ``get_rate_curve`` — Return a provider-backed risk-free-rate curve.

Package reference
-----------------

.. automodule:: abaquant.rates
   :members:
   :show-inheritance:
   :member-order: bysource
