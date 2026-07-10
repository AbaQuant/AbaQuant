"""Configurable visualizations for scalar option-pricing model objects."""

from __future__ import annotations

from copy import copy
from pathlib import Path
from typing import Literal

import numpy as np

from abaquant.derivatives.models.diagnostics import (
    current_intrinsic_value,
    model_greeks,
    validate_option_type,
)

from .core import (
    VisualizationBackend,
    VisualizationError,
    VisualizationTheme,
    finalize_figure,
    matplotlib_axes,
    require_matplotlib,
    require_plotly,
    resolve_theme,
    style_matplotlib_axes,
    style_matplotlib_title,
    style_plotly_figure,
)

SurfaceChart = Literal[
    "price_surface",
    "delta_surface",
    "gamma_surface",
    "theta_surface",
    "vega_surface",
    "extrinsic_surface",
]


def _scalar_float(value: object, name: str) -> float:
    """Return one finite scalar float used for a plotting grid."""
    array = np.asarray(value)
    if array.ndim != 0 or not np.isfinite(array.item()):
        raise VisualizationError(
            f"{name} must be a finite scalar to produce a class visualization. "
            "Use the package's vectorized functions for array calculations."
        )
    return float(array.item())


def _price_method(model: object, option_type: str):
    """Resolve one standard call or put pricing method from a model object."""
    method_name = "call_price" if option_type == "call" else "put_price"
    pricing_method = getattr(model, method_name, None)
    if pricing_method is None or not callable(pricing_method):
        raise VisualizationError(f"{type(model).__name__} does not expose {method_name}().")
    return pricing_method


def _option_payoff(spot_prices: np.ndarray, strike_price: float, option_type: str) -> np.ndarray:
    """Return terminal vanilla-option payoff values."""
    return (
        np.maximum(spot_prices - strike_price, 0.0)
        if option_type == "call"
        else np.maximum(strike_price - spot_prices, 0.0)
    )


def _price_profile(model: object, spot_prices: np.ndarray, option_type: str) -> np.ndarray:
    """Reprice one mutable scalar model over a spot-price grid."""
    prices: list[float] = []
    for spot_price in spot_prices:
        repriced_model = copy(model)
        repriced_model.spot_price = float(spot_price)
        prices.append(float(_price_method(repriced_model, option_type)()))
    return np.asarray(prices, dtype=float)


def _extrinsic_profile(model: object, spot_prices: np.ndarray, option_type: str) -> np.ndarray:
    """Return model value minus current intrinsic value over a spot grid."""
    prices = _price_profile(model, spot_prices, option_type)
    strike_price = _scalar_float(getattr(model, "strike_price", None), "strike_price")
    intrinsic_values = _option_payoff(spot_prices, strike_price, option_type)
    return prices - intrinsic_values


def _smile_profile(model: object, strikes: np.ndarray, option_type: str) -> np.ndarray:
    """Use a model's explicit volatility-smile method when available."""
    smile_method = getattr(model, "vol_smile", None)
    if smile_method is None or not callable(smile_method):
        raise VisualizationError(f"{type(model).__name__} does not expose vol_smile(strikes).")
    try:
        values = smile_method(strikes, option_type=option_type)
    except TypeError:
        values = smile_method(strikes)
    return np.asarray(values, dtype=float)


def _volatility_attribute(model: object) -> tuple[str, float]:
    """Resolve the volatility-like attribute varied in surface plots."""
    for attribute_name in ("volatility", "normal_volatility", "initial_volatility"):
        if hasattr(model, attribute_name):
            base_value = _scalar_float(getattr(model, attribute_name), attribute_name)
            if base_value <= 0:
                raise VisualizationError(f"{attribute_name} must be positive for surface plots.")
            return attribute_name, base_value
    raise VisualizationError(
        f"{type(model).__name__} does not expose a scalar volatility-like attribute "
        "supported by surface plots."
    )


def _greek_values(
    model: object, spot_prices: np.ndarray, option_type: str
) -> dict[str, np.ndarray]:
    """Evaluate normalized option-specific Greeks over a spot grid."""
    greek_series: dict[str, list[float]] = {}
    for spot_price in spot_prices:
        repriced_model = copy(model)
        repriced_model.spot_price = float(spot_price)
        greeks = model_greeks(repriced_model, option_type)
        if not greeks:
            raise VisualizationError(
                f"{type(model).__name__} does not expose option Greeks for visualization."
            )
        for greek_name, greek_value in greeks.items():
            greek_series.setdefault(greek_name, []).append(float(greek_value))
    return {name: np.asarray(values, dtype=float) for name, values in greek_series.items()}


def _standardize(values: np.ndarray) -> np.ndarray:
    """Return a standardized array suitable for comparing Greeks on one axis."""
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return values
    scale = np.nanmax(np.abs(finite))
    if not np.isfinite(scale) or scale == 0.0:
        return values
    return values / scale


