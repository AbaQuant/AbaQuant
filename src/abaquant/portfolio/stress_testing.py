"""Historical fixed-weight portfolio stress testing.

Purpose
-------
The module applies a supplied allocation to predefined historical windows and reports performance conditional on available price coverage.

Conventions
-----------
Price panels use dates on the index and asset labels on columns. Assets without enough coverage can be excluded and surviving weights are renormalized under the documented rule.

Scope and limitations
---------------------
Historical scenarios are descriptive rather than probabilistic forecasts.

References
----------
[ 1 ] Markowitz, H. (1952), "Portfolio Selection".
"""

from __future__ import annotations

import pandas as pd

from .risk_metrics import (
    annualized_volatility,
    cvar_historical,
    max_drawdown,
)

# Historical scenarios: start date, end date, and description.
SCENARIOS: dict[str, dict] = {
    "2008 Financial Crisis": {
        "start": "2007-10-09",
        "end": "2009-03-09",
        "description": "Lehman Brothers collapse and subprime mortgage crisis. "
        "The S&P 500 declined by roughly 56% from peak to trough.",
    },
    "COVID-19 (2020)": {
        "start": "2020-02-19",
        "end": "2020-04-30",
        "description": "Abrupt market selloff during the global pandemic, followed by a "
        "recovery supported by monetary stimulus.",
    },
    "Dot-com Bubble (2000-2002)": {
        "start": "2000-03-10",
        "end": "2002-10-09",
        "description": "Collapse of the late-1990s technology bubble. "
        "The Nasdaq lost more than 78% during this period.",
    },
    "2022 Fed Rate Hikes": {
        "start": "2022-01-01",
        "end": "2022-12-31",
        "description": "Aggressive Federal Reserve interest-rate hiking cycle to fight "
        "inflation, affecting both equities and bonds.",
    },
}


def run_stress_test(
    prices_full: pd.DataFrame,
    weights: pd.Series,
    scenario_name: str,
    min_coverage: float = 0.6,
) -> dict | None:
    """Evaluate a fixed-weight portfolio through one predefined historical scenario.

    Parameters
    ----------
    prices_full : pd.DataFrame
        Broad historical price panel used to assess scenario coverage and performance.
    weights : pd.Series
        Portfolio weights, either a mapping keyed by asset or an ordered numeric vector as documented by the callable.
    scenario_name : str
        Key identifying one predefined historical stress scenario.
    min_coverage : float, default=0.6
        Minimum fraction of scenario dates with usable prices required for an asset.

    Returns
    -------
    dict[str, object]
        Dictionary of named model outputs, metrics, or workflow results defined by the current public schema.
    """
    scenario = SCENARIOS[scenario_name]
    start, end = scenario["start"], scenario["end"]

    window = prices_full.loc[start:end]
    if window.empty:
        return None

    coverage = window.notna().mean()
    valid_cols = coverage[coverage >= min_coverage].index.tolist()
    excluded = [c for c in prices_full.columns if c not in valid_cols]

    if not valid_cols:
        return None

    window = window[valid_cols].dropna()
    if len(window) < 5:
        return None

    scenario_returns = window.pct_change().dropna()
    if scenario_returns.empty:
        return None

    valid_weights = weights.reindex(valid_cols).fillna(0.0)
    w_sum = valid_weights.sum()
    if w_sum == 0:
        valid_weights = pd.Series(1.0 / len(valid_cols), index=valid_cols)
    else:
        valid_weights = valid_weights / w_sum

    port_returns = scenario_returns @ valid_weights.values
    port_returns.name = "Portfolio"

    bench_weights = pd.Series(1.0 / len(valid_cols), index=valid_cols)
    bench_returns = scenario_returns @ bench_weights.values
    bench_returns.name = "Equal Weight"

    cum_port = (1 + port_returns).cumprod()
    cum_bench = (1 + bench_returns).cumprod()

    return {
        "scenario": scenario_name,
        "description": scenario["description"],
        "period_start": window.index[0],
        "period_end": window.index[-1],
        "returns": port_returns,
        "cumulative_returns": cum_port,
        "total_return": cum_port.iloc[-1] - 1,
        "max_drawdown": max_drawdown(port_returns),
        "volatility": annualized_volatility(port_returns),
        "cvar_95": cvar_historical(port_returns, 0.05),
        "benchmark_returns": bench_returns,
        "benchmark_cumulative": cum_bench,
        "benchmark_total_return": cum_bench.iloc[-1] - 1,
        "benchmark_max_drawdown": max_drawdown(bench_returns),
        "valid_assets": valid_cols,
        "excluded_assets": excluded,
        "weights_used": valid_weights,
    }


def run_all_scenarios(prices_full: pd.DataFrame, weights: pd.Series) -> dict:
    """Evaluate a fixed-weight portfolio through every predefined historical scenario.

    Parameters
    ----------
    prices_full : pd.DataFrame
        Broad historical price panel used to assess scenario coverage and performance.
    weights : pd.Series
        Portfolio weights, either a mapping keyed by asset or an ordered numeric vector as documented by the callable.

    Returns
    -------
    dict[str, object]
        Dictionary of named model outputs, metrics, or workflow results defined by the current public schema.
    """
    results = {}
    for name in SCENARIOS:
        results[name] = run_stress_test(prices_full, weights, name)
    return results
