"""Corporate-finance valuation, CAPM, and discounted-cash-flow helpers.

Purpose
-------
The module implements elementary CAPM, WACC, DCF, sensitivity, and return-regression calculations.

Conventions
-----------
Rates and growth assumptions are decimal annual rates. Free cash flow, debt, and enterprise values use currency units. Beta and alpha follow the implemented return-regression convention.

Scope and limitations
---------------------
DCF outputs depend directly on deterministic growth and discount-rate assumptions and are not forecasts.

References
----------
[ 1 ] Markowitz, H. (1952), "Portfolio Selection".
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def capm_cost_of_equity(risk_free_rate: float, beta: float, market_return: float) -> float:
    """Compute the CAPM required return on equity.

    Parameters
    ----------
    risk_free_rate : float
        Annual risk-free rate in decimal units.
    beta : float
        Model-specific beta parameter; consult the module convention.
    market_return : float
        Expected market return in decimal annual units.

    Returns
    -------
    float
        Computed capm cost of equity as a scalar in the units implied by the input values.
    """
    return float(risk_free_rate + beta * (market_return - risk_free_rate))


def weighted_average_cost_of_capital(
    cost_of_equity: float,
    equity_weight: float,
    cost_of_debt: float,
    tax_rate: float,
) -> float:
    """Compute after-tax weighted average cost of capital.

    Parameters
    ----------
    cost_of_equity : float
        Cost of equity in decimal annual units.
    equity_weight : float
        Capital-structure equity weight, expressed as a fraction.
    cost_of_debt : float
        Pre-tax cost of debt in decimal annual units.
    tax_rate : float
        Corporate tax rate as a decimal fraction.

    Returns
    -------
    float
        Computed weighted average cost of capital as a scalar in the units implied by the input values.
    """
    debt_weight = 1.0 - equity_weight
    return float(cost_of_equity * equity_weight + cost_of_debt * (1.0 - tax_rate) * debt_weight)


def dcf_valuation(
    fcf_base: float,
    projection_growth: float,
    terminal_growth: float,
    discount_rate: float,
    projection_years: int,
    net_debt: float,
    shares_outstanding: float,
) -> dict[str, float | list[float] | pd.DataFrame]:
    """Estimate enterprise and equity value from a deterministic discounted-cash-flow model.

    Parameters
    ----------
    fcf_base : float
        Base-period free cash flow in currency units.
    projection_growth : float
        Forecast free-cash-flow growth rate in decimal annual units.
    terminal_growth : float
        Perpetual terminal-growth rate in decimal annual units.
    discount_rate : float
        Annual discount rate in decimal units.
    projection_years : int
        Number of explicit free-cash-flow forecast years.
    net_debt : float
        Net debt deducted from enterprise value, in currency units.
    shares_outstanding : float
        Number of shares outstanding used to convert equity value to value per share.

    Returns
    -------
    dict[str, float | list[float] | pd.DataFrame]
        Named outputs of the dcf valuation calculation.
    """
    if discount_rate <= terminal_growth:
        raise ValueError("discount_rate must be greater than terminal_growth.")

    years = list(range(1, int(projection_years) + 1))
    fcfs = [float(fcf_base * (1 + projection_growth) ** t) for t in years]
    pv_fcfs = [float(f / (1 + discount_rate) ** t) for t, f in zip(years, fcfs, strict=True)]
    terminal_fcf = float(fcfs[-1] * (1 + terminal_growth))
    terminal_value = float(terminal_fcf / (discount_rate - terminal_growth))
    pv_terminal_value = float(terminal_value / (1 + discount_rate) ** int(projection_years))
    pv_fcf_total = float(sum(pv_fcfs))
    enterprise_value = float(pv_fcf_total + pv_terminal_value)
    equity_value = float(enterprise_value - net_debt)
    price_per_share = float(equity_value / shares_outstanding) if shares_outstanding > 0 else 0.0

    table = pd.DataFrame(
        {
            "Year": years,
            "Projected FCF": fcfs,
            "Discount Factor": [float(1 / (1 + discount_rate) ** t) for t in years],
            "Present Value": pv_fcfs,
        }
    )

    return {
        "fcfs": fcfs,
        "pv_fcfs": pv_fcfs,
        "terminal_fcf": terminal_fcf,
        "terminal_value": terminal_value,
        "pv_terminal_value": pv_terminal_value,
        "pv_fcf_total": pv_fcf_total,
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "price_per_share": price_per_share,
        "projection_table": table,
    }


def dcf_sensitivity_matrix(
    fcfs: list[float] | np.ndarray,
    terminal_growth_values: list[float] | np.ndarray,
    discount_rate_values: list[float] | np.ndarray,
    net_debt: float,
    shares_outstanding: float,
) -> np.ndarray:
    """Evaluate DCF output across terminal-growth and discount-rate scenarios.

    Parameters
    ----------
    fcfs : list[float] | np.ndarray
        Free-cash-flow sequence in currency units for DCF sensitivity analysis.
    terminal_growth_values : list[float] | np.ndarray
        Terminal-growth-rate grid in decimal annual units for DCF sensitivity analysis.
    discount_rate_values : list[float] | np.ndarray
        Discount-rate grid in decimal annual units for DCF sensitivity analysis.
    net_debt : float
        Net debt deducted from enterprise value, in currency units.
    shares_outstanding : float
        Number of shares outstanding used to convert equity value to value per share.

    Returns
    -------
    pandas.DataFrame
        Tabular result with the index, column schema, units, and missing-value treatment defined by the module convention.
    """
    cashflows = np.asarray(fcfs, dtype=float)
    g_vals = np.asarray(terminal_growth_values, dtype=float)
    wacc_vals = np.asarray(discount_rate_values, dtype=float)
    out = np.zeros((len(g_vals), len(wacc_vals)))
    projection_years = len(cashflows)

    for i, growth in enumerate(g_vals):
        for j, discount_rate in enumerate(wacc_vals):
            if discount_rate <= growth or discount_rate <= 0:
                out[i, j] = np.nan
                continue
            terminal_fcf = cashflows[-1] * (1 + growth)
            terminal_value = terminal_fcf / (discount_rate - growth)
            pv_terminal_value = terminal_value / (1 + discount_rate) ** projection_years
            pv_fcfs = sum(
                cashflows[t - 1] / (1 + discount_rate) ** t for t in range(1, projection_years + 1)
            )
            equity_value = (pv_fcfs + pv_terminal_value) - net_debt
            out[i, j] = equity_value / shares_outstanding if shares_outstanding > 0 else 0.0
    return out


def beta_alpha_from_returns(
    asset_returns: pd.Series,
    market_returns: pd.Series,
    risk_free_rate: float,
    trading_days: int = 252,
) -> dict[str, float | pd.DataFrame]:
    """Estimate beta and alpha from paired asset and market return series.

    Parameters
    ----------
    asset_returns : pd.Series
        Periodic return series for the asset.
    market_returns : pd.Series
        Periodic return series for the market benchmark.
    risk_free_rate : float
        Annual risk-free rate in decimal units.
    trading_days : int, default=252
        Observations per year used to annualize regression statistics.

    Returns
    -------
    dict[str, float | pd.DataFrame]
        Named outputs of the beta alpha from returns calculation.
    """
    df = pd.concat(
        [asset_returns.rename("Asset"), market_returns.rename("Market")], axis=1, join="inner"
    ).dropna()
    rf_daily = (1 + risk_free_rate) ** (1 / trading_days) - 1
    df["Asset Excess Return"] = df["Asset"] - rf_daily
    df["Market Excess Return"] = df["Market"] - rf_daily
    x = np.column_stack([np.ones(len(df)), df["Market Excess Return"].values])
    alpha_daily, beta = np.linalg.lstsq(x, df["Asset Excess Return"].values, rcond=None)[0]
    alpha_annual = float(alpha_daily * trading_days)
    ret_asset = float((1 + df["Asset"].mean()) ** trading_days - 1)
    ret_market = float((1 + df["Market"].mean()) ** trading_days - 1)
    vol_asset = float(df["Asset"].std() * np.sqrt(trading_days))
    vol_market = float(df["Market"].std() * np.sqrt(trading_days))
    cost_of_equity = capm_cost_of_equity(risk_free_rate, float(beta), ret_market)

    return {
        "alpha": alpha_annual,
        "beta": float(beta),
        "ret_a": ret_asset,
        "ret_m": ret_market,
        "vol_a": vol_asset,
        "vol_m": vol_market,
        "ke": cost_of_equity,
        "rf": float(risk_free_rate),
        "returns": df,
    }


__all__ = [
    "beta_alpha_from_returns",
    "capm_cost_of_equity",
    "dcf_sensitivity_matrix",
    "dcf_valuation",
    "weighted_average_cost_of_capital",
]