def _surface_values(
    model: object,
    *,
    spot_prices: np.ndarray,
    volatility_values: np.ndarray,
    volatility_attribute: str,
    chart: SurfaceChart,
    option_type: str,
) -> np.ndarray:
    """Evaluate one two-dimensional option diagnostic over spot and volatility grids."""
    surface = np.empty((len(volatility_values), len(spot_prices)), dtype=float)
    greek_name = chart.replace("_surface", "")
    for row_index, volatility_value in enumerate(volatility_values):
        for column_index, spot_price in enumerate(spot_prices):
            repriced_model = copy(model)
            repriced_model.spot_price = float(spot_price)
            setattr(repriced_model, volatility_attribute, float(volatility_value))
            if chart == "price_surface":
                surface[row_index, column_index] = float(
                    _price_method(repriced_model, option_type)()
                )
            elif chart == "extrinsic_surface":
                surface[row_index, column_index] = float(
                    _price_method(repriced_model, option_type)()
                    - current_intrinsic_value(repriced_model, option_type)
                )
            else:
                greeks = model_greeks(repriced_model, option_type)
                if greek_name not in greeks:
                    raise VisualizationError(
                        f"{type(model).__name__} does not expose {greek_name!r} for a "
                        f"{option_type} option surface."
                    )
                surface[row_index, column_index] = float(greeks[greek_name])
    return surface


def _spot_grid(
    model: object,
    *,
    lower_spot_multiple: float,
    upper_spot_multiple: float,
    grid_size: int,
) -> tuple[float, np.ndarray]:
    """Build a deterministic strike-centered spot grid."""
    strike_price = _scalar_float(getattr(model, "strike_price", None), "strike_price")
    if lower_spot_multiple <= 0 or upper_spot_multiple <= lower_spot_multiple:
        raise VisualizationError("spot multiples must satisfy 0 < lower < upper.")
    if grid_size < 2:
        raise VisualizationError("grid_size must be at least two.")
    return strike_price, np.linspace(
        lower_spot_multiple * strike_price, upper_spot_multiple * strike_price, grid_size
    )


def _volatility_grid(
    model: object,
    *,
    lower_volatility_multiple: float,
    upper_volatility_multiple: float,
    volatility_grid_size: int,
) -> tuple[str, np.ndarray]:
    """Build a deterministic volatility grid for surface visualizations."""
    volatility_attribute, base_volatility = _volatility_attribute(model)
    if lower_volatility_multiple <= 0 or upper_volatility_multiple <= lower_volatility_multiple:
        raise VisualizationError("volatility multiples must satisfy 0 < lower < upper.")
    if volatility_grid_size < 2:
        raise VisualizationError("volatility_grid_size must be at least two.")
    return volatility_attribute, np.linspace(
        lower_volatility_multiple * base_volatility,
        upper_volatility_multiple * base_volatility,
        volatility_grid_size,
    )


