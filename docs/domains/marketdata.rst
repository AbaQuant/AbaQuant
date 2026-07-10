Market data
===========

The ``abaquant.marketdata`` namespace provides lazy ticker and universe
facades, provider interfaces, cached financial-statement workflows,
option-chain analytics, and bridges into portfolio and credit analytics.

Ticker facade
-------------

.. code:: python

   from abaquant.marketdata import get_ticker

   ticker = get_ticker("AAPL")

A ticker object groups related namespaces:

+-----------------------------------+-----------------------------------+
| Ticker namespace                  | Typical methods                   |
+===================================+===================================+
| ``ticker.spot()``                 | latest or configured spot quote.  |
+-----------------------------------+-----------------------------------+
| ``ticker.history``                | price and return history.         |
+-----------------------------------+-----------------------------------+
| ``ticker.options``                | listed option chains, pricing     |
|                                   | helpers, Greeks, option-chain     |
|                                   | analytics.                        |
+-----------------------------------+-----------------------------------+
| ``ticker.financials``             | statement snapshots, line-item    |
|                                   | helpers, credit-input             |
|                                   | construction.                     |
+-----------------------------------+-----------------------------------+
| ``ticker.credit``                 | credit proxy assessment from      |
|                                   | supplied or cached financials.    |
+-----------------------------------+-----------------------------------+
| ``ticker.visualize()``            | price-history and related charts. |
+-----------------------------------+-----------------------------------+

Object construction is lazy. Provider retrieval occurs when you call a
retrieval method.

Universe facade
---------------

.. code:: python

   from abaquant.marketdata import get_tickers

   universe = get_tickers(["AAPL", "MSFT", "NVDA"])
   prices = universe.history.prices(period="1mo")
   returns = universe.history.returns(period="1mo")
   summary = universe.statistics.summary(period="1mo")
   portfolio = universe.portfolio.max_sharpe(period="1mo", risk_free_rate=0.02)

A universe object aligns multi-asset data and exposes portfolio-oriented
helpers.

Option-chain analytics
----------------------

.. code:: python

   chain_analytics = ticker.options.analytics("2027-01-15")
   iv_smile = chain_analytics.iv_smile(option_type="call")
   iv_surface = chain_analytics.iv_surface(option_type="call")
   skew = chain_analytics.skew(option_type="call")
   rich_cheap = chain_analytics.rich_cheap_table(risk_free_rate=0.04, option_type="call")

Analytics include implied-volatility smiles, surfaces, term structure,
skew summaries, rich/cheap model comparisons, and open-interest
heatmaps.

Financial statements
--------------------

Financial statement workflows normalize provider facts into canonical
statement tables and then build credit inputs.

.. code:: python

   snapshot = ticker.financials.snapshot()
   inputs = ticker.financials.credit_inputs()
   assessment = ticker.credit.assess_from_financials()

The financial statement stack includes:

+-----------------------------------+-----------------------------------+
| Component                         | Role                              |
+===================================+===================================+
| Provider adapter                  | Supplies raw facts or tables.     |
+-----------------------------------+-----------------------------------+
| Normalizer                        | Converts provider data into       |
|                                   | consistent DataFrames.            |
+-----------------------------------+-----------------------------------+
| Line-item resolver                | Maps provider-specific labels     |
|                                   | into canonical metrics.           |
+-----------------------------------+-----------------------------------+
| Cache                             | Reuses raw and normalized         |
|                                   | statement snapshots.              |
+-----------------------------------+-----------------------------------+
| Credit input builder              | Converts statement data into      |
|                                   | ``CreditAnalysisInputs``.         |
+-----------------------------------+-----------------------------------+

Providers
---------

+-----------------------------------+-----------------------------------+
| Provider area                     | Notes                             |
+===================================+===================================+
| Yahoo/yfinance                    | Optional market extra; useful for |
|                                   | quotes, prices, options, and      |
|                                   | broad equity data when available. |
+-----------------------------------+-----------------------------------+
| SEC EDGAR/XBRL                    | Company Facts style provider for  |
|                                   | U.S. public company fundamentals. |
|                                   | Use a real contact user agent for |
|                                   | live requests.                    |
+-----------------------------------+-----------------------------------+
| Manual/deterministic fixtures     | Used by examples and tests to     |
|                                   | keep workflows reproducible.      |
+-----------------------------------+-----------------------------------+

Caching
-------

Use disk caching for repeated live-data sessions and reproducibility.
Cache keys should be interpreted as implementation details; use public
facade methods rather than depending on file names.

Provider risk
-------------

Market-data providers can produce:

-  stale data;
-  delayed data;
-  missing contracts or statements;
-  adjusted historical prices;
-  restated fundamentals;
-  survivorship-biased symbol sets;
-  incomplete option chains;
-  rate-limit or authorization failures.

Record provenance and avoid mixing provider snapshots without checking
retrieval times and reporting periods.
