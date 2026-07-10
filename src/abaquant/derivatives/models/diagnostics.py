"""Scalar option diagnostics for AbaQuant pricing models.

Purpose
-------
The module defines a compact diagnostics report for vanilla option models and a
mixin that adds moneyness, intrinsic value, extrinsic value, break-even, and
Greek summaries to scalar pricing classes.

Conventions
-----------
Moneyness is reported as spot divided by strike. Forward moneyness uses the
model's explicit ``forward_price`` when present; otherwise it uses
``spot_price * exp((risk_free_rate - dividend_yield) * maturity_years)``. All
prices are expressed in the same units as the model's underlying and strike.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import suppress
from copy import copy
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from abaquant.core import DataProvenance


@dataclass(frozen=True)
class DerivativeDiagnosticsReport:
    """Computed scalar diagnostics for one vanilla derivative contract.

    Parameters
    ----------
    option_type : {"call", "put"}
        Vanilla option family used for the report.
    price : float
        Model value of the option in currency units.
    intrinsic_value : float
        Immediate-exercise payoff at the current underlying price.
    extrinsic_value : float
        Difference between model value and intrinsic value.
    moneyness : float
        Spot moneyness, defined as ``spot_price / strike_price``.
    forward_moneyness : float
        Forward moneyness, defined as forward price divided by strike price.
    greeks : Mapping[str, float]
        Option-specific sensitivity dictionary when the model exposes Greeks.
    break_even_price : float
        Terminal underlying price at which intrinsic payoff equals the model
        premium, ignoring financing, trading costs, and bid--ask effects.
    """

    option_type: str
    price: float
    intrinsic_value: float
    extrinsic_value: float
    moneyness: float
    forward_moneyness: float
    greeks: Mapping[str, float]
    break_even_price: float
    provenance: DataProvenance | None = None

    def __post_init__(self) -> None:
        """Attach default provenance when the diagnostics were built locally."""
        if self.provenance is None:
            object.__setattr__(
                self,
                "provenance",
                DataProvenance(
                    provider="derived",
                    dataset="derivative_diagnostics",
                    source_labels=(self.option_type,),
                    transformation_steps=(
                        "model pricing",
                        "intrinsic value decomposition",
                        "moneyness calculation",
                        "Greek selection",
                    ),
                    request={"option_type": self.option_type},
                ),
            )

    def as_dict(self) -> dict[str, object]:
        """Return a plain dictionary representation of the diagnostics report.

        Returns
        -------
        dict[str, object]
            Dictionary containing all scalar diagnostics and the nested Greek
            dictionary under the ``"greeks"`` key.
        """
        return {
            "option_type": self.option_type,
            "price": self.price,
            "intrinsic_value": self.intrinsic_value,
            "extrinsic_value": self.extrinsic_value,
            "moneyness": self.moneyness,
            "forward_moneyness": self.forward_moneyness,
            "greeks": dict(self.greeks),
            "break_even_price": self.break_even_price,
            "provenance": self.provenance.as_dict(),
        }


@dataclass(frozen=True)
class DerivativeScenarioGrid:
    """Scenario-grid result for one vanilla option model.

    Parameters
    ----------
    option_type : {"call", "put"}
        Vanilla option family used for every scenario row.
    data : pandas.DataFrame
        Long-form scenario table. Required columns are ``spot_price``,
        ``volatility``, ``price``, ``intrinsic_value``, ``extrinsic_value``,
        ``moneyness``, ``forward_moneyness``, and ``break_even_price``. Greek
        columns are included when the model exposes them.
    base_spot_price : float
        Spot price on the model used to seed the scenario calculation.
    base_volatility : float
        Volatility-like attribute value on the model before perturbation.
    volatility_attribute : str
        Name of the model attribute varied across the volatility axis.

    Notes
    -----
    The grid is long-form rather than matrix-form so it can be filtered,
    grouped, exported, or pivoted without losing diagnostics columns.
    """

    option_type: str
    data: pd.DataFrame
    base_spot_price: float
    base_volatility: float
    volatility_attribute: str
    provenance: DataProvenance | None = None

    def __post_init__(self) -> None:
        """Store a defensive copy of the scenario table."""
        object.__setattr__(self, "data", self.data.copy(deep=True))
        if self.provenance is None:
            object.__setattr__(
                self,
                "provenance",
                DataProvenance(
                    provider="derived",
                    dataset="derivative_scenario_grid",
                    source_labels=(self.option_type, self.volatility_attribute),
                    transformation_steps=(
                        "spot-volatility grid repricing",
                        "intrinsic and extrinsic decomposition",
                        "scenario Greek calculation",
                    ),
                    request={
                        "option_type": self.option_type,
                        "rows": len(self.data),
                        "base_spot_price": self.base_spot_price,
                        "base_volatility": self.base_volatility,
                    },
                ),
            )

    def as_dict(self) -> dict[str, object]:
        """Return a serialization-friendly representation of the grid."""
        return {
            "option_type": self.option_type,
            "base_spot_price": self.base_spot_price,
            "base_volatility": self.base_volatility,
            "volatility_attribute": self.volatility_attribute,
            "records": self.data.to_dict("records"),
            "provenance": self.provenance.as_dict(),
        }

    def pivot(self, value: str = "price") -> pd.DataFrame:
        """Return a spot-by-volatility pivot table for one scenario metric.

        Parameters
        ----------
        value : str, default="price"
            Metric column to pivot.

        Returns
        -------
        pandas.DataFrame
            Matrix indexed by ``volatility`` and columned by ``spot_price``.
        """
        if value not in self.data.columns:
            raise ValueError(f"Unknown scenario metric: {value!r}.")
        return self.data.pivot(index="volatility", columns="spot_price", values=value)

    def visualize(
        self,
        *,
        metric: str = "price",
        chart: str = "surface",
        backend: str | None = None,
        theme=None,
        save_path: str | Path | None = None,
        filename: str | None = None,
    ):
        """Return a figure for this derivative scenario grid.

        Parameters
        ----------
        metric : str, default="price"
            Scenario metric to display. Common values are ``"price"``,
            ``"extrinsic_value"``, ``"delta"``, ``"gamma"``, ``"theta"``,
            and ``"vega"``.
        chart : {"surface", "heatmap", "curves"}, default="surface"
            Visual form for the long-form scenario grid.
        backend : {"matplotlib", "plotly"}, optional
            Backend override for this figure.
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
        from abaquant.visualization import visualize_derivative_scenario_grid

        return visualize_derivative_scenario_grid(
            self,
            metric=metric,
            chart=chart,
            backend=backend,
            theme=theme,
            save_path=save_path,
            filename=filename,
        )