def visualize_option_model(
    model: object,
    *,
    option_type: Literal["call", "put"] = "call",
    chart: str = "payoff",
    backend: VisualizationBackend | None = None,
    theme: VisualizationTheme | None = None,
    save_path: str | Path | None = None,
    filename: str | None = None,
    lower_spot_multiple: float = 0.5,
    upper_spot_multiple: float = 1.5,
    grid_size: int = 101,
    lower_volatility_multiple: float = 0.5,
    upper_volatility_multiple: float = 1.5,
    volatility_grid_size: int = 31,
    greek_scale: Literal["raw", "standardized"] = "raw",
):
    """Visualize one scalar option-pricing model using the active theme.

    Parameters
    ----------
    model : object
        Scalar model exposing ``spot_price`` and ``strike_price``. Value charts
        require ``call_price()`` and ``put_price()``. Greek charts additionally
        require ``greeks()``.
    option_type : {"call", "put"}, default="call"
        Vanilla payoff, value, decomposition, and Greek family to display.
    chart : str, default="payoff"
        Requested visual diagnostic. Supported values are ``"payoff"``,
        ``"price_profile"``, ``"extrinsic_value"``, ``"greeks"``,
        ``"volatility_smile"``, ``"tree"``, ``"price_surface"``,
        ``"extrinsic_surface"``, ``"delta_surface"``, ``"gamma_surface"``,
        ``"theta_surface"``, and ``"vega_surface"``.
    backend : {"matplotlib", "plotly"}, optional
        Per-call backend override. When omitted, ``theme.backend`` is used.
    theme : VisualizationTheme, optional
        Per-call style and export override. When omitted, the global theme is
        used.
    save_path : str or pathlib.Path, optional
        Explicit export path. A filename extension selects the export format.
    filename : str, optional
        Filename relative to ``theme.save_directory``.
    lower_spot_multiple, upper_spot_multiple : float, default=0.5, 1.5
        Spot-grid bounds expressed as multiples of the strike price.
    grid_size : int, default=101
        Number of spot points for curves and the surface x-axis.
    lower_volatility_multiple, upper_volatility_multiple : float, default=0.5, 1.5
        Volatility-grid bounds expressed as multiples of the model's base
        volatility-like attribute.
    volatility_grid_size : int, default=31
        Number of volatility points for surface charts.
    greek_scale : {"raw", "standardized"}, default="raw"
        Scaling mode for the multi-Greek curve chart. ``"standardized"``
        divides each Greek by its maximum absolute value over the spot grid.

    Returns
    -------
    matplotlib.figure.Figure or plotly.graph_objects.Figure
        Styled backend-native figure object. The figure is optionally saved but
        is never shown automatically.
    """
    active_theme = resolve_theme(theme, backend)
    validated_option_type = validate_option_type(option_type)
    strike_price, x_values = _spot_grid(
        model,
        lower_spot_multiple=lower_spot_multiple,
        upper_spot_multiple=upper_spot_multiple,
        grid_size=grid_size,
    )
    if chart == "tree":
        figure = _visualize_tree(model, option_type=validated_option_type, theme=active_theme)
    elif chart in {
        "price_surface",
        "delta_surface",
        "gamma_surface",
        "theta_surface",
        "vega_surface",
        "extrinsic_surface",
    }:
        volatility_attribute, volatility_values = _volatility_grid(
            model,
            lower_volatility_multiple=lower_volatility_multiple,
            upper_volatility_multiple=upper_volatility_multiple,
            volatility_grid_size=volatility_grid_size,
        )
        surface = _surface_values(
            model,
            spot_prices=x_values,
            volatility_values=volatility_values,
            volatility_attribute=volatility_attribute,
            chart=chart,  # type: ignore[arg-type]
            option_type=validated_option_type,
        )
        title = _surface_title(model, chart, validated_option_type, volatility_attribute)
        y_label = volatility_attribute.replace("_", " ").title()
        z_label = _surface_z_label(chart)
        figure = _plot_surface(
            x_values,
            volatility_values,
            surface,
            title=title,
            x_label="Current underlying price",
            y_label=y_label,
            z_label=z_label,
            theme=active_theme,
        )
    else:
        figure = _visualize_curve(
            model,
            option_type=validated_option_type,
            chart=chart,
            x_values=x_values,
            strike_price=strike_price,
            theme=active_theme,
            greek_scale=greek_scale,
        )
    return finalize_figure(
        figure,
        backend=active_theme.backend,
        theme=active_theme,
        save_path=save_path,
        filename=filename,
        default_name=f"{type(model).__name__}_{chart}",
    )


def _visualize_curve(
    model: object,
    *,
    option_type: str,
    chart: str,
    x_values: np.ndarray,
    strike_price: float,
    theme: VisualizationTheme,
    greek_scale: str,
):
    """Render one two-dimensional option diagnostic curve."""
    if chart == "volatility_smile":
        y_values = _smile_profile(model, x_values, option_type)
        title = f"{type(model).__name__} implied-volatility smile ({option_type})"
        x_label, y_label = "Strike price", "Implied volatility"
        series = {option_type.title(): y_values}
    elif chart == "payoff":
        y_values = _option_payoff(x_values, strike_price, option_type)
        title = f"{type(model).__name__} terminal payoff ({option_type})"
        x_label, y_label = "Underlying price at expiry", "Payoff"
        series = {option_type.title(): y_values}
    elif chart == "price_profile":
        y_values = _price_profile(model, x_values, option_type)
        title = f"{type(model).__name__} option value profile ({option_type})"
        x_label, y_label = "Current underlying price", "Model option value"
        series = {option_type.title(): y_values}
    elif chart == "extrinsic_value":
        y_values = _extrinsic_profile(model, x_values, option_type)
        title = f"{type(model).__name__} extrinsic value profile ({option_type})"
        x_label, y_label = "Current underlying price", "Extrinsic value"
        series = {"Extrinsic value": y_values}
    elif chart == "greeks":
        greeks = _greek_values(model, x_values, option_type)
        if greek_scale == "standardized":
            greeks = {name: _standardize(values) for name, values in greeks.items()}
            y_label = "Standardized Greek value"
        elif greek_scale == "raw":
            y_label = "Greek value"
        else:
            raise VisualizationError("greek_scale must be 'raw' or 'standardized'.")
        title = f"{type(model).__name__} Greeks across spot ({option_type})"
        x_label = "Current underlying price"
        series = {name.title(): values for name, values in greeks.items()}
    else:
        raise VisualizationError(f"Unsupported option chart: {chart!r}.")
    return _plot_lines(
        x_values,
        series,
        title=title,
        x_label=x_label,
        y_label=y_label,
        strike_price=strike_price,
        theme=theme,
    )


