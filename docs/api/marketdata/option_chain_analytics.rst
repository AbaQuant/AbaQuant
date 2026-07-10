abaquant.marketdata.option_chain_analytics
==========================================

**Import path:** ``abaquant.marketdata.option_chain_analytics``

**Domain:** Provider-neutral market-data facades, normalized records, caching, and analytics.

Purpose
-------

Listed-option-chain analytics that connect provider data to pricing models.

When to use it
--------------

Use this package to retrieve or inject quotes, price history, option chains, and financial statements while preserving a stable analytical interface.

Public objects
--------------

* **class:** ``OptionSkewSummary`` — Linear implied-volatility skew summary for one listed option slice.
  * ``OptionSkewSummary.as_dict`` — Return a serialization-friendly representation of the skew summary.
* **class:** ``OptionChainAnalytics`` — Provider-independent analytics for one ticker's listed option chains.
  * ``OptionChainAnalytics.enriched_chain`` — Return the chain with midpoint, moneyness, and log-moneyness columns.
  * ``OptionChainAnalytics.iv_smile`` — Return implied volatility by strike and moneyness for one expiry.
  * ``OptionChainAnalytics.iv_surface`` — Return a long-form implied-volatility surface across expirations.
  * ``OptionChainAnalytics.skew`` — Estimate linear implied-volatility skew against log-moneyness.
  * ``OptionChainAnalytics.term_structure`` — Return implied volatility across expirations for one strike.
  * ``OptionChainAnalytics.rich_cheap_table`` — Compare listed market prices with model values contract by contract.
  * ``OptionChainAnalytics.open_interest_grid`` — Return open interest by expiry, strike, and option type.
  * ``OptionChainAnalytics.visualize`` — Visualize a listed-option-chain analytic table.
  * ``OptionChainAnalytics.calibrate_bsm_flat_vol`` — Calibrate one flat Black--Scholes--Merton volatility to the chain.
  * ``OptionChainAnalytics.calibrate_sabr`` — Calibrate SABR smile parameters to listed implied volatilities.
  * ``OptionChainAnalytics.calibrate_heston`` — Calibrate Heston parameters to listed option observations.

Detailed reference
------------------

.. automodule:: abaquant.marketdata.option_chain_analytics
   :members:
   :show-inheritance:
   :member-order: bysource
