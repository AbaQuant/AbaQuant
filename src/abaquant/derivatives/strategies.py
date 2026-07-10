"""Composable option-strategy objects and expiration payoff profiles.

Purpose
-------
The module defines static option strategies built from long and short call,
put, and underlying legs. Strategies can be evaluated at a single terminal
underlying price, expanded into payoff tables, inspected for maximum profit,
maximum loss, and break-even points, and visualized through the optional
AbaQuant visualization layer.

Conventions
-----------
A positive ``position`` denotes a long leg and a negative ``position`` denotes
a short leg. Premiums are quoted as positive currency amounts per contract. By
default, strategy ``payoff`` methods report net expiration profit after option
premiums and underlying entry costs. Use ``gross_payoff`` to exclude inception
cash flows.

Scope and limitations
---------------------
Strategies are static expiration profiles. They do not model early exercise,
dynamic hedging, funding, margin, bid--ask slippage, taxes, assignment timing,
or path-dependent risk.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

OptionType = Literal["call", "put"]
LegKind = Literal["call", "put", "underlying"]


def _validate_option_type(option_type: str) -> OptionType:
    """Return a normalized option type label.

    Parameters
    ----------
    option_type : str
        Candidate option family.

    Returns
    -------
    {"call", "put"}
        Normalized option family.

    Raises
    ------
    ValueError
        If the label is not ``"call"`` or ``"put"``.
    """
    normalized = str(option_type).lower().strip()
    if normalized not in {"call", "put"}:
        raise ValueError("option_type must be 'call' or 'put'.")
    return normalized  # type: ignore[return-value]


def _finite_positive(value: float, name: str, *, allow_zero: bool = False) -> float:
    """Validate and return one finite non-negative or positive scalar.

    Parameters
    ----------
    value : float
        Candidate scalar.
    name : str
        Name used in the error message.
    allow_zero : bool, default=False
        Whether zero is an admissible value.

    Returns
    -------
    float
        Validated scalar.
    """
    scalar = float(value)
    if not np.isfinite(scalar):
        raise ValueError(f"{name} must be finite.")
    if allow_zero:
        if scalar < 0.0:
            raise ValueError(f"{name} must be non-negative.")
    elif scalar <= 0.0:
        raise ValueError(f"{name} must be positive.")
    return scalar


def option_payoff_leg(
    option_type: str,
    position: int,
    terminal_prices: np.ndarray,
    strike: float,
    premium: float,
) -> np.ndarray:
    """Evaluate one legacy option leg's net expiration profit.

    Parameters
    ----------
    option_type : str
        Option type label, either ``"call"`` or ``"put"``.
    position : int
        Position side. ``1`` represents a long option and ``-1`` represents a
        short option.
    terminal_prices : numpy.ndarray
        Terminal underlying-price grid in currency units.
    strike : float
        Option strike price in the same currency units as the underlying.
    premium : float
        Positive premium paid by a long option holder and received by a short
        option writer.

    Returns
    -------
    numpy.ndarray
        Net expiration profit for the option leg, including premium.
    """
    option_leg = OptionStrategyLeg.option(
        option_type=option_type,
        position=position,
        strike=strike,
        premium=premium,
        quantity=1.0,
    )
    return option_leg.profit(terminal_prices)


@dataclass(frozen=True)
class OptionStrategyLeg:
    """One line item in a static option strategy.

    Parameters
    ----------
    kind : {"call", "put", "underlying"}
        Type of financial exposure represented by the leg.
    position : float
        Signed direction of the exposure. Positive values are long exposures;
        negative values are short exposures.
    quantity : float, default=1.0
        Number of contracts or underlying units represented by the leg.
    strike : float, optional
        Strike price for option legs. Must be ``None`` for an underlying leg.
    premium : float, default=0.0
        Option premium per contract in currency units. Must be non-negative.
    entry_price : float, optional
        Underlying entry price per unit for stock-like legs.
    label : str, optional
        Human-readable label used in payoff tables and plots. A default label
        is generated when omitted.
    """

    kind: LegKind
    position: float
    quantity: float = 1.0
    strike: float | None = None
    premium: float = 0.0
    entry_price: float | None = None
    label: str | None = None

    def __post_init__(self) -> None:
        """Validate leg direction, size, strike, premium, and entry price."""
        if self.kind not in {"call", "put", "underlying"}:
            raise ValueError("kind must be 'call', 'put', or 'underlying'.")
        if not np.isfinite(float(self.position)) or float(self.position) == 0.0:
            raise ValueError("position must be finite and non-zero.")
        object.__setattr__(self, "quantity", _finite_positive(self.quantity, "quantity"))
        object.__setattr__(
            self, "premium", _finite_positive(self.premium, "premium", allow_zero=True)
        )
        if self.kind in {"call", "put"}:
            if self.strike is None:
                raise ValueError("option legs require strike.")
            object.__setattr__(self, "strike", _finite_positive(self.strike, "strike"))
            if self.entry_price is not None:
                raise ValueError("option legs must not set entry_price.")
        else:
            if self.strike is not None:
                raise ValueError("underlying legs must not set strike.")
            if self.entry_price is None:
                raise ValueError("underlying legs require entry_price.")
            object.__setattr__(
                self, "entry_price", _finite_positive(self.entry_price, "entry_price")
            )

    @classmethod
    def option(
        cls,
        *,
        option_type: str,
        position: float,
        strike: float,
        premium: float,
        quantity: float = 1.0,
        label: str | None = None,
    ) -> OptionStrategyLeg:
        """Create one call or put leg.

        Parameters
        ----------
        option_type : {"call", "put"}
            Vanilla option family.
        position : float
            Positive for long exposure and negative for short exposure.
        strike : float
            Option strike price.
        premium : float
            Premium per contract in currency units.
        quantity : float, default=1.0
            Contract count.
        label : str, optional
            Custom display label.

        Returns
        -------
        OptionStrategyLeg
            Validated option leg.
        """
        return cls(
            kind=_validate_option_type(option_type),
            position=float(position),
            quantity=quantity,
            strike=strike,
            premium=premium,
            label=label,
        )

    @classmethod
    def underlying(
        cls,
        *,
        position: float,
        entry_price: float,
        quantity: float = 1.0,
        label: str | None = None,
    ) -> OptionStrategyLeg:
        """Create one underlying asset leg.

        Parameters
        ----------
        position : float
            Positive for long underlying exposure and negative for short
            underlying exposure.
        entry_price : float
            Initial purchase or sale price per underlying unit.
        quantity : float, default=1.0
            Number of underlying units.
        label : str, optional
            Custom display label.

        Returns
        -------
        OptionStrategyLeg
            Validated underlying leg.
        """
        return cls(
            kind="underlying",
            position=float(position),
            quantity=quantity,
            entry_price=entry_price,
            label=label,
        )

    def display_label(self) -> str:
        """Return the label used in strategy profiles and charts."""
        if self.label:
            return self.label
        side = "Long" if self.position > 0 else "Short"
        size = abs(self.position * self.quantity)
        if self.kind == "underlying":
            return f"{side} underlying x {size:g}"
        return f"{side} {self.kind.capitalize()} K={self.strike:g} x {size:g}"

    def gross_payoff(self, spot_price: float | Sequence[float] | np.ndarray) -> float | np.ndarray:
        """Evaluate the terminal payoff before inception cash flows.

        Parameters
        ----------
        spot_price : float or array-like
            Terminal underlying price or price grid.

        Returns
        -------
        float or numpy.ndarray
            Signed terminal payoff before premiums or underlying entry costs.
        """
        prices = np.asarray(spot_price, dtype=float)
        if self.kind == "call":
            intrinsic = np.maximum(prices - float(self.strike), 0.0)
        elif self.kind == "put":
            intrinsic = np.maximum(float(self.strike) - prices, 0.0)
        else:
            intrinsic = prices
        payoff = float(self.position) * float(self.quantity) * intrinsic
        return float(payoff) if np.ndim(payoff) == 0 else payoff

    def net_inception_cost(self) -> float:
        """Return the initial net cash cost of the leg.

        Positive values represent net cash paid at inception. Negative values
        represent net cash received at inception.
        """
        if self.kind == "underlying":
            return float(self.position) * float(self.quantity) * float(self.entry_price)
        return float(self.position) * float(self.quantity) * float(self.premium)

    def profit(self, spot_price: float | Sequence[float] | np.ndarray) -> float | np.ndarray:
        """Evaluate terminal net profit after inception cash flows.

        Parameters
        ----------
        spot_price : float or array-like
            Terminal underlying price or price grid.

        Returns
        -------
        float or numpy.ndarray
            Terminal payoff minus the net inception cost.
        """
        payoff = np.asarray(self.gross_payoff(spot_price), dtype=float) - self.net_inception_cost()
        return float(payoff) if payoff.ndim == 0 else payoff

    def terminal_slope(self) -> float:
        """Return the profit slope as the terminal price tends to infinity."""
        if self.kind == "put":
            return 0.0
        return float(self.position) * float(self.quantity)


class OptionStrategy:
    """Composable static option strategy with payoff and risk diagnostics.

    Notes
    -----
    Builder methods mutate the strategy and return ``self`` so scripts can use
    either imperative or chained construction. The analytics are deterministic
    expiration calculations and do not require a market-data provider.
    """

    def __init__(self, legs: Iterable[OptionStrategyLeg] | None = None, *, name: str | None = None):
        self._legs = list(legs or [])
        self.name = name or "Option strategy"

    @property
    def legs(self) -> tuple[OptionStrategyLeg, ...]:
        """Return the strategy legs as an immutable tuple."""
        return tuple(self._legs)

    def add_leg(self, leg: OptionStrategyLeg) -> OptionStrategy:
        """Append a validated leg and return ``self`` for chaining.

        Parameters
        ----------
        leg : OptionStrategyLeg
            Strategy leg to append.

        Returns
        -------
        OptionStrategy
            This strategy after mutation.
        """
        if not isinstance(leg, OptionStrategyLeg):
            raise TypeError("leg must be an OptionStrategyLeg instance.")
        self._legs.append(leg)
        return self

    def buy_call(self, *, strike: float, premium: float, quantity: float = 1.0) -> OptionStrategy:
        """Add a long call leg and return the strategy."""
        return self.add_leg(
            OptionStrategyLeg.option(
                option_type="call", position=1.0, strike=strike, premium=premium, quantity=quantity
            )
        )

    def sell_call(self, *, strike: float, premium: float, quantity: float = 1.0) -> OptionStrategy:
        """Add a short call leg and return the strategy."""
        return self.add_leg(
            OptionStrategyLeg.option(
                option_type="call", position=-1.0, strike=strike, premium=premium, quantity=quantity
            )
        )

    def buy_put(self, *, strike: float, premium: float, quantity: float = 1.0) -> OptionStrategy:
        """Add a long put leg and return the strategy."""
        return self.add_leg(
            OptionStrategyLeg.option(
                option_type="put", position=1.0, strike=strike, premium=premium, quantity=quantity
            )
        )

    def sell_put(self, *, strike: float, premium: float, quantity: float = 1.0) -> OptionStrategy:
        """Add a short put leg and return the strategy."""
        return self.add_leg(
            OptionStrategyLeg.option(
                option_type="put", position=-1.0, strike=strike, premium=premium, quantity=quantity
            )
        )

    def buy_underlying(self, *, entry_price: float, quantity: float = 1.0) -> OptionStrategy:
        """Add a long underlying leg and return the strategy."""
        return self.add_leg(
            OptionStrategyLeg.underlying(position=1.0, entry_price=entry_price, quantity=quantity)
        )

    def sell_underlying(self, *, entry_price: float, quantity: float = 1.0) -> OptionStrategy:
        """Add a short underlying leg and return the strategy."""
        return self.add_leg(
            OptionStrategyLeg.underlying(position=-1.0, entry_price=entry_price, quantity=quantity)
        )

    @classmethod
    def bull_call_spread(
        cls,
        *,
        lower_strike: float,
        upper_strike: float,
        lower_premium: float,
        upper_premium: float,
        quantity: float = 1.0,
    ) -> OptionStrategy:
        """Create a long bull call spread.

        The strategy buys the lower-strike call and sells the higher-strike
        call with the same quantity.
        """
        if upper_strike <= lower_strike:
            raise ValueError("upper_strike must exceed lower_strike.")
        return (
            cls(name="Bull call spread")
            .buy_call(strike=lower_strike, premium=lower_premium, quantity=quantity)
            .sell_call(strike=upper_strike, premium=upper_premium, quantity=quantity)
        )

    @classmethod
    def protective_put(
        cls,
        *,
        underlying_entry_price: float,
        put_strike: float,
        put_premium: float,
        quantity: float = 1.0,
    ) -> OptionStrategy:
        """Create a protective put from a long underlying and long put."""
        return (
            cls(name="Protective put")
            .buy_underlying(entry_price=underlying_entry_price, quantity=quantity)
            .buy_put(strike=put_strike, premium=put_premium, quantity=quantity)
        )

    @classmethod
    def straddle(
        cls,
        *,
        strike: float,
        call_premium: float,
        put_premium: float,
        quantity: float = 1.0,
    ) -> OptionStrategy:
        """Create a long straddle using one call and one put at one strike."""
        return (
            cls(name="Long straddle")
            .buy_call(strike=strike, premium=call_premium, quantity=quantity)
            .buy_put(strike=strike, premium=put_premium, quantity=quantity)
        )

    @classmethod
    def strangle(
        cls,
        *,
        put_strike: float,
        call_strike: float,
        put_premium: float,
        call_premium: float,
        quantity: float = 1.0,
    ) -> OptionStrategy:
        """Create a long strangle using an out-of-the-money put and call."""
        if call_strike <= put_strike:
            raise ValueError("call_strike must exceed put_strike.")
        return (
            cls(name="Long strangle")
            .buy_put(strike=put_strike, premium=put_premium, quantity=quantity)
            .buy_call(strike=call_strike, premium=call_premium, quantity=quantity)
        )

    @classmethod
    def iron_condor(
        cls,
        *,
        lower_put_strike: float,
        short_put_strike: float,
        short_call_strike: float,
        upper_call_strike: float,
        lower_put_premium: float,
        short_put_premium: float,
        short_call_premium: float,
        upper_call_premium: float,
        quantity: float = 1.0,
    ) -> OptionStrategy:
        """Create a long-wing iron condor with four option legs."""
        if not lower_put_strike < short_put_strike < short_call_strike < upper_call_strike:
            raise ValueError("iron condor strikes must be strictly increasing.")
        return (
            cls(name="Iron condor")
            .buy_put(strike=lower_put_strike, premium=lower_put_premium, quantity=quantity)
            .sell_put(strike=short_put_strike, premium=short_put_premium, quantity=quantity)
            .sell_call(strike=short_call_strike, premium=short_call_premium, quantity=quantity)
            .buy_call(strike=upper_call_strike, premium=upper_call_premium, quantity=quantity)
        )

    @classmethod
    def butterfly(
        cls,
        *,
        lower_strike: float,
        middle_strike: float,
        upper_strike: float,
        lower_premium: float,
        middle_premium: float,
        upper_premium: float,
        option_type: OptionType = "call",
        quantity: float = 1.0,
    ) -> OptionStrategy:
        """Create a symmetric or asymmetric long butterfly.

        The strategy buys the lower and upper strikes and sells twice the
        middle strike using either calls or puts.
        """
        validated_type = _validate_option_type(option_type)
        if not lower_strike < middle_strike < upper_strike:
            raise ValueError("butterfly strikes must be strictly increasing.")
        strategy = cls(name=f"Long {validated_type} butterfly")
        add_long = strategy.buy_call if validated_type == "call" else strategy.buy_put
        add_short = strategy.sell_call if validated_type == "call" else strategy.sell_put
        add_long(strike=lower_strike, premium=lower_premium, quantity=quantity)
        add_short(strike=middle_strike, premium=middle_premium, quantity=2.0 * quantity)
        add_long(strike=upper_strike, premium=upper_premium, quantity=quantity)
        return strategy

    def net_inception_cost(self) -> float:
        """Return total net cash paid at inception."""
        return float(sum(leg.net_inception_cost() for leg in self._legs))

    def gross_payoff(self, spot_price: float | Sequence[float] | np.ndarray) -> float | np.ndarray:
        """Evaluate strategy payoff before premiums and entry costs."""
        if not self._legs:
            raise ValueError("OptionStrategy must contain at least one leg.")
        prices = np.asarray(spot_price, dtype=float)
        payoff = np.zeros_like(prices, dtype=float)
        for leg in self._legs:
            payoff = payoff + np.asarray(leg.gross_payoff(prices), dtype=float)
        return float(payoff) if payoff.ndim == 0 else payoff

    def profit(self, spot_price: float | Sequence[float] | np.ndarray) -> float | np.ndarray:
        """Evaluate terminal net profit after inception cash flows."""
        payoff = np.asarray(self.gross_payoff(spot_price), dtype=float) - self.net_inception_cost()
        return float(payoff) if payoff.ndim == 0 else payoff

    def payoff(
        self,
        spot_price: float | Sequence[float] | np.ndarray,
        *,
        include_premium: bool = True,
    ) -> float | np.ndarray:
        """Evaluate the strategy expiration payoff or profit.

        Parameters
        ----------
        spot_price : float or array-like
            Terminal underlying price or price grid.
        include_premium : bool, default=True
            When ``True``, return net profit after option premiums and
            underlying entry costs. When ``False``, return gross terminal
            payoff only.

        Returns
        -------
        float or numpy.ndarray
            Net profit or gross terminal payoff according to
            ``include_premium``.
        """
        return self.profit(spot_price) if include_premium else self.gross_payoff(spot_price)

    def profile(
        self,
        *,
        spot_prices: Sequence[float] | np.ndarray | None = None,
        spot_min: float | None = None,
        spot_max: float | None = None,
        points: int = 501,
        include_leg_columns: bool = True,
    ) -> pd.DataFrame:
        """Return a payoff table over terminal underlying prices.

        Parameters
        ----------
        spot_prices : array-like, optional
            Explicit terminal price grid. When supplied, ``spot_min``,
            ``spot_max``, and ``points`` are ignored.
        spot_min, spot_max : float, optional
            Bounds for a generated terminal-price grid.
        points : int, default=501
            Number of grid points when ``spot_prices`` is omitted.
        include_leg_columns : bool, default=True
            Include per-leg profit columns in addition to aggregate columns.

        Returns
        -------
        pandas.DataFrame
            Table with ``spot_price``, ``gross_payoff``, ``net_profit``, and
            optional per-leg profit columns.
        """
        prices = self._spot_grid(
            spot_prices=spot_prices, spot_min=spot_min, spot_max=spot_max, points=points
        )
        data: dict[str, np.ndarray] = {
            "spot_price": prices,
            "gross_payoff": np.asarray(self.gross_payoff(prices), dtype=float),
            "net_profit": np.asarray(self.profit(prices), dtype=float),
        }
        if include_leg_columns:
            for index, leg in enumerate(self._legs, start=1):
                column = f"leg_{index}_{leg.display_label()}"
                data[column] = np.asarray(leg.profit(prices), dtype=float)
        return pd.DataFrame(data)

    def max_profit(self) -> float:
        """Return maximum expiration profit, or ``np.inf`` if unbounded above."""
        if self._terminal_slope() > 0.0:
            return float(np.inf)
        return float(np.max([self.profit(price) for price in self._candidate_prices()]))

    def max_loss(self) -> float:
        """Return minimum expiration profit, or ``-np.inf`` if unbounded below."""
        if self._terminal_slope() < 0.0:
            return float(-np.inf)
        return float(np.min([self.profit(price) for price in self._candidate_prices()]))

    def break_even_points(self, *, tolerance: float = 1e-10) -> list[float]:
        """Return terminal prices where net profit is approximately zero.

        Parameters
        ----------
        tolerance : float, default=1e-10
            Numerical tolerance used for duplicate removal and exact-zero
            detection.

        Returns
        -------
        list[float]
            Sorted break-even terminal prices. The list may be empty when a
            strategy has no non-negative-price break-even point.
        """
        points = self._candidate_prices()
        roots: list[float] = []
        for left, right in pairwise(points):
            left_value = float(self.profit(left))
            right_value = float(self.profit(right))
            if abs(left_value) <= tolerance:
                roots.append(left)
            if abs(right_value) <= tolerance:
                roots.append(right)
            if left_value * right_value < 0.0:
                roots.append(left - left_value * (right - left) / (right_value - left_value))
        last = points[-1]
        last_value = float(self.profit(last))
        tail_slope = self._terminal_slope()
        if abs(last_value) <= tolerance:
            roots.append(last)
        if abs(tail_slope) > tolerance:
            root = last - last_value / tail_slope
            if root >= last - tolerance:
                roots.append(max(0.0, root))
        return _unique_sorted(roots, tolerance=tolerance)

    def as_dict(self) -> dict[str, object]:
        """Return a plain-Python summary of the strategy and diagnostics."""
        return {
            "name": self.name,
            "legs": [leg.__dict__.copy() for leg in self._legs],
            "net_inception_cost": self.net_inception_cost(),
            "max_profit": self.max_profit(),
            "max_loss": self.max_loss(),
            "break_even_points": self.break_even_points(),
        }

    def visualize(
        self,
        *,
        chart: str = "payoff",
        backend: str | None = None,
        theme=None,
        save_path: str | Path | None = None,
        filename: str | None = None,
        spot_min: float | None = None,
        spot_max: float | None = None,
        points: int = 501,
    ):
        """Visualize the strategy payoff or component profile.

        Parameters
        ----------
        chart : {"payoff", "components"}, default="payoff"
            ``"payoff"`` plots aggregate net profit. ``"components"`` plots
            aggregate net profit and each leg's contribution.
        backend : {"matplotlib", "plotly"}, optional
            Visualization backend override.
        theme : VisualizationTheme, optional
            Per-call theme override.
        save_path : str or pathlib.Path, optional
            Explicit export path.
        filename : str, optional
            Filename relative to the active theme save directory.
        spot_min, spot_max : float, optional
            Terminal-price grid bounds.
        points : int, default=501
            Number of grid points.

        Returns
        -------
        matplotlib.figure.Figure or plotly.graph_objects.Figure
            Backend-native figure object.
        """
        from abaquant.visualization import visualize_option_strategy

        return visualize_option_strategy(
            self,
            chart=chart,
            backend=backend,
            theme=theme,
            save_path=save_path,
            filename=filename,
            spot_min=spot_min,
            spot_max=spot_max,
            points=points,
        )

    def _terminal_slope(self) -> float:
        """Return the strategy profit slope for very large terminal prices."""
        return float(sum(leg.terminal_slope() for leg in self._legs))

    def _candidate_prices(self) -> list[float]:
        """Return kink prices at which a piecewise-linear payoff can change slope."""
        if not self._legs:
            raise ValueError("OptionStrategy must contain at least one leg.")
        strikes = [float(leg.strike) for leg in self._legs if leg.strike is not None]
        return _unique_sorted([0.0, *strikes])

    def _spot_grid(
        self,
        *,
        spot_prices: Sequence[float] | np.ndarray | None,
        spot_min: float | None,
        spot_max: float | None,
        points: int,
    ) -> np.ndarray:
        """Return the terminal-price grid used for tables and charts."""
        if spot_prices is not None:
            prices = np.asarray(spot_prices, dtype=float)
            if prices.ndim != 1 or prices.size == 0 or not np.all(np.isfinite(prices)):
                raise ValueError("spot_prices must be a one-dimensional finite array.")
            if np.any(prices < 0.0):
                raise ValueError("spot_prices cannot contain negative values.")
            return np.sort(prices)
        if points < 2:
            raise ValueError("points must be at least two.")
        references = [float(leg.strike) for leg in self._legs if leg.strike is not None]
        references.extend(
            float(leg.entry_price) for leg in self._legs if leg.entry_price is not None
        )
        upper_reference = max(references or [1.0])
        lower = 0.0 if spot_min is None else _finite_positive(spot_min, "spot_min", allow_zero=True)
        upper = (
            2.0 * upper_reference if spot_max is None else _finite_positive(spot_max, "spot_max")
        )
        if upper <= lower:
            raise ValueError("spot_max must exceed spot_min.")
        return np.linspace(lower, upper, points)


def _unique_sorted(values: Iterable[float], *, tolerance: float = 1e-10) -> list[float]:
    """Return sorted non-negative finite values with near-duplicates removed."""
    clean = sorted(float(value) for value in values if np.isfinite(value) and float(value) >= 0.0)
    unique: list[float] = []
    for value in clean:
        if not unique or abs(value - unique[-1]) > tolerance:
            unique.append(value)
    return unique


def strategy_profile(spot: float, legs: list[dict], points: int = 500) -> pd.DataFrame:
    """Evaluate a legacy dictionary-based static strategy profile.

    Parameters
    ----------
    spot : float
        Current underlying or asset spot price used to build a terminal-price
        grid from ``0.5 * spot`` to ``1.5 * spot``.
    legs : list[dict]
        Sequence of option-leg specifications with ``option_type``,
        ``position``, ``strike``, and ``premium`` keys.
    points : int, default=500
        Number of terminal-price grid points.

    Returns
    -------
    pandas.DataFrame
        Payoff table preserving the historical ``S_T``, per-leg, and
        ``Net Payoff`` column names while using the validated leg payoff
        calculation internally.
    """
    terminal_prices = np.linspace(float(spot) * 0.5, float(spot) * 1.5, points)
    net_payoff = np.zeros_like(terminal_prices)
    data: dict[str, np.ndarray] = {"S_T": terminal_prices}
    for leg in legs:
        option_type = leg["option_type"]
        position = leg["position"]
        strike = leg["strike"]
        premium = leg["premium"]
        payoff = option_payoff_leg(option_type, position, terminal_prices, strike, premium)
        net_payoff += payoff
        label = f"{'Long' if position == 1 else 'Short'} {str(option_type).capitalize()} K={strike}"
        data[label] = payoff
    data["Net Payoff"] = net_payoff
    return pd.DataFrame(data)


__all__ = [
    "OptionStrategy",
    "OptionStrategyLeg",
    "OptionType",
    "option_payoff_leg",
    "strategy_profile",
]