def _plot_lines(
    x_values: np.ndarray,
    series: dict[str, np.ndarray],
    *,
    title: str,
    x_label: str,
    y_label: str,
    strike_price: float,
    theme: VisualizationTheme,
):
    """Plot one or more line series using the configured backend."""
    if theme.backend == "matplotlib":
        pyplot = require_matplotlib()
        figure, axes = matplotlib_axes(pyplot, theme)
        style_matplotlib_axes(axes, theme)
        for label, y_values in series.items():
            axes.plot(x_values, y_values, label=label, linewidth=theme.line_width)
        axes.axvline(
            strike_price,
            linestyle="--",
            label="Strike",
            color=theme.color_sequence[1 % len(theme.color_sequence)],
        )
        style_matplotlib_title(axes, title, theme)
        axes.set_xlabel(x_label)
        axes.set_ylabel(y_label)
        axes.legend(prop={"family": theme.font_family, "size": theme.base_font_size})
        figure.tight_layout()
        return figure
    graph_objects = require_plotly()
    figure = graph_objects.Figure()
    for label, y_values in series.items():
        figure.add_scatter(
            x=x_values,
            y=y_values,
            mode="lines",
            name=label,
            line={"width": theme.line_width},
        )
    figure.add_vline(x=strike_price, line_dash="dash", annotation_text="Strike")
    return style_plotly_figure(figure, theme, title=title, xaxis_title=x_label, yaxis_title=y_label)


def _surface_title(model: object, chart: str, option_type: str, volatility_attribute: str) -> str:
    """Return a concise surface chart title."""
    chart_name = chart.replace("_", " ").title()
    volatility_name = volatility_attribute.replace("_", " ")
    return f"{type(model).__name__} {chart_name} ({option_type}, {volatility_name})"


def _surface_z_label(chart: str) -> str:
    """Return the z-axis label associated with one surface chart."""
    labels = {
        "price_surface": "Model option value",
        "extrinsic_surface": "Extrinsic value",
        "delta_surface": "Delta",
        "gamma_surface": "Gamma",
        "theta_surface": "Theta",
        "vega_surface": "Vega",
    }
    return labels[chart]


def _plot_surface(
    x_values: np.ndarray,
    y_values: np.ndarray,
    z_values: np.ndarray,
    *,
    title: str,
    x_label: str,
    y_label: str,
    z_label: str,
    theme: VisualizationTheme,
):
    """Plot a three-dimensional surface using Matplotlib or Plotly."""
    mesh_x, mesh_y = np.meshgrid(x_values, y_values)
    if theme.backend == "matplotlib":
        pyplot = require_matplotlib()
        figure = pyplot.figure(
            figsize=theme.figure_size,
            dpi=theme.dpi,
            facecolor=theme.background_color,
        )
        axes = figure.add_subplot(111, projection="3d")
        axes.set_facecolor(theme.background_color)
        axes.plot_surface(mesh_x, mesh_y, z_values, linewidth=0, antialiased=True, alpha=0.92)
        axes.set_xlabel(x_label, fontname=theme.font_family, fontsize=theme.base_font_size)
        axes.set_ylabel(y_label, fontname=theme.font_family, fontsize=theme.base_font_size)
        axes.set_zlabel(z_label, fontname=theme.font_family, fontsize=theme.base_font_size)
        axes.set_title(title, fontname=theme.font_family, fontsize=theme.title_font_size)
        figure.tight_layout()
        return figure
    graph_objects = require_plotly()
    figure = graph_objects.Figure(data=[graph_objects.Surface(x=mesh_x, y=mesh_y, z=z_values)])
    style_plotly_figure(figure, theme, title=title, xaxis_title=x_label, yaxis_title=z_label)
    figure.update_layout(
        scene={
            "xaxis_title": x_label,
            "yaxis_title": y_label,
            "zaxis_title": z_label,
        }
    )
    return figure


def _visualize_tree(model: object, *, option_type: str, theme: VisualizationTheme):
    """Render a small recombining option-value lattice using one theme."""
    full_tree = getattr(model, "full_tree", None)
    if full_tree is None or not callable(full_tree):
        raise VisualizationError(
            f"{type(model).__name__} does not expose full_tree(); tree visualization is unsupported."
        )
    _underlying_tree, option_tree = full_tree(option_type=option_type)
    points_x: list[int] = []
    points_y: list[float] = []
    for time_index, node_values in enumerate(option_tree):
        for node_value in np.asarray(node_values, dtype=float).ravel():
            points_x.append(time_index)
            points_y.append(float(node_value))
    title = f"{type(model).__name__} option-value lattice ({option_type})"
    if theme.backend == "matplotlib":
        pyplot = require_matplotlib()
        figure, axes = matplotlib_axes(pyplot, theme)
        style_matplotlib_axes(axes, theme)
        axes.scatter(points_x, points_y, s=theme.marker_size**2)
        style_matplotlib_title(axes, title, theme)
        axes.set_xlabel("Tree time step")
        axes.set_ylabel("Option value")
        figure.tight_layout()
        return figure
    graph_objects = require_plotly()
    figure = graph_objects.Figure()
    figure.add_scatter(
        x=points_x,
        y=points_y,
        mode="markers",
        name="Option nodes",
        marker={"size": theme.marker_size},
    )
    return style_plotly_figure(
        figure, theme, title=title, xaxis_title="Tree time step", yaxis_title="Option value"
    )


