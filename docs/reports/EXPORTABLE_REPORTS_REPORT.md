# Exportable reports implementation report

## Scope

Added a dependency-light reporting layer for AbaQuant objects that already produce useful diagnostics:

- option pricing models;
- portfolio allocators;
- deterministic portfolio backtest results;
- credit-proxy assessments;
- integrated risk dashboards.

## Public API

```python
report = option_model.report(option_type="call")
report.to_markdown("option_report.md")
report.to_html("option_report.html")
report.to_pdf("option_report.pdf")

portfolio_report = allocator.report()
portfolio_report.to_html("portfolio_report.html")

credit_report = assessment.report()
credit_report.to_markdown("credit_proxy_report.md")
```

Additional supported objects:

```python
backtest.report().to_html("backtest_report.html")
dashboard.report().to_pdf("risk_dashboard_report.pdf")
```

## Design notes

- Markdown and HTML exports use only the Python standard library plus pandas, which is already a package dependency.
- PDF export writes a simple valid text PDF using the standard library. It does not require reportlab, weasyprint, wkhtmltopdf, LaTeX, or a browser runtime.
- Reports are represented as `ExportableReport`, `ReportSection`, and `ReportTable` objects.
- The `save(directory, stem, formats=...)` helper exports multiple formats with one call.

## Validation

- `python -m compileall -q src examples tests scripts` passed.
- `PYTHONPATH=src python scripts/check_documentation.py` passed.
- `PYTHONPATH=src python -m pytest -q tests` passed: 253 tests.
- `PYTHONPATH=src python examples/00_import_all_public_modules.py` passed.
- `PYTHONPATH=src python examples/21_exportable_reports.py` passed.
- `PYTHONPATH=src python examples/run_all_deterministic_examples.py` passed.
- `PYTHONPATH=src python examples/run_all_visual_examples.py` passed.
- ZIP integrity test passed.

Ruff was not available in this environment.
