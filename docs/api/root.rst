abaquant root facade
====================

The root namespace provides version metadata and convenience re-exports. For 
long-lived production code, prefer the domain namespaces shown below because they 
make dependencies and ownership clearer.

.. code-block:: python

   :caption: Prefer explicit domain imports


   import abaquant
   from abaquant.derivatives import black_scholes
   from abaquant.portfolio import PortfolioAllocator

Root package documentation
--------------------------

.. automodule:: abaquant
   :no-index:


Domain packages
---------------

* :doc:`core/index` — Auditability and metadata primitives.
* :doc:`credit/index` — Credit-risk analytics and fundamentals-derived credit proxies.
* :doc:`derivatives/index` — Derivative pricing, simulation, calibration, diagnostics, and strategy analysis.
* :doc:`financial_math/index` — Time-value, actuarial, fixed-income, corporate-finance, and portfolio mathematics.
* :doc:`marketdata/index` — Provider-neutral market-data facades, normalized records, caching, and analytics.
* :doc:`portfolio/index` — Portfolio construction, optimization, backtesting, risk metrics, and stress testing.
* :doc:`rates/index` — Interest-rate curves, interpolation, discounting, and FRED/manual providers.
* :doc:`reports/index` — Structured analytical reports and Markdown, HTML, or lightweight PDF export.
* :doc:`risk/index` — Integrated portfolio and credit-risk dashboards.
* :doc:`visualization/index` — Matplotlib and Plotly visualization helpers with shared themes.