def visualize_derivative_scenario_grid(
    scenario_grid: object,
    *,
    metric: str = "price",
    chart: Literal["surface", "heatmap", "curves"] = "surface",
    backend: VisualizationBackend | None = None,
    theme: VisualizationTheme | None = None,
    save_path: str | Path | None = None,
    filename: str | None = None,
):
    """Visualize a derivative spot--volatility scenario grid.

    Parameters
    ----------
    scenario_grid : object
        Object exposing a long-form ``data`` DataFrame with ``spot_price``,
        ``volatility``, and the selected metric column.
    metric : str, default="price"
        Scenario metric to display.
    chart : {"surface", "heatmap", "curves"}, default="surface"
        Visual form for the scenario table.
    backend : {"matplotlib", "plotly"}, optional
        Per-call backend override.
    theme : VisualizationTheme, optional
        Per-call style override.
    save_path : str or pathlib.Path, optional
        Explicit export path.
    filename : str, optional
        Filename relative to the active theme's save directory.

    Returns
    -------
    matplotlib.figure.Figure or plotly.graph_objects.Figure
        Backend-native figure object.
    """
    active_theme = resolve_theme(theme, backend)
    data = getattr(scenario_grid, "data", None)
    if data is None or metric not in data.columns:
        raise VisualizationError(f"scenario_grid must expose metric column {metric!r}.")
    if chart not in {"surface", "heatmap", "curves"}:
        raise VisualizationError("chart must be 'surface', 'heatmap', or 'curves'.")
    pivot = data.pivot(index="volatility", columns="spot_price", values=metric).sort_index()
    pivot = pivot.reindex(sorted(pivot.columns), axis=1)
    x_values = np.asarray(pivot.columns, dtype=float)
    y_values = np.asarray(pivot.index, dtype=float)
    z_values = pivot.to_numpy(dtype=float)
    title = f"Derivative scenario {metric.replace('_', ' ')}"
    if chart == "surface":
        figure = _plot_surface(
            x_values,
            y_values,
            z_values,
            title=title,
            x_label="Current underlying price",
            y_label="Volatility",
            z_label=metric.replace("_", " ").title(),
            theme=active_theme,
        )
    elif chart == "curves":
        series = {
            f"vol={volatility:.3g}": pivot.loc[volatility].to_numpy(dtype=float)
            for volatility in pivot.index
        }
        figure = _plot_lines(
            x_values,
            series,
            title=title,
            x_label="Current underlying price",
            y_label=metric.replace("_", " ").title(),
            strike_price=float(np.nanmedian(x_values)),
            theme=active_theme,
        )
    else:
        figure = _plot_heatmap(
            x_values,
            y_values,
            z_values,
            title=title,
            x_label="Current underlying price",
            y_label="Volatility",
            value_label=metric.replace("_", " ").title(),
            theme=active_theme,
        )
    return finalize_figure(
        figure,
        backend=active_theme.backend,
        theme=active_theme,
        save_path=save_path,
        filename=filename,
        default_name=f"derivative_scenario_{metric}_{chart}",
    )


def _plot_heatmap(
    x_values: np.ndarray,
    y_values: np.ndarray,
    z_values: np.ndarray,
    *,
    title: str,
    x_label: str,
    y_label: str,
    value_label: str,
    theme: VisualizationTheme,
):
    """Plot a two-dimensional scenario heatmap using Matplotlib or Plotly."""
    if theme.backend == "matplotlib":
        pyplot = require_matplotlib()
        figure, axes = matplotlib_axes(pyplot, theme)
        image = axes.imshow(
            z_values,
            aspect="auto",
            origin="lower",
            extent=(x_values.min(), x_values.max(), y_values.min(), y_values.max()),
        )
        style_matplotlib_title(axes, title, theme)
        axes.set_xlabel(x_label)
        axes.set_ylabel(y_label)
        figure.colorbar(image, ax=axes, label=value_label)
        figure.tight_layout()
        return figure
    graph_objects = require_plotly()
    figure = graph_objects.Figure(
        data=graph_objects.Heatmap(
            x=x_values, y=y_values, z=z_values, colorbar={"title": value_label}
        )
    )
    return style_plotly_figure(
        figure,
        theme,
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
    )