def validate_option_type(option_type: str) -> str:
    """Normalize and validate a vanilla option type label.

    Parameters
    ----------
    option_type : str
        Candidate option type label.

    Returns
    -------
    str
        Normalized option type, either ``"call"`` or ``"put"``.

    Raises
    ------
    ValueError
        If ``option_type`` is not ``"call"`` or ``"put"``.
    """
    normalized = str(option_type).lower().strip()
    if normalized not in {"call", "put"}:
        raise ValueError("option_type must be 'call' or 'put'.")
    return normalized


def _scalar_float(value: object, name: str) -> float:
    """Convert a model attribute to one finite scalar float.

    Parameters
    ----------
    value : object
        Candidate scalar value.
    name : str
        Attribute name used in error messages.

    Returns
    -------
    float
        Finite scalar value.

    Raises
    ------
    ValueError
        If the value is not finite and scalar.
    """
    array = np.asarray(value)
    if array.ndim != 0 or not np.isfinite(array.item()):
        raise ValueError(f"{name} must be a finite scalar for derivative diagnostics.")
    return float(array.item())


def vanilla_intrinsic_value_from_prices(
    spot_price: float, strike_price: float, option_type: str
) -> float:
    """Return the current intrinsic value of a vanilla option.

    Parameters
    ----------
    spot_price : float
        Current underlying price.
    strike_price : float
        Option strike price.
    option_type : {"call", "put"}
        Vanilla option family.

    Returns
    -------
    float
        Current intrinsic value, ``max(S-K, 0)`` for a call and
        ``max(K-S, 0)`` for a put.
    """
    validated_option_type = validate_option_type(option_type)
    if validated_option_type == "call":
        return float(max(spot_price - strike_price, 0.0))
    return float(max(strike_price - spot_price, 0.0))


