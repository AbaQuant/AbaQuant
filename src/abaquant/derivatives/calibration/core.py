"""Object-oriented calibration tools for listed and synthetic option smiles.

Purpose
-------
The module provides a small, deterministic calibration layer that connects
market option-chain observations to advanced option-pricing models. It exposes
result objects with fitted parameters, model-versus-market tables, residual
statistics, and visualization/export hooks.

Conventions
-----------
Rates and dividend yields are decimal annual quantities. Maturities are in
years. Option premiums and strikes use the same currency units as the underlying
spot price. Implied volatilities are annualized decimal volatilities.

Scope and limitations
---------------------
Calibrations are numerical least-squares fits. Results depend on input quality,
liquidity filters, initial parameters, and bounds. They are diagnostics, not
trading recommendations.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import pandas as pd
from scipy.optimize import minimize, minimize_scalar

from abaquant.core import DataProvenance
from abaquant.derivatives.models.black_scholes import BlackScholesMertonModel
from abaquant.derivatives.models.heston import HestonStochasticVolatilityModel
from abaquant.derivatives.models.sabr import SABRVolatilityModel
from abaquant.derivatives.numerics.implied_volatility import implied_volatility_black_scholes

CalibrationObjective = Literal["price", "iv"]
CalibrationWeighting = Literal["equal", "vega", "open_interest"]
OptionType = Literal["call", "put"]


class CalibrationError(ValueError):
    """Raised when option-model calibration inputs are incomplete or invalid."""


@dataclass(frozen=True)
class CalibrationResult:
    """Fitted option-model calibration result.

    Parameters
    ----------
    model_name : str
        Human-readable model identifier, such as ``"bsm"`` or ``"heston"``.
    parameters : Mapping[str, float]
        Calibrated model parameters.
    error : float
        Root-mean-square calibration error in the selected objective units.
    success : bool
        Whether the numerical optimizer reported success.
    message : str
        Solver or workflow message.
    market_data : pandas.DataFrame
        Cleaned market observations used in the fit.
    model_data : pandas.DataFrame
        Contract-level model values, market values, and residuals.
    objective : str
        Objective used during fitting: ``"price"`` or ``"iv"``.
    option_type : str
        Option family used by the fit.
    metadata : Mapping[str, object]
        Additional reproducibility metadata such as bounds, maturity, and rate.
    """

    model_name: str
    parameters: Mapping[str, float]
    error: float
    success: bool
    message: str
    market_data: pd.DataFrame
    model_data: pd.DataFrame
    objective: str
    option_type: str
    metadata: Mapping[str, object] = field(default_factory=dict)
    provenance: DataProvenance | None = None

    def __post_init__(self) -> None:
        """Attach calibration provenance when not supplied explicitly."""
        if self.provenance is None:
            object.__setattr__(
                self,
                "provenance",
                DataProvenance(
                    provider="derived",
                    dataset="derivative_calibration",
                    source_labels=(self.model_name, self.option_type, self.objective),
                    transformation_steps=(
                        "market option observation cleaning",
                        "least-squares calibration",
                        "model-versus-market residual calculation",
                    ),
                    request={
                        "model_name": self.model_name,
                        "objective": self.objective,
                        "option_type": self.option_type,
                        "observations": len(self.model_data),
                        "metadata": dict(self.metadata),
                    },
                ),
            )

    def summary(self) -> dict[str, object]:
        """Return compact fit diagnostics and calibrated parameters."""
        finite_residuals = self.model_data["residual"].replace([np.inf, -np.inf], np.nan).dropna()
        mean_absolute_error = (
            float(finite_residuals.abs().mean()) if not finite_residuals.empty else float("nan")
        )
        max_absolute_error = (
            float(finite_residuals.abs().max()) if not finite_residuals.empty else float("nan")
        )
        return {
            "model_name": self.model_name,
            "objective": self.objective,
            "option_type": self.option_type,
            "success": self.success,
            "error": self.error,
            "mean_absolute_error": mean_absolute_error,
            "max_absolute_error": max_absolute_error,
            "observations": len(self.model_data),
            **{f"parameter_{name}": value for name, value in self.parameters.items()},
        }

    def error_table(self) -> pd.DataFrame:
        """Return the contract-level market-versus-model residual table."""
        return self.model_data.copy()

    def parameter_table(self) -> pd.DataFrame:
        """Return calibrated parameters as a two-column table."""
        return pd.DataFrame(
            [{"parameter": name, "value": float(value)} for name, value in self.parameters.items()]
        )

    def as_dict(self) -> dict[str, object]:
        """Return a serialization-friendly representation of the calibration result."""
        return {
            "model_name": self.model_name,
            "parameters": dict(self.parameters),
            "error": self.error,
            "success": self.success,
            "message": self.message,
            "objective": self.objective,
            "option_type": self.option_type,
            "metadata": dict(self.metadata),
            "provenance": self.provenance.as_dict(),
        }

    def visualize(
        self,
        *,
        chart: Literal["model_vs_market", "residuals", "parameters"] = "model_vs_market",
        backend: str | None = None,
        theme: object | None = None,
        save_path: str | None = None,
        filename: str | None = None,
    ):
        """Visualize model-versus-market fit quality or calibrated parameters.

        Parameters
        ----------
        chart : {"model_vs_market", "residuals", "parameters"}, default="model_vs_market"
            Calibration diagnostic to render.
        backend, theme, save_path, filename
            Standard AbaQuant visualization overrides.

        Returns
        -------
        matplotlib.figure.Figure or plotly.graph_objects.Figure
            Backend-native figure object.
        """
        from abaquant.visualization import visualize_calibration_result

        return visualize_calibration_result(
            self,
            chart=chart,
            backend=backend,
            theme=theme,
            save_path=save_path,
            filename=filename,
        )

    def report(self):
        """Return an exportable report describing the calibration fit."""
        from abaquant.reports import ExportableReport, ReportSection, ReportTable

        summary = self.summary()
        return ExportableReport(
            title=f"{self.model_name.upper()} Calibration Report",
            metadata={"report_type": "derivative_calibration", "model_name": self.model_name},
            provenance=self.provenance.with_step("calibration report generation"),
            sections=(
                ReportSection(
                    title="Summary",
                    body=(
                        f"Calibration objective: {self.objective}. "
                        f"Fit used {summary['observations']} {self.option_type} observations."
                    ),
                    tables=(ReportTable("Fit summary", pd.DataFrame([summary])),),
                ),
                ReportSection(
                    title="Parameters",
                    tables=(ReportTable("Calibrated parameters", self.parameter_table()),),
                ),
                ReportSection(
                    title="Model versus market",
                    tables=(ReportTable("Residual table", self.error_table()),),
                ),
            ),
        )


@dataclass(frozen=True)
class BSMFlatVolCalibration:
    """Calibrate a single flat Black--Scholes--Merton volatility.

    Parameters
    ----------
    option_chain : object
        DataFrame-like option observations, or an object exposing
        ``iv_smile(...)``. Required fields are ``strike`` and either
        ``market_price`` or ``implied_volatility`` depending on the objective.
    spot_price : float | None, default=None
        Current underlying price. Required for price-objective fits unless the
        chain has a ``spot_price`` column.
    maturity_years : float | None, default=None
        Time to expiry. Required for price-objective fits unless the chain has a
        ``maturity_years`` column or ``days_to_expiry`` column.
    risk_free_rate : float, default=0.0
        Continuously compounded annual risk-free rate.
    dividend_yield : float, default=0.0
        Continuous annual dividend yield.
    option_type : {"call", "put"}, default="call"
        Option family used during calibration.
    objective : {"price", "iv"}, default="price"
        Fit to market premiums or listed implied volatilities.
    """

    option_chain: object
    spot_price: float | None = None
    maturity_years: float | None = None
    risk_free_rate: float = 0.0
    dividend_yield: float = 0.0
    option_type: OptionType = "call"
    objective: CalibrationObjective = "price"
    initial_volatility: float = 0.2
    bounds: tuple[float, float] = (1e-4, 5.0)
    weighting: CalibrationWeighting = "equal"
    min_open_interest: float | None = None

    def fit(self) -> CalibrationResult:
        """Fit the flat-volatility model and return a calibration result."""
        table = _prepare_market_table(
            self.option_chain,
            option_type=self.option_type,
            spot_price=self.spot_price,
            maturity_years=self.maturity_years,
            min_open_interest=self.min_open_interest,
        )
        if self.objective == "iv":
            fit_table = _require_columns(table, ["implied_volatility"])
            weights = _calibration_weights(fit_table, self.weighting)
            volatility = _weighted_average(
                fit_table["implied_volatility"].to_numpy(dtype=float), weights
            )
            model_table = _bsm_model_table(
                fit_table,
                volatility=volatility,
                risk_free_rate=self.risk_free_rate,
                dividend_yield=self.dividend_yield,
                objective="iv",
            )
            error = _weighted_rmse(model_table["residual"].to_numpy(dtype=float), weights)
            return CalibrationResult(
                model_name="bsm_flat_vol",
                parameters={"volatility": float(volatility)},
                error=error,
                success=True,
                message="Closed-form weighted flat implied-volatility fit.",
                market_data=fit_table,
                model_data=model_table,
                objective=self.objective,
                option_type=self.option_type,
                metadata=_metadata(self, observations=len(fit_table)),
            )
        if self.objective != "price":
            raise CalibrationError("objective must be 'price' or 'iv'.")
        fit_table = _require_columns(table, ["market_price"])
        weights = _calibration_weights(fit_table, self.weighting)

        def objective(volatility: float) -> float:
            """Return weighted sum of squared BSM premium residuals."""
            model_table = _bsm_model_table(
                fit_table,
                volatility=float(volatility),
                risk_free_rate=self.risk_free_rate,
                dividend_yield=self.dividend_yield,
                objective="price",
            )
            residuals = model_table["residual"].to_numpy(dtype=float)
            return float(np.nansum(weights * residuals**2))

        result = minimize_scalar(
            objective, bounds=self.bounds, method="bounded", options={"xatol": 1e-10}
        )
        volatility = float(result.x)
        model_table = _bsm_model_table(
            fit_table,
            volatility=volatility,
            risk_free_rate=self.risk_free_rate,
            dividend_yield=self.dividend_yield,
            objective="price",
        )
        error = _weighted_rmse(model_table["residual"].to_numpy(dtype=float), weights)
        return CalibrationResult(
            model_name="bsm_flat_vol",
            parameters={"volatility": volatility},
            error=error,
            success=bool(result.success),
            message=str(result.message),
            market_data=fit_table,
            model_data=model_table,
            objective=self.objective,
            option_type=self.option_type,
            metadata=_metadata(self, observations=len(fit_table)),
        )


@dataclass(frozen=True)
class SABRSmileCalibration:
    """Calibrate SABR alpha, rho, and nu against a listed volatility smile.

    Parameters
    ----------
    option_chain : object
        DataFrame-like option observations, or an object exposing
        ``iv_smile(...)``. The fit requires ``strike`` and
        ``implied_volatility`` observations.
    forward_price : float | None, default=None
        Forward price at the option maturity. If omitted, the value is inferred
        from ``spot_price`` and carry inputs when possible.
    maturity_years : float | None, default=None
        Time to expiry in years.
    beta : float, default=1.0
        Fixed SABR elasticity parameter.
    """

    option_chain: object
    forward_price: float | None = None
    spot_price: float | None = None
    maturity_years: float | None = None
    risk_free_rate: float = 0.0
    dividend_yield: float = 0.0
    beta: float = 1.0
    option_type: OptionType = "call"
    initial_parameters: Mapping[str, float] | None = None
    bounds: Mapping[str, tuple[float, float]] | None = None
    weighting: CalibrationWeighting = "equal"
    min_open_interest: float | None = None
    max_iter: int = 500
    tol: float = 1e-8

    def fit(self) -> CalibrationResult:
        """Fit SABR smile parameters and return the calibration diagnostics."""
        table = _prepare_market_table(
            self.option_chain,
            option_type=self.option_type,
            spot_price=self.spot_price,
            maturity_years=self.maturity_years,
            min_open_interest=self.min_open_interest,
        )
        table = _require_columns(table, ["implied_volatility"])
        maturity = _single_column_or_value(
            table, "maturity_years", self.maturity_years, "maturity_years"
        )
        forward = _resolve_forward_price(
            table,
            forward_price=self.forward_price,
            spot_price=self.spot_price,
            maturity_years=maturity,
            risk_free_rate=self.risk_free_rate,
            dividend_yield=self.dividend_yield,
        )
        initial = {"alpha": 0.2, "rho": -0.25, "nu": 0.5}
        if self.initial_parameters:
            initial.update({name: float(value) for name, value in self.initial_parameters.items()})
        bounds = {
            "alpha": (1e-4, 5.0),
            "rho": (-0.999, 0.999),
            "nu": (1e-4, 5.0),
        }
        if self.bounds:
            bounds.update({name: tuple(map(float, value)) for name, value in self.bounds.items()})
        weights = _calibration_weights(table, self.weighting)
        strikes = table["strike"].to_numpy(dtype=float)
        market_ivs = table["implied_volatility"].to_numpy(dtype=float)

        def objective(params: np.ndarray) -> float:
            """Return weighted sum of squared SABR volatility residuals."""
            alpha, rho, nu = params
            if alpha <= 0.0 or nu <= 0.0 or abs(rho) >= 1.0:
                return 1e12
            model_ivs = _sabr_implied_vols(
                forward,
                strikes,
                maturity,
                alpha=alpha,
                beta=float(self.beta),
                rho=rho,
                nu=nu,
            )
            residuals = model_ivs - market_ivs
            return float(np.nansum(weights * residuals**2))

        result = minimize(
            objective,
            np.array([initial["alpha"], initial["rho"], initial["nu"]], dtype=float),
            method="L-BFGS-B",
            bounds=[bounds["alpha"], bounds["rho"], bounds["nu"]],
            options={"maxiter": int(self.max_iter), "ftol": float(self.tol)},
        )
        alpha, rho, nu = map(float, result.x)
        model_table = _sabr_model_table(
            table,
            forward_price=forward,
            maturity_years=maturity,
            alpha=alpha,
            beta=float(self.beta),
            rho=rho,
            nu=nu,
        )
        error = _weighted_rmse(model_table["residual"].to_numpy(dtype=float), weights)
        return CalibrationResult(
            model_name="sabr",
            parameters={"alpha": alpha, "beta": float(self.beta), "rho": rho, "nu": nu},
            error=error,
            success=bool(result.success),
            message=str(result.message),
            market_data=table,
            model_data=model_table,
            objective="iv",
            option_type=self.option_type,
            metadata={**_metadata(self, observations=len(table)), "forward_price": forward},
        )


@dataclass(frozen=True)
class HestonCalibration:
    """Calibrate Heston parameters against option prices or implied volatilities.

    Parameters
    ----------
    option_chain : object
        DataFrame-like option observations, or an object exposing
        ``iv_smile(...)``. Heston fits require strike, maturity, and either
        market premium or implied-volatility observations depending on the
        objective.
    initial_parameters : Mapping[str, float] | None, default=None
        Initial values for ``kappa``, ``theta``, ``xi``, ``rho``, and ``v0``.
    objective : {"iv", "price"}, default="iv"
        Calibration target. ``"iv"`` is usually faster and more stable.
    """

    option_chain: object
    spot_price: float | None = None
    maturity_years: float | None = None
    risk_free_rate: float = 0.0
    dividend_yield: float = 0.0
    option_type: OptionType = "call"
    objective: CalibrationObjective = "iv"
    initial_parameters: Mapping[str, float] | None = None
    bounds: Mapping[str, tuple[float, float]] | None = None
    weighting: CalibrationWeighting = "equal"
    min_open_interest: float | None = None
    max_contracts: int | None = 25
    max_iter: int = 250
    tol: float = 1e-8

    def fit(self) -> CalibrationResult:
        """Fit Heston stochastic-volatility parameters."""
        table = _prepare_market_table(
            self.option_chain,
            option_type=self.option_type,
            spot_price=self.spot_price,
            maturity_years=self.maturity_years,
            min_open_interest=self.min_open_interest,
        )
        required = ["implied_volatility"] if self.objective == "iv" else ["market_price"]
        table = _require_columns(table, required)
        if self.max_contracts is not None and len(table) > self.max_contracts:
            table = _nearest_moneyness_subset(table, int(self.max_contracts))
        spot = _single_column_or_value(table, "spot_price", self.spot_price, "spot_price")
        maturity = _single_column_or_value(
            table, "maturity_years", self.maturity_years, "maturity_years"
        )
        initial = {"kappa": 2.0, "theta": 0.04, "xi": 0.35, "rho": -0.5, "v0": 0.04}
        if self.initial_parameters:
            initial.update({name: float(value) for name, value in self.initial_parameters.items()})
        bounds = {
            "kappa": (0.01, 15.0),
            "theta": (1e-4, 2.0),
            "xi": (0.01, 5.0),
            "rho": (-0.999, 0.999),
            "v0": (1e-5, 2.0),
        }
        if self.bounds:
            bounds.update({name: tuple(map(float, value)) for name, value in self.bounds.items()})
        weights = _calibration_weights(table, self.weighting)
        strikes = table["strike"].to_numpy(dtype=float)
        market_prices = table.get("market_price", pd.Series(np.nan, index=table.index)).to_numpy(
            dtype=float
        )
        market_ivs = table.get("implied_volatility", pd.Series(np.nan, index=table.index)).to_numpy(
            dtype=float
        )

        def objective(params: np.ndarray) -> float:
            """Return weighted Heston calibration loss."""
            kappa, theta, xi, rho, v0 = map(float, params)
            if not _valid_heston_parameters(kappa, theta, xi, rho, v0):
                return 1e12
            residuals: list[float] = []
            for index, strike in enumerate(strikes):
                try:
                    model = HestonStochasticVolatilityModel(
                        spot,
                        float(strike),
                        maturity,
                        self.risk_free_rate,
                        self.dividend_yield,
                        v0,
                        kappa,
                        theta,
                        xi,
                        rho,
                    )
                    model_price = model.price(self.option_type)
                    if self.objective == "iv":
                        model_value = implied_volatility_black_scholes(
                            model_price,
                            spot,
                            float(strike),
                            maturity,
                            self.risk_free_rate,
                            self.dividend_yield,
                            self.option_type,
                        )
                        market_value = market_ivs[index]
                    else:
                        model_value = model_price
                        market_value = market_prices[index]
                    residuals.append(float(model_value - market_value))
                except Exception:
                    residuals.append(1e6)
            residual_array = np.asarray(residuals, dtype=float)
            return float(np.nansum(weights * residual_array**2))

        result = minimize(
            objective,
            np.array(
                [initial["kappa"], initial["theta"], initial["xi"], initial["rho"], initial["v0"]],
                dtype=float,
            ),
            method="L-BFGS-B",
            bounds=[bounds["kappa"], bounds["theta"], bounds["xi"], bounds["rho"], bounds["v0"]],
            options={"maxiter": int(self.max_iter), "ftol": float(self.tol)},
        )
        kappa, theta, xi, rho, v0 = map(float, result.x)
        model_table = _heston_model_table(
            table,
            spot_price=spot,
            maturity_years=maturity,
            risk_free_rate=self.risk_free_rate,
            dividend_yield=self.dividend_yield,
            option_type=self.option_type,
            objective=self.objective,
            kappa=kappa,
            theta=theta,
            xi=xi,
            rho=rho,
            v0=v0,
        )
        error = _weighted_rmse(model_table["residual"].to_numpy(dtype=float), weights)
        return CalibrationResult(
            model_name="heston",
            parameters={"kappa": kappa, "theta": theta, "xi": xi, "rho": rho, "v0": v0},
            error=error,
            success=bool(result.success),
            message=str(result.message),
            market_data=table,
            model_data=model_table,
            objective=self.objective,
            option_type=self.option_type,
            metadata=_metadata(self, observations=len(table)),
        )


def _prepare_market_table(
    option_chain: object,
    *,
    option_type: OptionType,
    spot_price: float | None,
    maturity_years: float | None,
    min_open_interest: float | None,
) -> pd.DataFrame:
    """Return a cleaned option-calibration table from multiple accepted inputs."""
    if option_type not in {"call", "put"}:
        raise CalibrationError("option_type must be 'call' or 'put'.")
    if hasattr(option_chain, "iv_smile") and callable(option_chain.iv_smile):
        table = option_chain.iv_smile(
            option_type=option_type, spot_price=spot_price, min_open_interest=min_open_interest
        )
    elif isinstance(option_chain, pd.DataFrame):
        table = option_chain.copy()
    else:
        raise CalibrationError(
            "option_chain must be a pandas DataFrame or an OptionChainAnalytics-like object."
        )
    table = _normalize_columns(table)
    if "option_type" in table.columns:
        table = table[table["option_type"].astype(str).str.lower() == option_type].copy()
    else:
        table["option_type"] = option_type
    if min_open_interest is not None and "open_interest" in table.columns:
        table = table[
            pd.to_numeric(table["open_interest"], errors="coerce") >= float(min_open_interest)
        ].copy()
    if "market_price" not in table.columns:
        table["market_price"] = _market_price_from_columns(table)
    if spot_price is not None and "spot_price" not in table.columns:
        table["spot_price"] = float(spot_price)
    if maturity_years is not None and "maturity_years" not in table.columns:
        table["maturity_years"] = float(maturity_years)
    if "maturity_years" not in table.columns and "days_to_expiry" in table.columns:
        table["maturity_years"] = pd.to_numeric(table["days_to_expiry"], errors="coerce") / 365.25
    for column in (
        "strike",
        "market_price",
        "implied_volatility",
        "spot_price",
        "maturity_years",
        "open_interest",
    ):
        if column in table.columns:
            table[column] = pd.to_numeric(table[column], errors="coerce")
    table = table[np.isfinite(table["strike"]) & (table["strike"] > 0.0)].copy()
    if "spot_price" in table.columns:
        table["moneyness"] = table["spot_price"] / table["strike"]
    if "moneyness" not in table.columns:
        table["moneyness"] = np.nan
    table = table.reset_index(drop=True)
    if table.empty:
        raise CalibrationError("No valid option observations remain after cleaning.")
    return table


def _normalize_columns(table: pd.DataFrame) -> pd.DataFrame:
    """Normalize common listed-option column labels."""
    rename_map = {
        "lastprice": "last_price",
        "lastPrice": "last_price",
        "midpoint": "mid_price",
        "mid": "mid_price",
        "impliedvolatility": "implied_volatility",
        "impliedVolatility": "implied_volatility",
        "openinterest": "open_interest",
        "openInterest": "open_interest",
        "optionType": "option_type",
        "type": "option_type",
    }
    return table.rename(
        columns={column: rename_map.get(str(column), str(column)) for column in table.columns}
    )


def _market_price_from_columns(table: pd.DataFrame) -> pd.Series:
    """Infer a usable market premium from midpoint, bid/ask, or last price."""
    if "mid_price" in table.columns:
        market = pd.to_numeric(table["mid_price"], errors="coerce")
    else:
        market = pd.Series(np.nan, index=table.index, dtype=float)
    if "bid" in table.columns and "ask" in table.columns:
        bid = pd.to_numeric(table["bid"], errors="coerce")
        ask = pd.to_numeric(table["ask"], errors="coerce")
        midpoint = ((bid + ask) / 2.0).where((bid > 0.0) & (ask >= bid))
        market = market.where(np.isfinite(market) & (market > 0.0), midpoint)
    if "last_price" in table.columns:
        last_price = pd.to_numeric(table["last_price"], errors="coerce")
        market = market.where(np.isfinite(market) & (market > 0.0), last_price)
    return market


def _require_columns(table: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    """Return rows with finite required fields or raise a calibration error."""
    result = table.copy()
    missing = [column for column in columns if column not in result.columns]
    if missing:
        raise CalibrationError(f"Calibration data are missing required columns: {missing}")
    for column in columns:
        result = result[np.isfinite(result[column]) & (result[column] > 0.0)].copy()
    if result.empty:
        raise CalibrationError(f"No finite positive observations are available for {columns}.")
    return result.reset_index(drop=True)


def _calibration_weights(table: pd.DataFrame, weighting: CalibrationWeighting) -> np.ndarray:
    """Return normalized non-negative calibration weights."""
    if weighting == "equal":
        weights = np.ones(len(table), dtype=float)
    elif weighting == "open_interest":
        if "open_interest" not in table.columns:
            raise CalibrationError("open_interest weighting requires an open_interest column.")
        weights = (
            pd.to_numeric(table["open_interest"], errors="coerce").fillna(0.0).to_numpy(dtype=float)
        )
        weights = np.where(weights > 0.0, weights, 0.0)
        if float(weights.sum()) <= 0.0:
            weights = np.ones(len(table), dtype=float)
    elif weighting == "vega":
        if "vega" in table.columns:
            weights = (
                pd.to_numeric(table["vega"], errors="coerce").fillna(0.0).to_numpy(dtype=float)
            )
        else:
            weights = np.ones(len(table), dtype=float)
    else:
        raise CalibrationError("weighting must be 'equal', 'vega', or 'open_interest'.")
    total = float(np.sum(weights))
    return weights / total * len(weights) if total > 0.0 else np.ones(len(table), dtype=float)


def _weighted_average(values: np.ndarray, weights: np.ndarray) -> float:
    """Return a finite weighted average of numeric observations."""
    mask = np.isfinite(values) & np.isfinite(weights) & (weights >= 0.0)
    if not mask.any():
        raise CalibrationError("No finite values are available for weighted averaging.")
    return float(np.average(values[mask], weights=weights[mask]))


def _weighted_rmse(residuals: np.ndarray, weights: np.ndarray) -> float:
    """Return a finite weighted root-mean-square error."""
    mask = np.isfinite(residuals) & np.isfinite(weights)
    if not mask.any():
        return float("nan")
    return float(np.sqrt(np.average(residuals[mask] ** 2, weights=weights[mask])))


def _single_column_or_value(
    table: pd.DataFrame, column: str, value: float | None, name: str
) -> float:
    """Resolve one scalar value from an explicit argument or table column."""
    if value is not None:
        resolved = float(value)
    elif column in table.columns:
        finite = table[column].replace([np.inf, -np.inf], np.nan).dropna()
        if finite.empty:
            raise CalibrationError(
                f"{name} is required and could not be inferred from the option chain."
            )
        resolved = float(finite.iloc[0])
    else:
        raise CalibrationError(
            f"{name} is required and could not be inferred from the option chain."
        )
    if not np.isfinite(resolved) or resolved <= 0.0:
        raise CalibrationError(f"{name} must be a positive finite number.")
    return resolved


def _resolve_forward_price(
    table: pd.DataFrame,
    *,
    forward_price: float | None,
    spot_price: float | None,
    maturity_years: float,
    risk_free_rate: float,
    dividend_yield: float,
) -> float:
    """Resolve a forward price from explicit, table, or spot/carry inputs."""
    if forward_price is not None:
        return _positive_float(forward_price, "forward_price")
    if "forward_price" in table.columns:
        finite = table["forward_price"].replace([np.inf, -np.inf], np.nan).dropna()
        if not finite.empty:
            return _positive_float(float(finite.iloc[0]), "forward_price")
    spot = _single_column_or_value(table, "spot_price", spot_price, "spot_price")
    return float(spot * np.exp((float(risk_free_rate) - float(dividend_yield)) * maturity_years))


def _positive_float(value: object, name: str) -> float:
    """Return a positive finite scalar float."""
    resolved = float(value)
    if not np.isfinite(resolved) or resolved <= 0.0:
        raise CalibrationError(f"{name} must be a positive finite number.")
    return resolved


def _nearest_moneyness_subset(table: pd.DataFrame, max_contracts: int) -> pd.DataFrame:
    """Keep a deterministic near-the-money subset for expensive calibrations."""
    if max_contracts <= 0 or len(table) <= max_contracts:
        return table.reset_index(drop=True)
    if "moneyness" in table.columns and table["moneyness"].notna().any():
        ordered = table.assign(_distance=(table["moneyness"] - 1.0).abs()).sort_values(
            ["_distance", "strike"]
        )
    else:
        ordered = table.sort_values("strike")
    return (
        ordered.head(max_contracts)
        .drop(columns=["_distance"], errors="ignore")
        .sort_values("strike")
        .reset_index(drop=True)
    )


def _bsm_model_table(
    table: pd.DataFrame,
    *,
    volatility: float,
    risk_free_rate: float,
    dividend_yield: float,
    objective: CalibrationObjective,
) -> pd.DataFrame:
    """Return BSM market-versus-model values for each contract."""
    rows: list[dict[str, float | str]] = []
    for row in table.itertuples(index=False):
        strike = float(row.strike)
        spot = float(row.spot_price)
        maturity = float(row.maturity_years)
        option_type = str(row.option_type)
        model = BlackScholesMertonModel(
            spot, strike, maturity, risk_free_rate, volatility, dividend_yield
        )
        model_price = model.price(option_type)
        market_price = float(getattr(row, "market_price", np.nan))
        market_iv = float(getattr(row, "implied_volatility", np.nan))
        model_value = volatility if objective == "iv" else model_price
        market_value = market_iv if objective == "iv" else market_price
        rows.append(
            {
                "strike": strike,
                "moneyness": float(getattr(row, "moneyness", np.nan)),
                "option_type": option_type,
                "market_price": market_price,
                "market_implied_volatility": market_iv,
                "model_price": float(model_price),
                "model_implied_volatility": float(volatility),
                "market_value": float(market_value),
                "model_value": float(model_value),
                "residual": float(model_value - market_value),
            }
        )
    return pd.DataFrame(rows)


def _sabr_implied_vols(
    forward_price: float,
    strikes: np.ndarray,
    maturity_years: float,
    *,
    alpha: float,
    beta: float,
    rho: float,
    nu: float,
) -> np.ndarray:
    """Return SABR implied volatilities for a strike vector."""
    return np.asarray(
        [
            SABRVolatilityModel(
                forward_price,
                float(strike),
                maturity_years,
                alpha,
                beta,
                rho,
                nu,
            ).implied_vol()
            for strike in strikes
        ],
        dtype=float,
    )


def _sabr_model_table(
    table: pd.DataFrame,
    *,
    forward_price: float,
    maturity_years: float,
    alpha: float,
    beta: float,
    rho: float,
    nu: float,
) -> pd.DataFrame:
    """Return SABR market-versus-model implied-volatility diagnostics."""
    strikes = table["strike"].to_numpy(dtype=float)
    model_ivs = _sabr_implied_vols(
        forward_price,
        strikes,
        maturity_years,
        alpha=alpha,
        beta=beta,
        rho=rho,
        nu=nu,
    )
    market_ivs = table["implied_volatility"].to_numpy(dtype=float)
    return pd.DataFrame(
        {
            "strike": strikes,
            "moneyness": table.get("moneyness", pd.Series(np.nan, index=table.index)).to_numpy(
                dtype=float
            ),
            "option_type": table["option_type"].astype(str).to_numpy(),
            "market_implied_volatility": market_ivs,
            "model_implied_volatility": model_ivs,
            "market_value": market_ivs,
            "model_value": model_ivs,
            "residual": model_ivs - market_ivs,
        }
    )


def _valid_heston_parameters(kappa: float, theta: float, xi: float, rho: float, v0: float) -> bool:
    """Return whether Heston parameters satisfy basic numerical bounds."""
    return (
        np.isfinite(kappa)
        and np.isfinite(theta)
        and np.isfinite(xi)
        and np.isfinite(rho)
        and np.isfinite(v0)
        and kappa > 0.0
        and theta > 0.0
        and xi > 0.0
        and abs(rho) < 1.0
        and v0 > 0.0
    )


def _heston_model_table(
    table: pd.DataFrame,
    *,
    spot_price: float,
    maturity_years: float,
    risk_free_rate: float,
    dividend_yield: float,
    option_type: OptionType,
    objective: CalibrationObjective,
    kappa: float,
    theta: float,
    xi: float,
    rho: float,
    v0: float,
) -> pd.DataFrame:
    """Return Heston market-versus-model diagnostics for each contract."""
    rows: list[dict[str, float | str]] = []
    for row in table.itertuples(index=False):
        strike = float(row.strike)
        model = HestonStochasticVolatilityModel(
            spot_price,
            strike,
            maturity_years,
            risk_free_rate,
            dividend_yield,
            v0,
            kappa,
            theta,
            xi,
            rho,
        )
        model_price = model.price(option_type)
        model_iv = implied_volatility_black_scholes(
            model_price,
            spot_price,
            strike,
            maturity_years,
            risk_free_rate,
            dividend_yield,
            option_type,
        )
        market_price = float(getattr(row, "market_price", np.nan))
        market_iv = float(getattr(row, "implied_volatility", np.nan))
        model_value = model_iv if objective == "iv" else model_price
        market_value = market_iv if objective == "iv" else market_price
        rows.append(
            {
                "strike": strike,
                "moneyness": float(getattr(row, "moneyness", np.nan)),
                "option_type": option_type,
                "market_price": market_price,
                "market_implied_volatility": market_iv,
                "model_price": float(model_price),
                "model_implied_volatility": float(model_iv),
                "market_value": float(market_value),
                "model_value": float(model_value),
                "residual": float(model_value - market_value),
            }
        )
    return pd.DataFrame(rows)


def _metadata(calibration: object, *, observations: int) -> dict[str, object]:
    """Return common metadata from a calibration object."""
    return {
        "observations": observations,
        "spot_price": getattr(calibration, "spot_price", None),
        "maturity_years": getattr(calibration, "maturity_years", None),
        "risk_free_rate": getattr(calibration, "risk_free_rate", None),
        "dividend_yield": getattr(calibration, "dividend_yield", None),
        "weighting": getattr(calibration, "weighting", None),
    }
