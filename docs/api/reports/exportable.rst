abaquant.reports.exportable
===========================

**Import path:** ``abaquant.reports.exportable``

**Domain:** Structured analytical reports and Markdown, HTML, or lightweight PDF export.

Purpose
-------

Exportable Markdown, HTML, and PDF reports for AbaQuant objects.

When to use it
--------------

Use these objects after calculations are complete and results must be packaged for review, storage, or distribution.

Public objects
--------------

* **class:** ``ReportTable`` — One tabular block inside an exportable report.
  * ``ReportTable.frame`` — Return this table as a defensive pandas DataFrame copy.
* **class:** ``ReportSection`` — One titled narrative section inside an exportable report.
* **class:** ``ExportableReport`` — Structured report that can be exported as Markdown, HTML, or PDF.
  * ``ExportableReport.to_markdown`` — Return the report as Markdown and optionally write it to disk.
  * ``ExportableReport.to_html`` — Return the report as standalone HTML and optionally write it to disk.
  * ``ExportableReport.to_pdf`` — Write a simple text PDF representation of the report.
  * ``ExportableReport.save`` — Export this report to several formats in one directory.
  * ``ExportableReport.as_dict`` — Return a serialization-friendly nested representation of the report.
* **function:** ``generated_metadata`` — Return standard metadata used by AbaQuant generated reports.
* **function:** ``build_option_model_report`` — Build an exportable report for one vanilla option pricing model.
* **function:** ``build_portfolio_allocator_report`` — Build an exportable report for a portfolio allocator object.
* **function:** ``build_backtest_report`` — Build an exportable report for a deterministic portfolio backtest result.
* **function:** ``build_credit_report`` — Build an exportable report for a credit-proxy assessment.
* **function:** ``build_risk_dashboard_report`` — Build an exportable report for an integrated risk dashboard.

Detailed reference
------------------

.. automodule:: abaquant.reports.exportable
   :members:
   :show-inheritance:
   :member-order: bysource