def option_price(model: object, option_type: str) -> float:
    """Return the call or put price from a scalar pricing model.

    Parameters
    ----------
    model : object
        Pricing model exposing ``call_price()`` and ``put_price()`` methods.
    option_type : {"call", "put"}
        Vanilla option family.

    Returns
    -------
    float
        Model option value in currency units.
    """
    validated_option_type = validate_option_type(option_type)
    method_name = "call_price" if validated_option_type == "call" else "put_price"
    pricing_method = getattr(model, method_name, None)
    if pricing_method is None or not callable(pricing_method):
        raise ValueError(f"{type(model).__name__} does not expose {method_name}().")
    return float(pricing_method())


def current_intrinsic_value(model: object, option_type: str) -> float:
    """Return the current intrinsic value for a scalar pricing model.

    Parameters
    ----------
    model : object
        Model exposing ``spot_price`` and ``strike_price`` attributes.
    option_type : {"call", "put"}
        Vanilla option family.

    Returns
    -------
    float
        Current intrinsic value in currency units.
    """
    spot_price = _scalar_float(getattr(model, "spot_price", None), "spot_price")
    strike_price = _scalar_float(getattr(model, "strike_price", None), "strike_price")
    return vanilla_intrinsic_value_from_prices(spot_price, strike_price, option_type)


def current_extrinsic_value(model: object, option_type: str) -> float:
    """Return the model value in excess of current intrinsic value.

    Parameters
    ----------
    model : object
        Scalar pricing model exposing price and vanilla payoff inputs.
    option_type : {"call", "put"}
        Vanilla option family.

    Returns
    -------
    float
        Extrinsic value, equal to model price minus current intrinsic value.
    """
    return float(option_price(model, option_type) - current_intrinsic_value(model, option_type))


def spot_moneyness(model: object) -> float:
    """Return spot moneyness for a scalar model.

    Parameters
    ----------
    model : object
        Model exposing ``spot_price`` and ``strike_price``.

    Returns
    -------
    float
        Ratio ``spot_price / strike_price``.
    """
    spot_price = _scalar_float(getattr(model, "spot_price", None), "spot_price")
    strike_price = _scalar_float(getattr(model, "strike_price", None), "strike_price")
    return float(spot_price / strike_price)


def forward_moneyness(model: object) -> float:
    """Return forward moneyness for a scalar model.

    Parameters
    ----------
    model : object
        Model exposing ``strike_price`` and either ``forward_price`` or the
        spot/rate/dividend/maturity inputs needed to form a forward price.

    Returns
    -------
    float
        Ratio of forward price to strike price.
    """
    strike_price = _scalar_float(getattr(model, "strike_price", None), "strike_price")
    if hasattr(model, "forward_price"):
        forward_price = _scalar_float(model.forward_price, "forward_price")
    else:
        spot_price = _scalar_float(getattr(model, "spot_price", None), "spot_price")
        maturity_years = _scalar_float(getattr(model, "maturity_years", 0.0), "maturity_years")
        risk_free_rate = _scalar_float(getattr(model, "risk_free_rate", 0.0), "risk_free_rate")
        dividend_yield = _scalar_float(getattr(model, "dividend_yield", 0.0), "dividend_yield")
        forward_price = spot_price * np.exp((risk_free_rate - dividend_yield) * maturity_years)
    return float(forward_price / strike_price)


