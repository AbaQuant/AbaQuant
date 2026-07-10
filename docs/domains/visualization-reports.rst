Visualization and reports
=========================

AbaQuant separates numerical workflows from presentation workflows.
Model, portfolio, credit, market-data, calibration, and dashboard
objects can create visualizations and exportable reports.

Visualization setup
-------------------

.. code:: python

   from abaquant.visualization import (
       VisualizationTheme,
       configure_visualization,
       visualization_theme,
       save_figure,
   )

   theme = VisualizationTheme(title="Research", backend="matplotlib")
   configure_visualization(theme)

Use a temporary theme in a context manager:

.. code:: python

   with visualization_theme(VisualizationTheme(backend="plotly")):
       fig = model.visualize(chart="price_surface", option_type="call")

Common chart entry points
-------------------------

+-----------------------------------+-----------------------------------+
| Object or namespace               | Typical charts                    |
+===================================+===================================+
| Option model                      | price curves, Greek curves, price |
|                                   | surfaces, Greek surfaces,         |
|                                   | intrinsic/extrinsic               |
|                                   | decomposition.                    |
+-----------------------------------+-----------------------------------+
| Option strategy                   | payoff profile, component payoff, |
|                                   | net profit.                       |
+-----------------------------------+-----------------------------------+
| Option-chain analytics            | IV smile, IV surface, skew, term  |
|                                   | structure, rich/cheap table,      |
|                                   | open-interest heatmap.            |
+-----------------------------------+-----------------------------------+
| Portfolio allocator               | weights, cumulative returns,      |
|                                   | correlation, risk contribution.   |
+-----------------------------------+-----------------------------------+
| Portfolio backtest                | equity curve, drawdown, rolling   |
|                                   | metrics, calendar returns,        |
|                                   | contribution, trades.             |
+-----------------------------------+-----------------------------------+
| Credit assessment                 | metric dashboard, score/band      |
|                                   | visualization, scenario chart.    |
+-----------------------------------+-----------------------------------+
| Market ticker/universe            | price history,                    |
|                                   | financial-statement charts,       |
|                                   | universe performance.             |
+-----------------------------------+-----------------------------------+
| Calibration result                | model-versus-market fit, residual |
|                                   | diagnostics.                      |
+-----------------------------------+-----------------------------------+
| Risk dashboard                    | risk contribution, drawdown,      |
|                                   | correlation, credit score         |
|                                   | summary.                          |
+-----------------------------------+-----------------------------------+

Save figures
------------

.. code:: python

   fig = allocator.visualize(chart="correlation")
   save_figure(fig, "portfolio_correlation.png")

Backends return different object types. Use ``save_figure()`` or the
built-in ``filename`` arguments on high-level visualization methods when
available.

Reports
-------

Reports are built from reusable sections, metrics, and tables.

.. code:: python

   from abaquant.reports import ExportableReport, ReportSection, ReportTable

Most high-level objects expose ``.report()``:

.. code:: python

   option_report = model.report(option_type="call")
   portfolio_report = allocator.report()
   backtest_report = backtest.report()
   credit_report = assessment.report()
   dashboard_report = dashboard.report()

Export formats
--------------

.. code:: python

   written = option_report.save(
       "reports",
       "option_report",
       formats=("markdown", "html", "pdf"),
   )

+-----------------------------------+-----------------------------------+
| Format                            | Use case                          |
+===================================+===================================+
| Markdown                          | Plain-text review, Git diffs,     |
|                                   | notebooks, README fragments.      |
+-----------------------------------+-----------------------------------+
| HTML                              | Browser review, richer tables,    |
|                                   | lightweight sharing.              |
+-----------------------------------+-----------------------------------+
| PDF                               | Self-contained static report;     |
|                                   | generated by a lightweight        |
|                                   | built-in writer.                  |
+-----------------------------------+-----------------------------------+

The PDF exporter is intentionally simple and pure Python. It is useful
for compact static reports, not for complex print-layout publishing.

Report provenance
-----------------

Reports can include generated metadata and provenance inherited from
source objects. This is useful when a report combines live provider
data, cached financial statements, rate curves, and model
transformations.

Common pitfalls
---------------

-  Creating many Matplotlib figures without closing them can trigger
   open-figure warnings.
-  Plotly output requires the optional visualization dependencies.
-  Figure object APIs differ by backend.
-  Visualizations are explanatory aids; numerical result objects are the
   source of truth.
