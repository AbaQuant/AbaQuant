abaquant.visualization.core
===========================

**Import path:** ``abaquant.visualization.core``

**Domain:** Matplotlib and Plotly visualization helpers with shared themes.

Purpose
-------

Global styling, backend selection, and export helpers for visualizations.

When to use it
--------------

Use these functions to inspect model behavior, portfolio allocations, market surfaces, credit assessments, calibrations, and dashboard outputs.

Public objects
--------------

* **class:** ``VisualizationError`` — Raised when a visualization request cannot be produced or exported.
* **class:** ``VisualizationTheme`` — Reusable presentation and export settings for all library plots.
* **function:** ``get_visualization_theme`` — Return the immutable global visualization theme currently in effect.
* **function:** ``configure_visualization`` — Set and return the global visualization theme.
* **function:** ``reset_visualization_theme`` — Restore the built-in global visualization theme and return it.
* **function:** ``visualization_theme`` — Temporarily apply a theme inside a ''with'' block.
* **function:** ``resolve_theme`` — Resolve one per-call theme, applying an optional backend override.
* **function:** ``validate_backend`` — Validate one backend name, using the global theme when ''None''.
* **function:** ``require_matplotlib`` — Import Matplotlib lazily and raise an actionable error when missing.
* **function:** ``require_plotly`` — Import Plotly lazily and raise an actionable error when missing.
* **function:** ``matplotlib_axes`` — Create one styled Matplotlib figure and axes using ''theme''.
* **function:** ``style_matplotlib_axes`` — Apply typography, grid, and color-cycle settings to Matplotlib axes.
* **function:** ``style_matplotlib_title`` — Set a consistently themed Matplotlib axes title.
* **function:** ``style_plotly_figure`` — Apply global layout, typography, palette, and dimensions to Plotly figures.
* **function:** ``save_figure`` — Persist one backend-native figure and return its resolved output path.
* **function:** ``finalize_figure`` — Optionally export a figure according to explicit or global theme settings.

Detailed reference
------------------

.. automodule:: abaquant.visualization.core
   :members:
   :show-inheritance:
   :member-order: bysource