def visualize_option_chain_analytics(
    analytics: object,
    *,
    chart: Literal[
        "iv_smile", "iv_surface", "term_structure", "rich_cheap", "open_interest_heatmap"
    ] = "iv_smile",
    option_type: Literal["call", "put"] = "call",
    metric: str = "implied_volatility",
    backend: VisualizationBackend | None = None,
    theme: VisualizationTheme | None = None,
    save_path: str | Path | None = None,
    filename: str | None = None,
    **kwargs: object,
):
    """Visualize listed-option-chain analytics with the active theme.

    Parameters
    ----------
    analytics : object
        Option-chain analytics object exposing ``iv_smile``, ``iv_surface``,
        ``term_structure``, ``rich_cheap_table``, and ``open_interest_grid``.
    chart : {"iv_smile", "iv_surface", "term_structure", "rich_cheap", "open_interest_heatmap"}, default="iv_smile"
        Chain diagnostic to render.
    option_type : {"call", "put"}, default="call"
        Option family used by diagnostics that accept an option-family filter.
    metric : str, default="implied_volatility"
        Metric displayed by surface charts.
    backend : {"matplotlib", "plotly"}, optional
        Per-call backend override.
    theme : VisualizationTheme, optional
        Per-call style override.
    save_path : str or pathlib.Path, optional
        Explicit output path.
    filename : str, optional
        Filename relative to the active theme save directory.
    **kwargs : object
        Additional keyword arguments forwarded to the requested analytic table.

    Returns
    -------
    matplotlib.figure.Figure or plotly.graph_objects.Figure
        Backend-native figure object.
    """
    active_theme = resolve_theme(theme, backend)
    if chart == "iv_smile":
        table = analytics.iv_smile(option_type=option_type, **kwargs)
        figure = _plot_option_chain_lines(
            table,
            x_column="moneyness",
            y_columns={"implied_volatility": "Implied volatility"},
            title=f"{getattr(analytics.ticker, 'symbol', 'Ticker')} IV smile ({option_type})",
            x_label="Moneyness (spot / strike)",
            y_label="Implied volatility",
            theme=active_theme,
        )
    elif chart == "iv_surface":
        table = analytics.iv_surface(option_type=option_type, **kwargs)
        if metric not in table.columns:
            raise VisualizationError(f"Option-chain surface has no metric column {metric!r}.")
        pivot = table.pivot_table(
            index="days_to_expiry", columns="moneyness", values=metric, aggfunc="mean"
        )
        pivot = pivot.sort_index().reindex(sorted(pivot.columns), axis=1)
        figure = _plot_heatmap(
            np.asarray(pivot.columns, dtype=float),
            np.asarray(pivot.index, dtype=float),
            pivot.to_numpy(dtype=float),
            title=f"{getattr(analytics.ticker, 'symbol', 'Ticker')} {metric.replace('_', ' ')} surface ({option_type})",
            x_label="Moneyness (spot / strike)",
            y_label="Days to expiry",
            value_label=metric.replace("_", " ").title(),
            theme=active_theme,
        )
    elif chart == "term_structure":
        table = analytics.term_structure(option_type=option_type, **kwargs)
        figure = _plot_option_chain_lines(
            table,
            x_column="days_to_expiry",
            y_columns={"implied_volatility": "Implied volatility"},
            title=f"{getattr(analytics.ticker, 'symbol', 'Ticker')} IV term structure ({option_type})",
            x_label="Days to expiry",
            y_label="Implied volatility",
            theme=active_theme,
        )
    elif chart == "rich_cheap":
        table = analytics.rich_cheap_table(option_type=option_type, **kwargs)
        figure = _plot_option_chain_bar(
            table.head(20),
            x_column="strike",
            y_column="rich_cheap",
            title=f"{getattr(analytics.ticker, 'symbol', 'Ticker')} rich/cheap by strike ({option_type})",
            x_label="Strike price",
            y_label="Market minus model value",
            theme=active_theme,
        )
    elif chart == "open_interest_heatmap":
        table = analytics.open_interest_grid(option_type=option_type, **kwargs)
        pivot = table.pivot_table(
            index="days_to_expiry", columns="strike", values="open_interest", aggfunc="sum"
        )
        pivot = pivot.sort_index().reindex(sorted(pivot.columns), axis=1)
        figure = _plot_heatmap(
            np.asarray(pivot.columns, dtype=float),
            np.asarray(pivot.index, dtype=float),
            pivot.to_numpy(dtype=float),
            title=f"{getattr(analytics.ticker, 'symbol', 'Ticker')} open interest heatmap ({option_type})",
            x_label="Strike price",
            y_label="Days to expiry",
            value_label="Open interest",
            theme=active_theme,
        )
    else:
        raise VisualizationError(f"Unsupported option-chain analytics chart: {chart!r}.")
    return finalize_figure(
        figure,
        backend=active_theme.backend,
        theme=active_theme,
        save_path=save_path,
        filename=filename,
        default_name=f"option_chain_{chart}",
    )


