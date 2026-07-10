"""Configurable optional plotting utilities for abaquant objects.

Set a project-wide :class:`VisualizationTheme` once with
:func:`configure_visualization`; every supported ``visualize`` method then
uses that template unless a per-call override is supplied.
"""

from .core import (
    VisualizationBackend,
    VisualizationError,
    VisualizationTheme,
    configure_visualization,
    finalize_figure,
    get_visualization_theme,
    reset_visualization_theme,
    save_figure,
    visualization_theme,
)
from .credit import visualize_credit_assessment, visualize_credit_scenario
from .dashboard import visualize_risk_dashboard
from .market import visualize_financial_snapshot, visualize_price_history
from .options import (
    visualize_calibration_result,
    visualize_derivative_scenario_grid,
    visualize_option_chain_analytics,
    visualize_option_model,
    visualize_option_strategy,
)
from .portfolio import (
    visualize_portfolio_allocator,
    visualize_portfolio_backtest,
    visualize_portfolio_scenario,
)

__all__ = [
    "VisualizationBackend",
    "VisualizationError",
    "VisualizationTheme",
    "configure_visualization",
    "finalize_figure",
    "get_visualization_theme",
    "reset_visualization_theme",
    "save_figure",
    "visualization_theme",
    "visualize_calibration_result",
    "visualize_credit_assessment",
    "visualize_credit_scenario",
    "visualize_derivative_scenario_grid",
    "visualize_financial_snapshot",
    "visualize_option_chain_analytics",
    "visualize_option_model",
    "visualize_option_strategy",
    "visualize_portfolio_allocator",
    "visualize_portfolio_backtest",
    "visualize_portfolio_scenario",
    "visualize_price_history",
    "visualize_risk_dashboard",
]
