"""Global styling, backend selection, and export helpers for visualizations.

The visualization layer is configured once through :func:`configure_visualization`.
Every public ``visualize`` method resolves the active :class:`VisualizationTheme`
unless an explicit ``theme`` or ``backend`` is supplied. Figure creation never
calls ``show``; optional export is controlled through the active theme or a
per-call ``save_path``.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

VisualizationBackend = Literal["matplotlib", "plotly"]


class VisualizationError(RuntimeError):
    """Raised when a visualization request cannot be produced or exported."""


@dataclass(frozen=True)
class VisualizationTheme:
    """Reusable presentation and export settings for all library plots.

    Parameters
    ----------
    backend : {"matplotlib", "plotly"}, default="matplotlib"
        Backend used when individual ``visualize`` calls omit ``backend``.
    color_sequence : sequence of str, optional
        Ordered color palette used for lines, bars, and markers. CSS color names
        and hexadecimal color strings are accepted by both supported backends.
    background_color, paper_color : str, default="white"
        Plot-area and canvas colors. ``paper_color`` applies to Plotly canvas;
        Matplotlib uses ``background_color`` for the figure face color.
    grid_color : str, default="#d9d9d9"
        Gridline color for Cartesian charts.
    font_family : str, default="DejaVu Sans"
        Preferred font family. Availability depends on the local rendering
        environment.
    base_font_size : float, default=11.0
        Default axis, legend, and tick-label font size in points.
    title_font_size : float, default=15.0
        Figure-title font size in points.
    figure_size : tuple[float, float], default=(10.0, 6.0)
        Default figure width and height in inches for Matplotlib. Plotly uses
        the equivalent pixel dimensions derived from ``dpi``.
    dpi : int, default=120
        Raster resolution used by Matplotlib and as the conversion basis for
        Plotly layout dimensions.
    line_width : float, default=2.0
        Default line width for line charts.
    marker_size : float, default=6.0
        Default marker size for scatter and lattice charts.
    transparent : bool, default=False
        Whether saved outputs should request transparent backgrounds where the
        selected backend and format support it.
    save_directory : str or pathlib.Path, optional
        Directory used when ``auto_save=True`` and no explicit ``save_path`` is
        provided. Directories are created on demand.
    save_format : str, default="png"
        File format appended to generated filenames when no extension is given.
        Matplotlib supports its installed writers. Plotly static image export
        requires the optional ``kaleido`` package; ``html`` requires no extra
        renderer.
    auto_save : bool, default=False
        Save every newly created visualization using ``save_directory`` and a
        generated file name. A missing ``save_directory`` raises an error.
    filename_prefix : str, default="abaquant"
        Prefix used for generated filenames.
    """

    backend: VisualizationBackend = "matplotlib"
    color_sequence: tuple[str, ...] = (
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
    )
    background_color: str = "white"
    paper_color: str = "white"
    grid_color: str = "#d9d9d9"
    font_family: str = "DejaVu Sans"
    base_font_size: float = 11.0
    title_font_size: float = 15.0
    figure_size: tuple[float, float] = (10.0, 6.0)
    dpi: int = 120
    line_width: float = 2.0
    marker_size: float = 6.0
    transparent: bool = False
    save_directory: str | Path | None = None
    save_format: str = "png"
    auto_save: bool = False
    filename_prefix: str = "abaquant"

    def __post_init__(self) -> None:
        """Validate theme dimensions, palette, export format, and font sizes."""
        if self.backend not in {"matplotlib", "plotly"}:
            raise ValueError("backend must be 'matplotlib' or 'plotly'.")
        if not self.color_sequence:
            raise ValueError("color_sequence must contain at least one color.")
        if len(self.figure_size) != 2 or any(float(value) <= 0.0 for value in self.figure_size):
            raise ValueError("figure_size must contain two positive values in inches.")
        if self.dpi <= 0 or self.base_font_size <= 0 or self.title_font_size <= 0:
            raise ValueError("dpi and font sizes must be positive.")
        if self.line_width <= 0 or self.marker_size <= 0:
            raise ValueError("line_width and marker_size must be positive.")
        if not self.save_format.strip():
            raise ValueError("save_format cannot be empty.")
        if self.auto_save and self.save_directory is None:
            raise ValueError("auto_save=True requires save_directory.")


_ACTIVE_THEME = VisualizationTheme()


def get_visualization_theme() -> VisualizationTheme:
    """Return the immutable global visualization theme currently in effect."""
    return _ACTIVE_THEME


def configure_visualization(
    theme: VisualizationTheme | None = None, /, **overrides: object
) -> VisualizationTheme:
    """Set and return the global visualization theme.

    Parameters
    ----------
    theme : VisualizationTheme, optional
        Complete baseline theme. When omitted, the current theme is used as the
        baseline.
    **overrides
        Named :class:`VisualizationTheme` fields to replace on the baseline.

    Returns
    -------
    VisualizationTheme
        Newly active immutable theme.
    """
    global _ACTIVE_THEME
    baseline = theme if theme is not None else _ACTIVE_THEME
    if not isinstance(baseline, VisualizationTheme):
        raise TypeError("theme must be a VisualizationTheme instance or None.")
    try:
        _ACTIVE_THEME = replace(baseline, **overrides) if overrides else baseline
    except TypeError as error:
        raise VisualizationError(f"Unknown visualization theme option: {error}") from error
    return _ACTIVE_THEME


def reset_visualization_theme() -> VisualizationTheme:
    """Restore the built-in global visualization theme and return it."""
    global _ACTIVE_THEME
    _ACTIVE_THEME = VisualizationTheme()
    return _ACTIVE_THEME


@contextmanager
def visualization_theme(
    theme: VisualizationTheme | None = None, /, **overrides: object
) -> Iterator[VisualizationTheme]:
    """Temporarily apply a theme inside a ``with`` block.

    The previous global theme is restored even when plotting raises an error.
    """
    global _ACTIVE_THEME
    previous_theme = _ACTIVE_THEME
    active_theme = configure_visualization(theme, **overrides)
    try:
        yield active_theme
    finally:
        _ACTIVE_THEME = previous_theme


def resolve_theme(
    theme: VisualizationTheme | None = None, backend: VisualizationBackend | None = None
) -> VisualizationTheme:
    """Resolve one per-call theme, applying an optional backend override."""
    selected_theme = theme if theme is not None else get_visualization_theme()
    if not isinstance(selected_theme, VisualizationTheme):
        raise TypeError("theme must be a VisualizationTheme instance or None.")
    if backend is None:
        return selected_theme
    return replace(selected_theme, backend=validate_backend(backend))


def validate_backend(backend: str | None) -> VisualizationBackend:
    """Validate one backend name, using the global theme when ``None``."""
    if backend is None:
        return get_visualization_theme().backend
    normalized_backend = str(backend).lower()
    if normalized_backend not in {"matplotlib", "plotly"}:
        raise VisualizationError("backend must be either 'matplotlib' or 'plotly'.")
    return normalized_backend  # type: ignore[return-value]


def require_matplotlib():
    """Import Matplotlib lazily and raise an actionable error when missing."""
    try:
        import matplotlib.pyplot as pyplot
    except ImportError as error:
        raise VisualizationError(
            "Matplotlib visualization requires the optional dependency 'matplotlib'. "
            "Install it with: pip install matplotlib"
        ) from error
    return pyplot


def require_plotly():
    """Import Plotly lazily and raise an actionable error when missing."""
    try:
        import plotly.graph_objects as graph_objects
    except ImportError as error:
        raise VisualizationError(
            "Plotly visualization requires the optional dependency 'plotly'. "
            "Install it with: pip install plotly"
        ) from error
    return graph_objects


def matplotlib_axes(pyplot, theme: VisualizationTheme):
    """Create one styled Matplotlib figure and axes using ``theme``."""
    figure, axes = pyplot.subplots(
        figsize=theme.figure_size,
        dpi=theme.dpi,
        facecolor=theme.background_color,
    )
    axes.set_facecolor(theme.background_color)
    return figure, axes


def style_matplotlib_axes(axes, theme: VisualizationTheme, *, grid_axis: str = "both") -> None:
    """Apply typography, grid, and color-cycle settings to Matplotlib axes."""
    axes.set_prop_cycle(color=list(theme.color_sequence))
    axes.grid(True, axis=grid_axis, color=theme.grid_color, alpha=0.65)
    for spine in axes.spines.values():
        spine.set_color(theme.grid_color)
    axes.tick_params(labelsize=theme.base_font_size)
    for label in [axes.xaxis.label, axes.yaxis.label]:
        label.set_fontname(theme.font_family)
        label.set_fontsize(theme.base_font_size)


def style_matplotlib_title(axes, title: str, theme: VisualizationTheme) -> None:
    """Set a consistently themed Matplotlib axes title."""
    axes.set_title(title, fontname=theme.font_family, fontsize=theme.title_font_size)


def style_plotly_figure(
    figure,
    theme: VisualizationTheme,
    *,
    title: str | None = None,
    xaxis_title: str | None = None,
    yaxis_title: str | None = None,
):
    """Apply global layout, typography, palette, and dimensions to Plotly figures."""
    width_pixels = int(theme.figure_size[0] * theme.dpi)
    height_pixels = int(theme.figure_size[1] * theme.dpi)
    layout = {
        "template": "plotly_white",
        "paper_bgcolor": theme.paper_color,
        "plot_bgcolor": theme.background_color,
        "font": {"family": theme.font_family, "size": theme.base_font_size},
        "colorway": list(theme.color_sequence),
        "width": width_pixels,
        "height": height_pixels,
        "margin": {"l": 70, "r": 30, "t": 80, "b": 60},
        "title": {
            "text": title or "",
            "font": {"family": theme.font_family, "size": theme.title_font_size},
        },
        "xaxis": {"title": xaxis_title, "showgrid": True, "gridcolor": theme.grid_color},
        "yaxis": {"title": yaxis_title, "showgrid": True, "gridcolor": theme.grid_color},
    }
    figure.update_layout(**layout)
    return figure


def save_figure(
    figure,
    *,
    backend: VisualizationBackend | None = None,
    path: str | Path | None = None,
    filename: str | None = None,
    theme: VisualizationTheme | None = None,
    default_name: str = "visualization",
) -> Path:
    """Persist one backend-native figure and return its resolved output path.

    Explicit ``path`` takes precedence. Otherwise, the theme's
    ``save_directory`` and ``save_format`` define the destination.
    """
    active_theme = resolve_theme(theme, backend)
    resolved_backend = active_theme.backend
    if path is not None and filename is not None:
        raise VisualizationError("Specify either path or filename, not both.")
    if path is not None:
        output_path = Path(path).expanduser()
    else:
        if active_theme.save_directory is None:
            raise VisualizationError(
                "A save path or theme.save_directory is required to export a figure."
            )
        stem = filename or f"{active_theme.filename_prefix}_{default_name}"
        output_path = Path(active_theme.save_directory).expanduser() / stem
    if not output_path.suffix:
        output_path = output_path.with_suffix("." + active_theme.save_format.lstrip("."))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if resolved_backend == "matplotlib":
        try:
            figure.savefig(
                output_path,
                dpi=active_theme.dpi,
                transparent=active_theme.transparent,
                bbox_inches="tight",
            )
        except Exception as error:
            raise VisualizationError(
                f"Could not save Matplotlib figure to {output_path}: {error}"
            ) from error
    else:
        suffix = output_path.suffix.lower()
        try:
            if suffix == ".html":
                figure.write_html(str(output_path), include_plotlyjs="cdn")
            else:
                figure.write_image(str(output_path), scale=1)
        except Exception as error:
            dependency_hint = (
                " Install kaleido for static Plotly image export." if suffix != ".html" else ""
            )
            raise VisualizationError(
                f"Could not save Plotly figure to {output_path}: {error}.{dependency_hint}"
            ) from error
    return output_path


def finalize_figure(
    figure,
    *,
    backend: VisualizationBackend | None = None,
    theme: VisualizationTheme | None = None,
    save_path: str | Path | None = None,
    filename: str | None = None,
    default_name: str = "visualization",
):
    """Optionally export a figure according to explicit or global theme settings."""
    active_theme = resolve_theme(theme, backend)
    if save_path is not None or filename is not None or active_theme.auto_save:
        save_figure(
            figure,
            backend=active_theme.backend,
            path=save_path,
            filename=filename,
            theme=active_theme,
            default_name=default_name,
        )
    return figure
