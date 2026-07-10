Architecture
============

AbaQuant is arranged by financial domain, not by numerical technique.
The package deliberately keeps public workflows stable while allowing
internal modules to evolve.

Source tree
-----------

.. code:: text

   src/abaquant/
     core/             shared provenance infrastructure
     derivatives/      option and forward pricing, strategies, calibration
     financial_math/   time-value, rates, annuities, bonds, corporate finance
     marketdata/       ticker/universe facades and provider adapters
     credit/           credit transitions, CDS/CDO, proxy scoring
     portfolio/        allocation, optimization, backtesting, stress tests
     rates/            rate curves and FRED/manual providers
     visualization/    Matplotlib and Plotly chart helpers
     reports/          Markdown/HTML/PDF report builders
     risk/             integrated risk dashboards

Design principles
-----------------

1. Stable public namespaces
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The public API is exposed through ``__all__`` in the main namespaces.
Prefer imports such as:

.. code:: python

   from abaquant.derivatives import BlackScholesMertonModel
   from abaquant.portfolio import PortfolioAllocator
   from abaquant.marketdata import get_ticker

Avoid importing private helper modules unless you are extending
internals.

2. Lazy provider access
~~~~~~~~~~~~~~~~~~~~~~~

Market-data objects are lightweight facades. Creating a ticker or
universe object should not itself imply a network request. Retrieval
methods such as ``spot()``, ``history.prices()``, ``options.chain()``,
or ``financials.snapshot()`` may use a configured provider.

3. Deterministic examples first
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The example suite is written to run without network access unless the
file explicitly describes live data. This protects regression tests and
makes tutorials reproducible.

4. Provenance-aware outputs
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Objects that depend on provider data, cached data, transformed financial
statements, rate curves, or derived reports should expose
``.provenance`` when possible.

5. Reports and visualizations are downstream products
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Charts and reports sit at the end of workflows:

.. code:: text

   inputs -> model or allocator -> analytics -> visualization/report -> provenance

This keeps numerical logic reusable in scripts, notebooks, CI jobs, and
applications.

Cross-domain workflow examples
------------------------------

Derivatives with rates
~~~~~~~~~~~~~~~~~~~~~~

.. code:: text

   ManualRateProvider or FredRateProvider
           |
           v
   RateCurve.zero_rate(T)
           |
           v
   BlackScholesMertonModel.risk_free_rate
           |
           v
   price, Greeks, report, chart

Market data with credit scoring
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: text

   MarketTicker.financials.snapshot()
           |
           v
   canonical financial statement tables
           |
           v
   CreditAnalysisInputs
           |
           v
   CreditProxyAssessment
           |
           v
   credit report and visualization

Portfolio with risk dashboard
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: text

   returns DataFrame
           |
           v
   PortfolioAllocator
           |
           v
   backtest + weights + risk metrics
           |
           v
   RiskDashboard with optional credit assessments
           |
           v
   dashboard report and figures

Error categories
----------------

AbaQuant uses domain-specific exceptions where possible:

+-----------------------------------+-----------------------------------+
| Error family                      | Meaning                           |
+===================================+===================================+
| ``MarketDataError`` and           | Provider, validation, optional    |
| subclasses                        | dependency, and universe errors.  |
+-----------------------------------+-----------------------------------+
| ``PortfolioOptimizationError``    | Optimization failure or           |
|                                   | infeasible allocation request.    |
+-----------------------------------+-----------------------------------+
| ``PortfolioValidationError``      | Invalid portfolio input shape,    |
|                                   | weight constraints, or return     |
|                                   | data.                             |
+-----------------------------------+-----------------------------------+
| ``RatesProviderError``            | Rate provider could not supply    |
|                                   | usable data.                      |
+-----------------------------------+-----------------------------------+
| ``RatesValidationError``          | Invalid rate-curve inputs or      |
|                                   | maturity requests.                |
+-----------------------------------+-----------------------------------+
| ``VisualizationError``            | Visualization backend or chart    |
|                                   | request failure.                  |
+-----------------------------------+-----------------------------------+
| ``CalibrationError``              | Model calibration could not       |
|                                   | complete or received invalid      |
|                                   | data.                             |
+-----------------------------------+-----------------------------------+

Stability policy for v1
-----------------------

Stable v1 imports should remain available through the documented
namespaces. Internal modules may be reorganized, but compatibility
wrappers should preserve documented imports when feasible.

Non-stable areas:

-  private functions and names beginning with ``_``;
-  provider implementation details;
-  exact figure object internals;
-  cached provider file layout;
-  numerical optimizer internals and default optimizer diagnostics.
