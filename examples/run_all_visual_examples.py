"""Run all standalone visualization examples in one Python process."""

from __future__ import annotations

import importlib.util
from pathlib import Path

VISUAL_SCRIPTS = (
    "09_visualizations.py",
    "10_visualization_theme.py",
    "11_visualize_method_gallery.py",
    "12_option_model_visual_report.py",
    "13_portfolio_credit_visual_dashboard.py",
    "14_scenario_analysis.py",
    "17_option_chain_analytics.py",
    "18_option_strategy_builder.py",
    "19_portfolio_backtesting.py",
    "20_risk_dashboard.py",
    "22_derivative_calibration.py",
)


def load_example(script_path: Path):
    """Load one visualization example module."""
    module_name = f"qa_visual_example_{script_path.stem.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def close_open_figures() -> None:
    """Close Matplotlib figures opened by one example when Matplotlib is present."""
    try:
        import matplotlib.pyplot as pyplot
    except Exception:
        return
    pyplot.close("all")


def run() -> None:
    """Run the visualization example suite."""
    example_directory = Path(__file__).resolve().parent
    for script_name in VISUAL_SCRIPTS:
        print(f"\n=== {script_name} ===", flush=True)
        load_example(example_directory / script_name).run()
        close_open_figures()


if __name__ == "__main__":
    run()