def break_even_price(model: object, option_type: str) -> float:
    """Return a premium-adjusted terminal break-even price.

    Parameters
    ----------
    model : object
        Scalar pricing model exposing price and strike inputs.
    option_type : {"call", "put"}
        Vanilla option family.

    Returns
    -------
    float
        ``strike_price + premium`` for calls and ``strike_price - premium`` for
        puts, ignoring financing and trading frictions.
    """
    validated_option_type = validate_option_type(option_type)
    strike_price = _scalar_float(getattr(model, "strike_price", None), "strike_price")
    premium = option_price(model, validated_option_type)
    if validated_option_type == "call":
        return float(strike_price + premium)
    return float(strike_price - premium)


def select_option_greeks(raw_greeks: Mapping[str, object], option_type: str) -> dict[str, float]:
    """Select option-specific Greek names from a raw model Greek mapping.

    Parameters
    ----------
    raw_greeks : Mapping[str, object]
        Raw mapping returned by a model's ``greeks()`` method. The function
        accepts both generic keys such as ``"gamma"`` and option-specific keys
        such as ``"call_delta"``.
    option_type : {"call", "put"}
        Vanilla option family used to resolve option-specific keys.

    Returns
    -------
    dict[str, float]
        Normalized Greek dictionary using canonical names where available:
        ``delta``, ``gamma``, ``vega``, ``theta``, ``rho``, ``vanna``,
        ``volga``, and ``charm``.
    """
    validated_option_type = validate_option_type(option_type)
    prefix = f"{validated_option_type}_"
    candidate_keys = {
        "delta": (f"{prefix}delta", "delta"),
        "gamma": ("gamma",),
        "vega": ("vega",),
        "theta": (f"{prefix}theta", "theta"),
        "rho": (f"{prefix}rho", "rho"),
        "vanna": (f"{prefix}vanna", "vanna"),
        "volga": (f"{prefix}volga", "volga", "vomma"),
        "charm": (f"{prefix}charm", "charm"),
    }
    normalized: dict[str, float] = {}
    for canonical_name, aliases in candidate_keys.items():
        for alias in aliases:
            if alias in raw_greeks:
                value = raw_greeks[alias]
                with suppress(ValueError):
                    normalized[canonical_name] = _scalar_float(value, alias)
                break
    return normalized


def model_greeks(model: object, option_type: str) -> dict[str, float]:
    """Return option-specific Greeks when a model exposes them.

    Parameters
    ----------
    model : object
        Pricing model that may expose a ``greeks()`` method.
    option_type : {"call", "put"}
        Vanilla option family.

    Returns
    -------
    dict[str, float]
        Normalized option-specific Greek mapping. An empty dictionary is
        returned when the model has no Greek method.
    """
    greek_method = getattr(model, "greeks", None)
    if greek_method is None or not callable(greek_method):
        return {}
    return select_option_greeks(greek_method(), option_type)


def _volatility_attribute(model: object) -> tuple[str, float]:
    """Resolve the scalar volatility-like attribute used by scenario grids."""
    for attribute_name in ("volatility", "normal_volatility", "initial_volatility"):
        if hasattr(model, attribute_name):
            value = _scalar_float(getattr(model, attribute_name), attribute_name)
            if value <= 0:
                raise ValueError(f"{attribute_name} must be positive for derivative scenarios.")
            return attribute_name, value
    raise ValueError(
        f"{type(model).__name__} does not expose a supported volatility-like attribute."
    )


def _finite_sequence(values: Sequence[float], name: str) -> list[float]:
    """Return a non-empty list of finite scenario-axis values."""
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be a numeric sequence, not a string.")
    normalized = [float(value) for value in values]
    if not normalized:
        raise ValueError(f"{name} must contain at least one value.")
    if not all(np.isfinite(normalized)):
        raise ValueError(f"{name} must contain only finite values.")
    return normalized