def _plot_option_chain_lines(
    table,
    *,
    x_column: str,
    y_columns: dict[str, str],
    title: str,
    x_label: str,
    y_label: str,
    theme: VisualizationTheme,
):
    """Plot one or more option-chain line diagnostics."""
    if table.empty:
        raise VisualizationError("option-chain analytic table is empty.")
    if theme.backend == "matplotlib":
        pyplot = require_matplotlib()
        figure, axes = matplotlib_axes(pyplot, theme)
        style_matplotlib_axes(axes, theme)
        for column, label in y_columns.items():
            axes.plot(
                table[x_column], table[column], label=label, linewidth=theme.line_width, marker="o"
            )
        style_matplotlib_title(axes, title, theme)
        axes.set_xlabel(x_label)
        axes.set_ylabel(y_label)
        axes.legend(prop={"family": theme.font_family, "size": theme.base_font_size})
        figure.tight_layout()
        return figure
    graph_objects = require_plotly()
    figure = graph_objects.Figure()
    for column, label in y_columns.items():
        figure.add_scatter(
            x=table[x_column],
            y=table[column],
            mode="lines+markers",
            name=label,
            line={"width": theme.line_width},
            marker={"size": theme.marker_size},
        )
    return style_plotly_figure(figure, theme, title=title, xaxis_title=x_label, yaxis_title=y_label)


def _plot_option_chain_bar(
    table,
    *,
    x_column: str,
    y_column: str,
    title: str,
    x_label: str,
    y_label: str,
    theme: VisualizationTheme,
):
    """Plot a contract-level option-chain bar diagnostic."""
    if table.empty:
        raise VisualizationError("option-chain analytic table is empty.")
    x_values = [str(value) for value in table[x_column]]
    y_values = table[y_column].to_numpy(dtype=float)
    if theme.backend == "matplotlib":
        pyplot = require_matplotlib()
        figure, axes = matplotlib_axes(pyplot, theme)
        style_matplotlib_axes(axes, theme, grid_axis="y")
        axes.bar(x_values, y_values)
        style_matplotlib_title(axes, title, theme)
        axes.set_xlabel(x_label)
        axes.set_ylabel(y_label)
        figure.tight_layout()
        return figure
    graph_objects = require_plotly()
    figure = graph_objects.Figure(data=graph_objects.Bar(x=x_values, y=y_values))
    return style_plotly_figure(figure, theme, title=title, xaxis_title=x_label, yaxis_title=y_label)


def visualize_option_strategy(
    strategy: object,
    *,
    chart: str = "payoff",
    backend: VisualizationBackend | None = None,
    theme: VisualizationTheme | None = None,
    save_path: str | Path | None = None,
    filename: str | None = None,
    spot_min: float | None = None,
    spot_max: float | None = None,
    points: int = 501,
):
    """Visualize a composable option strategy payoff profile.

    Parameters
    ----------
    strategy : object
        Strategy object exposing ``profile(...)`` and ``break_even_points()``.
    chart : {"payoff", "components"}, default="payoff"
        ``"payoff"`` plots aggregate net profit. ``"components"`` also plots
        each leg's net profit contribution.
    backend : {"matplotlib", "plotly"}, optional
        Backend override.
    theme : VisualizationTheme, optional
        Per-call style override.
    save_path : str or pathlib.Path, optional
        Explicit export path.
    filename : str, optional
        Filename relative to the active theme's save directory.
    spot_min, spot_max : float, optional
        Terminal-price grid bounds.
    points : int, default=501
        Number of grid points for the payoff table.

    Returns
    -------
    matplotlib.figure.Figure or plotly.graph_objects.Figure
        Backend-native figure object.
    """
    if chart not in {"payoff", "components"}:
        raise VisualizationError("strategy chart must be 'payoff' or 'components'.")
    active_theme = resolve_theme(theme, backend)
    profile = strategy.profile(spot_min=spot_min, spot_max=spot_max, points=points)
    x_values = profile["spot_price"].to_numpy(dtype=float)
    series = {"Net profit": profile["net_profit"].to_numpy(dtype=float)}
    if chart == "components":
        for column in profile.columns:
            if column.startswith("leg_"):
                label = column.removeprefix("leg_").replace("_", " ")
                series[label] = profile[column].to_numpy(dtype=float)
    title = f"{getattr(strategy, 'name', type(strategy).__name__)} payoff profile"
    figure = _plot_strategy_lines(
        x_values,
        series,
        break_even_points=list(strategy.break_even_points()),
        title=title,
        x_label="Underlying price at expiry",
        y_label="Net profit",
        theme=active_theme,
    )
    return finalize_figure(
        figure,
        backend=active_theme.backend,
        theme=active_theme,
        save_path=save_path,
        filename=filename,
        default_name=f"{type(strategy).__name__}_{chart}",
    )


