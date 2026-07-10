# Visualization examples update

## Added examples

- Extended advanced derivatives, credit risk, portfolio optimization, and offline market-data examples with direct `visualize()` calls.
- Expanded `09_visualizations.py` with ticker, universe, and financial-statement figures.
- Added `11_visualize_method_gallery.py`, a deterministic reference gallery covering every supported visualization family and one explicit PNG export path.
- Added a reusable deterministic market-data provider under `examples/_shared/`.

## Execution contract

Figures are returned without an implicit display call. The gallery writes only the payoff chart because it passes an explicit `save_path`; all remaining figures are in-memory objects.
