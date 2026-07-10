# Visualization Examples Validation Report

## Updated example coverage

- `03_advanced_derivatives.py` now creates Black--Scholes--Merton price-profile, CRR lattice, and SABR volatility-smile figures.
- `04_credit_risk.py` now creates credit-metrics and synthetic-score figures.
- `05_portfolio_optimization.py` now creates allocation-weight, cumulative-return, and correlation figures.
- `06_marketdata_offline.py` now creates ticker-price, financial-statement, credit-metrics, and universe-price figures using an offline deterministic provider.
- `09_visualizations.py` now includes option, lattice, portfolio, credit, ticker, universe, and financial-statement examples.
- `10_visualization_theme.py` remains the global-theme and export-policy example.
- `11_visualize_method_gallery.py` is a complete reference gallery covering every supported public visualization family and an explicit PNG `save_path` example.

## Validation completed

- `python -m compileall -q .`: passed.
- Targeted visualization examples (`03`, `04`, `05`, `06`, `09`, and `11`): passed through a temporary package alias required by the flat archive layout.
- Public import example (`00`) and baseline examples (`01`, `02`, and `08`): passed.
- `pytest -q tests`: passed (`11 passed`).

## Execution behavior

Examples return figures and do not call `show()` automatically. `11_visualize_method_gallery.py` writes only one PNG because it passes an explicit `save_path`; remaining figures are in-memory objects.