def _plot_strategy_lines(
    x_values: np.ndarray,
    series: dict[str, np.ndarray],
    *,
    break_even_points: list[float],
    title: str,
    x_label: str,
    y_label: str,
    theme: VisualizationTheme,
):
    """Render an option-strategy line chart using the configured backend."""
    if theme.backend == "matplotlib":
        pyplot = require_matplotlib()
        figure, axes = matplotlib_axes(pyplot, theme)
        style_matplotlib_axes(axes, theme)
        for label, y_values in series.items():
            axes.plot(x_values, y_values, label=label, linewidth=theme.line_width)
        axes.axhline(0.0, linestyle="--", color=theme.grid_color, linewidth=1.0)
        for break_even in break_even_points:
            axes.axvline(
                break_even,
                linestyle=":",
                color=theme.color_sequence[1 % len(theme.color_sequence)],
                linewidth=1.0,
            )
        style_matplotlib_title(axes, title, theme)
        axes.set_xlabel(x_label)
        axes.set_ylabel(y_label)
        axes.legend(prop={"family": theme.font_family, "size": theme.base_font_size})
        figure.tight_layout()
        return figure
    graph_objects = require_plotly()
    figure = graph_objects.Figure()
    for label, y_values in series.items():
        figure.add_scatter(
            x=x_values,
            y=y_values,
            mode="lines",
            name=label,
            line={"width": theme.line_width},
        )
    figure.add_hline(y=0.0, line_dash="dash")
    for break_even in break_even_points:
        figure.add_vline(x=break_even, line_dash="dot", annotation_text="Break-even")
    return style_plotly_figure(figure, theme, title=title, xaxis_title=x_label, yaxis_title=y_label)


def visualize_calibration_result(
    calibration_result: object,
    *,
    chart: Literal["model_vs_market", "residuals", "parameters"] = "model_vs_market",
    backend: VisualizationBackend | None = None,
    theme: VisualizationTheme | None = None,
    save_path: str | Path | None = None,
    filename: str | None = None,
):
    """Visualize an option-model calibration result.

    Parameters
    ----------
    calibration_result : object
        Calibration result exposing ``model_data`` and ``parameter_table()``.
    chart : {"model_vs_market", "residuals", "parameters"}, default="model_vs_market"
        Diagnostic to render. ``"model_vs_market"`` compares the fitted model
        with observed market values, ``"residuals"`` shows fit errors by strike,
        and ``"parameters"`` displays calibrated parameter values.
    backend : {"matplotlib", "plotly"}, optional
        Per-call backend override.
    theme : VisualizationTheme, optional
        Per-call style override.
    save_path : str or pathlib.Path, optional
        Explicit export path.
    filename : str, optional
        Filename relative to the active theme save directory.

    Returns
    -------
    matplotlib.figure.Figure or plotly.graph_objects.Figure
        Backend-native figure object.
    """
    active_theme = resolve_theme(theme, backend)
    model_name = getattr(calibration_result, "model_name", "calibration")
    if chart == "model_vs_market":
        table = getattr(calibration_result, "model_data", None)
        if table is None or table.empty:
            raise VisualizationError("calibration_result.model_data must be a non-empty DataFrame.")
        figure = _plot_option_chain_lines(
            table,
            x_column="strike",
            y_columns={"market_value": "Market", "model_value": "Model"},
            title=f"{str(model_name).upper()} calibration model versus market",
            x_label="Strike price",
            y_label=str(getattr(calibration_result, "objective", "value"))
            .replace("_", " ")
            .title(),
            theme=active_theme,
        )
    elif chart == "residuals":
        table = getattr(calibration_result, "model_data", None)
        if table is None or table.empty:
            raise VisualizationError("calibration_result.model_data must be a non-empty DataFrame.")
        figure = _plot_option_chain_bar(
            table,
            x_column="strike",
            y_column="residual",
            title=f"{str(model_name).upper()} calibration residuals",
            x_label="Strike price",
            y_label="Model minus market",
            theme=active_theme,
        )
    elif chart == "parameters":
        parameter_table = calibration_result.parameter_table()
        if parameter_table.empty:
            raise VisualizationError(
                "calibration_result.parameter_table() returned an empty table."
            )
        figure = _plot_option_chain_bar(
            parameter_table,
            x_column="parameter",
            y_column="value",
            title=f"{str(model_name).upper()} calibrated parameters",
            x_label="Parameter",
            y_label="Value",
            theme=active_theme,
        )
    else:
        raise VisualizationError(
            "calibration chart must be 'model_vs_market', 'residuals', or 'parameters'."
        )
    return finalize_figure(
        figure,
        backend=active_theme.backend,
        theme=active_theme,
        save_path=save_path,
        filename=filename,
        default_name=f"calibration_{model_name}_{chart}",
    )
