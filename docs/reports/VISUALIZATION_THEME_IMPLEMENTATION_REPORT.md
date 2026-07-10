# Visualization Theme and Export Implementation Report

## Delivered capabilities

- Added immutable `VisualizationTheme` configuration objects.
- Added global theme configuration through `configure_visualization()`.
- Added `get_visualization_theme()`, `reset_visualization_theme()`, and the
  temporary `visualization_theme()` context manager.
- Added global defaults for backend, palette, background, grid, font family,
  font sizes, figure size, DPI, line width, marker size, transparency, and
  export behavior.
- Added `save_path` and `filename` support to every supported public
  `visualize()` method.
- Added opt-in `auto_save` behavior through the global template.
- Added backend-aware saving: Matplotlib uses `savefig`; Plotly uses HTML
  directly or static image export when Kaleido is available.
- Updated option, lattice, portfolio, credit, market-price, and statement
  visualizations to use the active theme consistently.
- Added `examples/10_visualization_theme.py` and
  `docs/VISUALIZATION_THEME.md`.

## Validation

- `python -m compileall -q .` passed.
- `pytest -q tests` passed: 11 tests.
- Existing deterministic example runner passed.
- Import coverage passed for 76 public modules.
- Global theme, temporary theme restoration, and auto-save behavior were
  exercised by deterministic tests.

## Deliberate behavior

Figures are returned and never displayed automatically. Export is only
performed when an explicit output destination is supplied or the active theme
sets `auto_save=True`.