def derivative_scenario_grid(
    model: object,
    *,
    spot_prices: Sequence[float],
    volatilities: Sequence[float],
    option_type: str = "call",
) -> DerivativeScenarioGrid:
    """Evaluate a vanilla option model over spot and volatility scenarios.

    Parameters
    ----------
    model : object
        Scalar option-pricing model exposing spot, strike, price, and a
        supported volatility-like attribute.
    spot_prices : Sequence[float]
        Underlying prices used for the spot scenario axis.
    volatilities : Sequence[float]
        Annualized decimal volatility values used for the volatility axis.
    option_type : {"call", "put"}, default="call"
        Vanilla option family to price in every grid cell.

    Returns
    -------
    DerivativeScenarioGrid
        Long-form grid containing prices, decomposition, moneyness, break-even,
        and Greeks where available.
    """
    validated_option_type = validate_option_type(option_type)
    scenario_spots = _finite_sequence(spot_prices, "spot_prices")
    scenario_volatilities = _finite_sequence(volatilities, "volatilities")
    if any(spot_price <= 0 for spot_price in scenario_spots):
        raise ValueError("spot_prices must be positive.")
    if any(volatility <= 0 for volatility in scenario_volatilities):
        raise ValueError("volatilities must be positive decimal values.")
    volatility_attribute, base_volatility = _volatility_attribute(model)
    base_spot_price = _scalar_float(getattr(model, "spot_price", None), "spot_price")
    rows: list[dict[str, float | str]] = []
    for spot_price in scenario_spots:
        for volatility in scenario_volatilities:
            repriced_model = copy(model)
            repriced_model.spot_price = float(spot_price)
            setattr(repriced_model, volatility_attribute, float(volatility))
            scenario_price = option_price(repriced_model, validated_option_type)
            scenario_intrinsic = current_intrinsic_value(repriced_model, validated_option_type)
            row: dict[str, float | str] = {
                "option_type": validated_option_type,
                "spot_price": float(spot_price),
                "volatility": float(volatility),
                "price": float(scenario_price),
                "intrinsic_value": float(scenario_intrinsic),
                "extrinsic_value": float(scenario_price - scenario_intrinsic),
                "moneyness": spot_moneyness(repriced_model),
                "forward_moneyness": forward_moneyness(repriced_model),
                "break_even_price": break_even_price(repriced_model, validated_option_type),
            }
            row.update(model_greeks(repriced_model, validated_option_type))
            rows.append(row)
    return DerivativeScenarioGrid(
        option_type=validated_option_type,
        data=pd.DataFrame(rows),
        base_spot_price=base_spot_price,
        base_volatility=base_volatility,
        volatility_attribute=volatility_attribute,
    )


def derivative_diagnostics(model: object, option_type: str = "call") -> DerivativeDiagnosticsReport:
    """Build a complete scalar diagnostics report for one vanilla derivative.

    Parameters
    ----------
    model : object
        Scalar option-pricing model exposing ``call_price()``, ``put_price()``,
        ``spot_price``, and ``strike_price``.
    option_type : {"call", "put"}, default="call"
        Vanilla option family.

    Returns
    -------
    DerivativeDiagnosticsReport
        Immutable scalar diagnostics report.
    """
    validated_option_type = validate_option_type(option_type)
    price = option_price(model, validated_option_type)
    intrinsic_value = current_intrinsic_value(model, validated_option_type)
    return DerivativeDiagnosticsReport(
        option_type=validated_option_type,
        price=price,
        intrinsic_value=intrinsic_value,
        extrinsic_value=float(price - intrinsic_value),
        moneyness=spot_moneyness(model),
        forward_moneyness=forward_moneyness(model),
        greeks=model_greeks(model, validated_option_type),
        break_even_price=break_even_price(model, validated_option_type),
        provenance=DataProvenance(
            provider="derived",
            dataset="derivative_diagnostics",
            source_labels=(type(model).__name__, validated_option_type),
            transformation_steps=(
                "model pricing",
                "intrinsic value decomposition",
                "moneyness calculation",
                "Greek selection",
            ),
            request={"model_class": type(model).__name__, "option_type": validated_option_type},
        ),
    )


