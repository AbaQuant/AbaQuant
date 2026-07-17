# Examples refactor report

## Summary

The examples folder was rewritten from linear scripts into structured tutorial
modules. Each example now uses named functions for input construction,
calculation, visualization, and orchestration.

## Changes

- Standardized all library access through the installed public facade:
  `import abaquant as aq`.
- Removed source-tree path injection from the examples.
- Added `_shared/output.py` for consistent summaries and deterministic figure
  output directories.
- Rewrote examples `00` through `13` with function-level structure.
- Added additional `visualize()` calls across advanced derivatives, credit,
  portfolio optimization, and market-data examples.
- Added deterministic SVG output directories under `examples/generated_figures/`.
- Rasterized dense surfaces and heatmaps within SVG files to keep artifacts compact.
- Updated `run_all_deterministic_examples.py` to include the new visual report
  and dashboard scripts.
- Updated `README.md` and `MODULE_COVERAGE.md`.

## Visualization coverage

The examples now demonstrate:

- option payoff curves;
- option value profiles;
- recombining tree/lattice plots;
- SABR volatility-smile plots;
- portfolio weights;
- cumulative portfolio returns;
- asset correlation matrices;
- credit-proxy metric charts;
- synthetic credit-score charts;
- ticker price histories;
- universe price histories;
- cached financial-statement charts;
- global visualization themes;
- temporary theme overrides;
- explicit save-path/export workflows.

## Compatibility

The examples use the post-refactor canonical API and do not rely on removed
legacy aliases or any class name containing `Engine`. They require AbaQuant to
be installed from PyPI or as an editable development package.
