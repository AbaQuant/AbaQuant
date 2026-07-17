"""Run deterministic non-live examples in one Python process."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

CORE_SCRIPTS = (
    "00_import_all_public_modules.py",
    "01_derivatives.py",
    "02_financial_math.py",
    "03_derivatives_advanced_models.py",
    "04_credit_risk.py",
    "05_portfolio_optimization.py",
    "06_marketdata_offline.py",
    "08_root_facades.py",
    "manual_credit_proxy_example.py",
    "cached_financials_credit_example.py",
    "applied_marketdata_ticker_options.py",
    "applied_marketdata_universe_portfolio.py",
    "15_sec_xbrl_fundamentals.py",
    "16_fred_rate_curve.py",
    "17_option_chain_analytics.py",
    "18_option_strategy_builder.py",
    "19_portfolio_backtesting.py",
    "20_risk_dashboard.py",
    "21_exportable_reports.py",
    "22_derivative_calibration.py",
    "23_data_provenance.py",
)

VISUAL_SCRIPTS = (
    "09_visualizations.py",
    "10_visualization_theme.py",
    "11_visualize_method_gallery.py",
    "12_option_model_visual_report.py",
    "13_portfolio_credit_visual_dashboard.py",
    "14_scenario_analysis.py",
)


def parse_args() -> argparse.Namespace:
    """Parse runner options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--include-visuals", action="store_true", help="Also run visualization galleries."
    )
    return parser.parse_args()


def load_example(script_path: Path):
    """Load one example script as an isolated module object."""
    module_name = f"qa_example_{script_path.stem.replace('-', '_')}"
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


def run_script(script_path: Path) -> None:
    """Load one example script and execute its ``run`` function."""
    print(f"\n=== {script_path.name} ===", flush=True)
    module = load_example(script_path)
    run_function = getattr(module, "run", None)
    if not callable(run_function):
        raise RuntimeError(f"{script_path.name} does not expose run().")
    run_function()
    close_open_figures()


def run() -> None:
    """Run selected deterministic examples in a fixed order."""
    args = parse_args()
    example_directory = Path(__file__).resolve().parent
    scripts = CORE_SCRIPTS + (VISUAL_SCRIPTS if args.include_visuals else ())
    for script_name in scripts:
        run_script(example_directory / script_name)


if __name__ == "__main__":
    run()