class OptionDiagnosticsMixin:
    """Mixin adding scalar vanilla diagnostics to pricing model classes."""

    def price(self, option_type: str = "call") -> float:
        """Return this model's call or put price.

        Parameters
        ----------
        option_type : {"call", "put"}, default="call"
            Vanilla option family.

        Returns
        -------
        float
            Model price in currency units.
        """
        return option_price(self, option_type)

    def intrinsic_value(self, option_type: str = "call") -> float:
        """Return the current intrinsic value of the option.

        Parameters
        ----------
        option_type : {"call", "put"}, default="call"
            Vanilla option family.

        Returns
        -------
        float
            Immediate-exercise payoff at the current spot price.
        """
        return current_intrinsic_value(self, option_type)

    def extrinsic_value(self, option_type: str = "call") -> float:
        """Return the option's model value above intrinsic value.

        Parameters
        ----------
        option_type : {"call", "put"}, default="call"
            Vanilla option family.

        Returns
        -------
        float
            ``price(option_type) - intrinsic_value(option_type)``.
        """
        return current_extrinsic_value(self, option_type)

    def moneyness(self) -> float:
        """Return the current spot-to-strike moneyness ratio.

        Returns
        -------
        float
            Ratio ``spot_price / strike_price``.
        """
        return spot_moneyness(self)

    def forward_moneyness(self) -> float:
        """Return the forward-to-strike moneyness ratio.

        Returns
        -------
        float
            Forward moneyness under the model's forward convention.
        """
        return forward_moneyness(self)

    def break_even_price(self, option_type: str = "call") -> float:
        """Return the premium-adjusted terminal break-even price.

        Parameters
        ----------
        option_type : {"call", "put"}, default="call"
            Vanilla option family.

        Returns
        -------
        float
            Break-even terminal price ignoring financing and trading costs.
        """
        return break_even_price(self, option_type)

    def scenario_grid(
        self,
        *,
        spot_prices: Sequence[float],
        volatilities: Sequence[float],
        option_type: str = "call",
    ) -> DerivativeScenarioGrid:
        """Evaluate this option model over a spot--volatility scenario grid.

        Parameters
        ----------
        spot_prices : Sequence[float]
            Positive underlying prices for the scenario axis.
        volatilities : Sequence[float]
            Positive annualized decimal volatility values for the scenario axis.
        option_type : {"call", "put"}, default="call"
            Vanilla option family.

        Returns
        -------
        DerivativeScenarioGrid
            Long-form scenario grid with prices, decomposition, moneyness,
            break-even levels, and model Greeks where available.
        """
        return derivative_scenario_grid(
            self,
            spot_prices=spot_prices,
            volatilities=volatilities,
            option_type=option_type,
        )

    def report(self, option_type: str = "call"):
        """Return an exportable report for this option model.

        Parameters
        ----------
        option_type : {"call", "put"}, default="call"
            Vanilla option family.

        Returns
        -------
        ExportableReport
            Report object with ``to_markdown()``, ``to_html()``, and
            ``to_pdf()`` export methods.
        """
        from abaquant.reports import build_option_model_report

        return build_option_model_report(self, option_type=option_type)

    def diagnostics(self, option_type: str = "call") -> DerivativeDiagnosticsReport:
        """Return a complete scalar derivative diagnostics report.

        Parameters
        ----------
        option_type : {"call", "put"}, default="call"
            Vanilla option family.

        Returns
        -------
        DerivativeDiagnosticsReport
            Immutable price, decomposition, moneyness, Greek, and break-even
            report for this model.
        """
        return derivative_diagnostics(self, option_type)


__all__ = [
    "DerivativeDiagnosticsReport",
    "DerivativeScenarioGrid",
    "OptionDiagnosticsMixin",
    "break_even_price",
    "current_extrinsic_value",
    "current_intrinsic_value",
    "derivative_diagnostics",
    "derivative_scenario_grid",
    "forward_moneyness",
    "model_greeks",
    "option_price",
    "select_option_greeks",
    "spot_moneyness",
    "validate_option_type",
    "vanilla_intrinsic_value_from_prices",
]
