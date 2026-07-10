"""Annualized return and covariance statistics for ticker universes.

Purpose
-------
The module computes per-asset arithmetic means, volatility, and covariance matrices from aligned universe returns.

Conventions
-----------
Annualization uses the supplied periods-per-year factor, with 252 as the default. Covariances use pandas sample covariance conventions.

References
----------
[ 1 ] Markowitz, H. (1952), "Portfolio Selection".
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Literal

import numpy as np
import pandas as pd

from abaquant.financial_math import (
    annualized_covariance_from_returns,
    annualized_mean_returns_from_returns,
)

from .errors import InsufficientHistoryError

if TYPE_CHECKING:
    from .universe import MarketUniverse

ReturnKind = Literal["simple", "log"]


@dataclass(frozen=True)
class UniverseStatistics:
    """Annualized moment-estimation namespace for a :class:`MarketUniverse`.

    Attributes
    ----------
    universe : MarketUniverse
        Universe that supplies aligned historical returns through its lazy
        history namespace.

    Notes
    -----
    All estimates use complete aligned return observations and the caller's
    ``periods_per_year`` annualization factor.
    """

    universe: MarketUniverse

    def summary(
        self,
        *,
        kind: ReturnKind = "simple",
        start: str | date | None = None,
        end: str | date | None = None,
        period: str | None = "1y",
        interval: str = "1d",
        auto_adjust: bool = True,
        periods_per_year: int = 252,
    ) -> pd.DataFrame:
        """Compute per-asset annualized return and risk summary statistics.

        Parameters
        ----------
        kind : ReturnKind, default='simple'
            Return convention: ``"simple"`` for arithmetic returns or ``"log"`` for logarithmic returns.
        start : str | date | None, default=None
            Optional inclusive history start date.
        end : str | date | None, default=None
            Optional exclusive or provider-defined history end date.
        period : str | None, default='1y'
            Provider history period label, such as ``"1y"``, when explicit dates are not supplied.
        interval : str, default='1d'
            Provider sampling interval label, such as ``"1d"``.
        auto_adjust : bool, default=True
            Whether provider-adjusted price history is requested.
        periods_per_year : int, default=252
            Number of observations interpreted as one year for annualization.

        Returns
        -------
        pandas.DataFrame
            Tabular result with the index, column schema, units, and missing-value treatment defined by the module convention.

        Notes
        -----
        This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        aligned_return_panel = self.universe.history.returns(
            kind=kind,
            start=start,
            end=end,
            period=period,
            interval=interval,
            auto_adjust=auto_adjust,
            alignment="inner",
        ).dropna()
        _require_observations(aligned_return_panel, minimum=2)
        periodic_mean_returns = aligned_return_panel.mean()
        periodic_return_volatility = aligned_return_panel.std(ddof=1)
        return pd.DataFrame(
            {
                "mean_return": periodic_mean_returns,
                "annualized_return": periodic_mean_returns * periods_per_year,
                "volatility": periodic_return_volatility,
                "annualized_volatility": periodic_return_volatility * np.sqrt(periods_per_year),
                "skewness": aligned_return_panel.skew(),
                "excess_kurtosis": aligned_return_panel.kurt(),
                "minimum_return": aligned_return_panel.min(),
                "maximum_return": aligned_return_panel.max(),
                "observations": len(aligned_return_panel),
            }
        )

    def covariance(
        self,
        *,
        kind: ReturnKind = "simple",
        start: str | date | None = None,
        end: str | date | None = None,
        period: str | None = "1y",
        interval: str = "1d",
        auto_adjust: bool = True,
        periods_per_year: int = 252,
    ) -> pd.DataFrame:
        """Compute an annualized covariance matrix from aligned returns.

        Parameters
        ----------
        kind : ReturnKind, default='simple'
            Return convention: ``"simple"`` for arithmetic returns or ``"log"`` for logarithmic returns.
        start : str | date | None, default=None
            Optional inclusive history start date.
        end : str | date | None, default=None
            Optional exclusive or provider-defined history end date.
        period : str | None, default='1y'
            Provider history period label, such as ``"1y"``, when explicit dates are not supplied.
        interval : str, default='1d'
            Provider sampling interval label, such as ``"1d"``.
        auto_adjust : bool, default=True
            Whether provider-adjusted price history is requested.
        periods_per_year : int, default=252
            Number of observations interpreted as one year for annualization.

        Returns
        -------
        pandas.DataFrame
            Tabular result with the index, column schema, units, and missing-value treatment defined by the module convention.

        Notes
        -----
        This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        aligned_return_panel = self.universe.history.returns(
            kind=kind,
            start=start,
            end=end,
            period=period,
            interval=interval,
            auto_adjust=auto_adjust,
            alignment="inner",
        ).dropna()
        _require_observations(aligned_return_panel, minimum=2)
        return annualized_covariance_from_returns(
            aligned_return_panel,
            periods=periods_per_year,
        )

    def expected_returns(
        self,
        *,
        kind: ReturnKind = "simple",
        start: str | date | None = None,
        end: str | date | None = None,
        period: str | None = "1y",
        interval: str = "1d",
        auto_adjust: bool = True,
        periods_per_year: int = 252,
    ) -> pd.Series:
        """Compute annualized arithmetic expected returns from aligned returns.

        Parameters
        ----------
        kind : ReturnKind, default='simple'
            Return convention: ``"simple"`` for arithmetic returns or ``"log"`` for logarithmic returns.
        start : str | date | None, default=None
            Optional inclusive history start date.
        end : str | date | None, default=None
            Optional exclusive or provider-defined history end date.
        period : str | None, default='1y'
            Provider history period label, such as ``"1y"``, when explicit dates are not supplied.
        interval : str, default='1d'
            Provider sampling interval label, such as ``"1d"``.
        auto_adjust : bool, default=True
            Whether provider-adjusted price history is requested.
        periods_per_year : int, default=252
            Number of observations interpreted as one year for annualization.

        Returns
        -------
        pd.Series
            One-dimensional labeled result aligned to the documented input order.

        Notes
        -----
        This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        aligned_return_panel = self.universe.history.returns(
            kind=kind,
            start=start,
            end=end,
            period=period,
            interval=interval,
            auto_adjust=auto_adjust,
            alignment="inner",
        ).dropna()
        _require_observations(aligned_return_panel, minimum=2)
        return annualized_mean_returns_from_returns(
            aligned_return_panel,
            periods=periods_per_year,
        )


def _require_observations(
    aligned_return_panel: pd.DataFrame,
    *,
    minimum: int,
) -> None:
    """Ensure an aligned return panel contains enough observations.

    Parameters
    ----------
    aligned_return_panel : pandas.DataFrame
        Complete-case periodic return observations, with dates in rows and
        universe symbols in columns.
    minimum : int
        Minimum required row count.

    Raises
    ------
    InsufficientHistoryError
        If the panel has fewer than ``minimum`` observations.
    """
    if len(aligned_return_panel) < minimum:
        raise InsufficientHistoryError(
            f"At least {minimum} aligned return observations are required."
        )


# Backward-compatible alias for the original Phase-2 namespace class name.
MarketUniverseStatistics = UniverseStatistics
