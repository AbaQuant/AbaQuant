from __future__ import annotations

import inspect
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

import abaquant as quact
from tests.cases import CASES

RESULTS_PATH = Path(__file__).parent / "fixtures" / "results.json"
FLOAT_RELATIVE_TOLERANCE = 1e-7
# SLSQP/calibration results can differ by a few nanounits across Python/SciPy
# builds while preserving the same economic result and API shape.
FLOAT_ABSOLUTE_TOLERANCE = 1e-8
CASE_ABSOLUTE_TOLERANCE = {
    # This fixture deliberately stops L-BFGS-B after two iterations. Different
    # SciPy/OpenBLAS builds can end a few micro-units apart on that unfinished step.
    "calibrate_sabr": 1e-5,
    # The MVSK optimizer is solved with SLSQP. Python/SciPy builds can stop at
    # slightly different feasible points on this very flat objective.
    "mvsk_portfolio": 1e-7,
}


@pytest.fixture(scope="module")
def saved_results() -> dict[str, Any]:
    return json.loads(RESULTS_PATH.read_text(encoding="utf-8"))


NON_DETERMINISTIC_OR_FACADE_FUNCTIONS = {
    "build_backtest_report",
    "build_credit_report",
    "build_option_model_report",
    "build_portfolio_allocator_report",
    "build_risk_dashboard_report",
    "configure_visualization",
    "finalize_figure",
    "generated_metadata",
    "get_ticker",
    "get_tickers",
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
}


def public_function_names() -> set[str]:
    """Return deterministic scalar/table functions covered by saved-result fixtures."""
    return {
        name
        for name in quact.__all__
        if inspect.isfunction(getattr(quact, name, None))
        and name not in NON_DETERMINISTIC_OR_FACADE_FUNCTIONS
    }


def normalize_result(value: Any) -> Any:
    if isinstance(value, pd.DataFrame):
        return {
            "columns": list(value.columns),
            "records": normalize_result(value.to_dict("records")),
        }

    if isinstance(value, pd.Series):
        return normalize_result(value.to_dict())

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if isinstance(value, np.ndarray):
        return normalize_result(value.tolist())

    if isinstance(value, np.generic):
        return normalize_result(value.item())

    if isinstance(value, tuple):
        return [normalize_result(item) for item in value]

    if isinstance(value, list):
        return [normalize_result(item) for item in value]

    if isinstance(value, dict):
        return {str(key): normalize_result(item) for key, item in value.items()}

    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
        return value

    return value


def assert_matches_saved_result(
    actual: Any,
    expected: Any,
    *,
    absolute_tolerance: float = FLOAT_ABSOLUTE_TOLERANCE,
) -> None:
    if isinstance(expected, dict):
        assert set(actual) == set(expected)
        for key, value in expected.items():
            assert_matches_saved_result(actual[key], value, absolute_tolerance=absolute_tolerance)
        return

    if isinstance(expected, list):
        assert len(actual) == len(expected)
        for actual_item, expected_item in zip(actual, expected, strict=True):
            assert_matches_saved_result(
                actual_item, expected_item, absolute_tolerance=absolute_tolerance
            )
        return

    if isinstance(expected, float):
        assert actual == pytest.approx(
            expected,
            rel=FLOAT_RELATIVE_TOLERANCE,
            abs=absolute_tolerance,
        )
        return

    assert actual == expected


def test_every_public_function_has_a_saved_result_case() -> None:
    assert set(CASES) == public_function_names()


@pytest.mark.parametrize("function_name", sorted(CASES))
def test_function_matches_saved_result(function_name: str, saved_results: dict[str, Any]) -> None:
    actual = normalize_result(CASES[function_name]())
    assert_matches_saved_result(
        actual,
        saved_results[function_name],
        absolute_tolerance=CASE_ABSOLUTE_TOLERANCE.get(function_name, FLOAT_ABSOLUTE_TOLERANCE),
    )
