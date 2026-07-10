Examples
========

The ``examples/`` directory is the executable tutorial layer. Most
examples are deterministic and offline so they can be used as smoke
tests and learning material.

Run all deterministic examples
------------------------------

.. code:: bash

   PYTHONPATH=src python examples/run_all_deterministic_examples.py

Run visualization examples
--------------------------

.. code:: bash

   PYTHONPATH=src python examples/run_all_visual_examples.py

Visualization examples save files under:

.. code:: text

   examples/generated_figures/

Report examples save files under:

.. code:: text

   examples/generated_reports/

Example map
-----------

+-----------------------------------+-----------------------------------+
| File                              | Topic                             |
+===================================+===================================+
| ``                                | Imports public modules and        |
| 00_import_all_public_modules.py`` | catches namespace regressions.    |
+-----------------------------------+-----------------------------------+
| ``01_derivatives.py``             | Vanilla options, Greeks, trees,   |
|                                   | forwards, strategies, and         |
|                                   | exotics.                          |
+-----------------------------------+-----------------------------------+
| ``02_financial_math.py``          | Time value, rates, annuities,     |
|                                   | bonds, DCF, loans, portfolio      |
|                                   | math, VaR.                        |
+-----------------------------------+-----------------------------------+
| ``03                              | BSM, CRR, Bachelier, Heston,      |
| _derivatives_advanced_models.py`` | Merton, NIG, SABR,                |
|                                   | Variance-Gamma.                   |
+-----------------------------------+-----------------------------------+
| ``04_credit_risk.py``             | Credit proxy metrics, transition  |
|                                   | matrices, CDS, CDO, copula, VaR.  |
+-----------------------------------+-----------------------------------+
| ``05_portfolio_optimization.py``  | Allocation families, frontier,    |
|                                   | Monte Carlo portfolios, stress    |
|                                   | tests.                            |
+-----------------------------------+-----------------------------------+
| ``06_marketdata_offline.py``      | Deterministic ticker and universe |
|                                   | workflows.                        |
+-----------------------------------+-----------------------------------+
| ``07_marke                        | Optional live/cached market-data  |
| tdata_live_cached_financials.py`` | workflow.                         |
+-----------------------------------+-----------------------------------+
| ``08_root_facades.py``            | Root namespace and facade         |
|                                   | imports.                          |
+-----------------------------------+-----------------------------------+
| ``09_visualizations.py``          | General visualization smoke test. |
+-----------------------------------+-----------------------------------+
| ``10_visualization_theme.py``     | Matplotlib/Plotly theme           |
|                                   | configuration.                    |
+-----------------------------------+-----------------------------------+
| `                                 | Object ``.visualize()`` gallery.  |
| `11_visualize_method_gallery.py`` |                                   |
+-----------------------------------+-----------------------------------+
| ``1                               | Option model charts and reports.  |
| 2_option_model_visual_report.py`` |                                   |
+-----------------------------------+-----------------------------------+
| ``13_portf                        | Portfolio-credit visual           |
| olio_credit_visual_dashboard.py`` | dashboard.                        |
+-----------------------------------+-----------------------------------+
| ``14_scenario_analysis.py``       | Cross-domain scenario analysis.   |
+-----------------------------------+-----------------------------------+
| ``15_sec_xbrl_fundamentals.py``   | SEC-style facts to statements to  |
|                                   | credit inputs.                    |
+-----------------------------------+-----------------------------------+
| ``16_fred_rate_curve.py``         | Manual and optional live FRED     |
|                                   | rate curves.                      |
+-----------------------------------+-----------------------------------+
| ``17_option_chain_analytics.py``  | IV smile, IV surface, skew, term  |
|                                   | structure, rich/cheap, open       |
|                                   | interest.                         |
+-----------------------------------+-----------------------------------+
| ``18_option_strategy_builder.py`` | Composable option strategies and  |
|                                   | payoff diagnostics.               |
+-----------------------------------+-----------------------------------+
| ``19_portfolio_backtesting.py``   | Rebalanced portfolio backtesting  |
|                                   | and reporting.                    |
+-----------------------------------+-----------------------------------+
| ``20_risk_dashboard.py``          | Integrated portfolio and credit   |
|                                   | risk dashboard.                   |
+-----------------------------------+-----------------------------------+
| ``21_exportable_reports.py``      | Markdown, HTML, and PDF report    |
|                                   | export.                           |
+-----------------------------------+-----------------------------------+
| ``22_derivative_calibration.py``  | BSM, SABR, and Heston calibration |
|                                   | diagnostics.                      |
+-----------------------------------+-----------------------------------+
| ``23_data_provenance.py``         | Provenance across rates,          |
|                                   | derivatives, portfolios, credit,  |
|                                   | dashboards, and reports.          |
+-----------------------------------+-----------------------------------+

Learning path
-------------

1. Run ``01_derivatives.py``, ``02_financial_math.py``, and
   ``05_portfolio_optimization.py`` first.
2. Run ``06_marketdata_offline.py`` to understand ticker and universe
   facades without live data.
3. Run ``17_option_chain_analytics.py``,
   ``18_option_strategy_builder.py``, and
   ``22_derivative_calibration.py`` for derivatives workflows.
4. Run ``19_portfolio_backtesting.py`` and ``20_risk_dashboard.py`` for
   portfolio-risk workflows.
5. Run ``21_exportable_reports.py`` and ``23_data_provenance.py`` to
   understand deliverables and audit metadata.

Determinism policy
------------------

Examples should prefer deterministic fixtures over live providers. If an
example can make a network request, it should say so in the file and
remain skippable or optional.
