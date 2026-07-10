"""Applied static portfolio construction for ticker universes.

Purpose
-------
The module converts a universe return panel into equal-weight, minimum-variance, maximum-Sharpe, and user-specified portfolio evaluations.

Conventions
-----------
Risk-free rates are annualized decimal arithmetic rates. Optimizers use the core pure portfolio functions and require at least two assets.

Scope and limitations
---------------------
Results are static in-sample calculations; the lightweight backtest adds deterministic rebalancing and explicit transaction costs but still excludes execution, taxes, financing, and market impact.

References
----------
[ 1 ] Markowitz, H. (1952), "Portfolio Selection".
[ 2 ] Sharpe, W. F. (1966), "Mutual Fund Performance".
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Literal

import numpy as np
import pandas as pd

from abaquant.financial_math import (
    annualized_covariance_from_returns,
    annualized_mean_returns_from_returns,
    equal_weight,
    maximum_sharpe_weights,
    minimum_variance_weights,
    portfolio_return,
    portfolio_sharpe,
    portfolio_volatility,
)
from abaquant.portfolio.optimization import PortfolioScenarioAnalysis

from .errors import (
    InsufficientHistoryError,
    PortfolioOptimizationError,
    PortfolioValidationError,
)
from .models import PortfolioResult

if TYPE_CHECKING:
    import pandas as pd

    from .universe import MarketUniverse

ReturnKind = Literal["simple", "log"]


@dataclass(frozen=True)
class UniversePortfolioAnalytics:
    """Static portfolio-analysis namespace for a :class:`MarketUniverse`.

    The namespace requests aligned returns lazily through ``universe.history``
    and delegates estimation and optimization to the pure financial-math
    layer. It does not retain raw provider objects or execute trades.

    Attributes
    ----------
    universe : MarketUniverse
        Universe that supplies normalized ticker symbols, market-data provider,
        and historical return panels.
    """

    universe: MarketUniverse

    def equal_weight(
        self,
        *,
        risk_free_rate: float,
        kind: ReturnKind = "simple",
        start: str | date | None = None,
        end: str | date | None = None,
        period: str | None = "1y",
        interval: str = "1d",
        auto_adjust: bool = True,
        periods_per_year: int = 252,
    ) -> PortfolioResult:
        """Construct or evaluate an equally weighted fully invested portfolio.

        Parameters
        ----------
        risk_free_rate : float
            Annual risk-free rate in decimal units.
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
            Number of periodic observations interpreted as one year for annualization.

        Returns
        -------
        PortfolioResult
            Immutable result containing equal 1/N weights indexed by universe symbol,
            together with annualized expected return, volatility, and Sharpe ratio.

        Notes
        -----
        This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        self._require_two_assets()
        annualized_expected_returns, annualized_covariance_matrix, return_observation_count = (
            self._inputs(
                kind=kind,
                start=start,
                end=end,
                period=period,
                interval=interval,
                auto_adjust=auto_adjust,
                periods_per_year=periods_per_year,
            )
        )
        equal_weight_vector = equal_weight(len(self.universe.symbols))
        return self._result(
            equal_weight_vector,
            annualized_expected_returns,
            annualized_covariance_matrix,
            risk_free_rate,
            return_observation_count,
            "equal_weight",
        )

    def minimum_variance(
        self,
        *,
        risk_free_rate: float,
        bounds: tuple[float, float] = (0.0, 1.0),
        kind: ReturnKind = "simple",
        start: str | date | None = None,
        end: str | date | None = None,
        period: str | None = "1y",
        interval: str = "1d",
        auto_adjust: bool = True,
        periods_per_year: int = 252,
    ) -> PortfolioResult:
        """Construct a bounded global minimum-variance portfolio.

        Parameters
        ----------
        risk_free_rate : float
            Annual risk-free rate in decimal units.
        bounds : tuple[float, float], default=(0.0, 1.0)
            Allocation bounds in the format accepted by the underlying optimizer.
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
            Number of periodic observations interpreted as one year for annualization.

        Returns
        -------
        PortfolioResult
            Immutable result containing indexed weights and annualized portfolio performance statistics.

        Notes
        -----
        This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        self._require_two_assets()
        annualized_expected_returns, annualized_covariance_matrix, return_observation_count = (
            self._inputs(
                kind=kind,
                start=start,
                end=end,
                period=period,
                interval=interval,
                auto_adjust=auto_adjust,
                periods_per_year=periods_per_year,
            )
        )
        try:
            optimized_weight_vector = minimum_variance_weights(
                annualized_covariance_matrix.to_numpy(),
                bounds=bounds,
            )
        except ValueError as exc:
            raise PortfolioOptimizationError(str(exc)) from exc
        return self._result(
            optimized_weight_vector,
            annualized_expected_returns,
            annualized_covariance_matrix,
            risk_free_rate,
            return_observation_count,
            "minimum_variance",
        )

    def max_sharpe(
        self,
        *,
        risk_free_rate: float,
        bounds: tuple[float, float] = (0.0, 1.0),
        kind: ReturnKind = "simple",
        start: str | date | None = None,
        end: str | date | None = None,
        period: str | None = "1y",
        interval: str = "1d",
        auto_adjust: bool = True,
        periods_per_year: int = 252,
    ) -> PortfolioResult:
        """Construct a bounded maximum-Sharpe-ratio portfolio.

        Parameters
        ----------
        risk_free_rate : float
            Annual risk-free rate in decimal units.
        bounds : tuple[float, float], default=(0.0, 1.0)
            Allocation bounds in the format accepted by the underlying optimizer.
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
            Number of periodic observations interpreted as one year for annualization.

        Returns
        -------
        PortfolioResult
            Immutable result containing indexed weights and annualized portfolio performance statistics.

        Notes
        -----
        This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        self._require_two_assets()
        annualized_expected_returns, annualized_covariance_matrix, return_observation_count = (
            self._inputs(
                kind=kind,
                start=start,
                end=end,
                period=period,
                interval=interval,
                auto_adjust=auto_adjust,
                periods_per_year=periods_per_year,
            )
        )
        try:
            optimized_weight_vector = maximum_sharpe_weights(
                annualized_expected_returns.to_numpy(),
                annualized_covariance_matrix.to_numpy(),
                risk_free_rate=risk_free_rate,
                bounds=bounds,
            )
        except ValueError as exc:
            raise PortfolioOptimizationError(str(exc)) from exc
        return self._result(
            optimized_weight_vector,
            annualized_expected_returns,
            annualized_covariance_matrix,
            risk_free_rate,
            return_observation_count,
            "max_sharpe",
        )

    def evaluate(
        self,
        weights: Mapping[str, float] | Sequence[float],
        *,
        risk_free_rate: float,
        kind: ReturnKind = "simple",
        start: str | date | None = None,
        end: str | date | None = None,
        period: str | None = "1y",
        interval: str = "1d",
        auto_adjust: bool = True,
        periods_per_year: int = 252,
    ) -> PortfolioResult:
        """Evaluate a user-supplied portfolio allocation against historical inputs.

        Parameters
        ----------
        weights : Mapping[str, float] | Sequence[float]
            Portfolio weights, either a mapping keyed by asset or an ordered numeric vector as documented by the callable.
        risk_free_rate : float
            Annual risk-free rate in decimal units.
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
            Number of periodic observations interpreted as one year for annualization.

        Returns
        -------
        PortfolioResult
            Immutable result containing indexed weights and annualized portfolio performance statistics.

        Notes
        -----
        The applied layer normalizes provider data but cannot guarantee provider completeness, timeliness, or accuracy.
        """
        annualized_expected_returns, annualized_covariance_matrix, return_observation_count = (
            self._inputs(
                kind=kind,
                start=start,
                end=end,
                period=period,
                interval=interval,
                auto_adjust=auto_adjust,
                periods_per_year=periods_per_year,
            )
        )
        weight_vector = self._coerce_weights(weights)
        return self._result(
            weight_vector,
            annualized_expected_returns,
            annualized_covariance_matrix,
            risk_free_rate,
            return_observation_count,
            "custom",
        )

    def backtest(
        self,
        *,
        weights: str | Mapping[str, float] | Sequence[float] = "equal_weight",
        rebalance: str = "monthly",
        transaction_cost_bps: float = 0.0,
        slippage_bps: float = 0.0,
        fixed_transaction_cost: float = 0.0,
        initial_capital: float = 1.0,
        benchmark: str | Mapping[str, float] | Sequence[float] | pd.Series | None = "equal_weight",
        lookback: int = 63,
        min_history: int = 2,
        kind: ReturnKind = "simple",
        start: str | date | None = None,
        end: str | date | None = None,
        period: str | None = "1y",
        interval: str = "1d",
        auto_adjust: bool = True,
        periods_per_year: int = 252,
        risk_free_rate: float = 0.0,
    ):
        """Backtest a deterministic rebalanced allocation for this universe.

        Parameters
        ----------
        weights : str or Mapping[str, float] or Sequence[float], default="equal_weight"
            Target allocation policy. Supported string policies include
            ``"equal_weight"``, ``"buy_and_hold"``, and
            ``"inverse_volatility"``. Mappings are normalized to universe ticker
            symbols; sequences follow universe symbol order.
        rebalance : {"none", "daily", "weekly", "monthly", "quarterly", "annual"}, default="monthly"
            Calendar rebalance schedule.
        transaction_cost_bps : float, default=0.0
            One-way transaction cost in basis points of turnover.
        slippage_bps : float, default=0.0
            Additional one-way slippage in basis points of turnover.
        fixed_transaction_cost : float, default=0.0
            Fixed cost charged whenever a non-zero rebalance occurs.
        initial_capital : float, default=1.0
            Starting portfolio value.
        benchmark : str or Mapping[str, float] or Sequence[float] or pandas.Series or None, default="equal_weight"
            Benchmark specification used for active-return diagnostics.
        lookback : int, default=63
            Historical window used by dynamic policies such as
            ``"inverse_volatility"``.
        min_history : int, default=2
            Minimum observations required before dynamic policies are estimated.
        kind : {"simple", "log"}, default="simple"
            Return convention requested from the universe history namespace.
        start, end, period, interval, auto_adjust : optional
            Historical-data request controls forwarded to
            ``universe.history.returns``.
        periods_per_year : int, default=252
            Number of return observations interpreted as one year.
        risk_free_rate : float, default=0.0
            Annualized risk-free rate in decimal units for summary metrics.

        Returns
        -------
        PortfolioBacktestResult
            Simulated equity curve, drawdowns, returns, weights, trades,
            turnover, transaction costs, benchmark diagnostics, and summaries.
        """
        self._require_two_assets()
        from abaquant.portfolio.backtesting import run_rebalanced_backtest

        aligned_return_panel = self.universe.history.returns(
            kind=kind,
            start=start,
            end=end,
            period=period,
            interval=interval,
            auto_adjust=auto_adjust,
            alignment="inner",
        ).dropna()
        if isinstance(weights, Mapping):
            normalized_weights = {
                str(key).strip().upper(): float(value) for key, value in weights.items()
            }
        else:
            normalized_weights = weights
        if isinstance(benchmark, Mapping):
            normalized_benchmark = {
                str(key).strip().upper(): float(value) for key, value in benchmark.items()
            }
        else:
            normalized_benchmark = benchmark
        return run_rebalanced_backtest(
            aligned_return_panel,
            weights=normalized_weights,
            rebalance=rebalance,
            transaction_cost_bps=transaction_cost_bps,
            slippage_bps=slippage_bps,
            fixed_transaction_cost=fixed_transaction_cost,
            initial_capital=initial_capital,
            annual_risk_free_rate=risk_free_rate,
            periods_per_year=periods_per_year,
            benchmark=normalized_benchmark,
            lookback=lookback,
            min_history=min_history,
        )

    def scenario_analysis(
        self,
        shocks: Mapping[str, float],
        *,
        weights: Mapping[str, float] | Sequence[float] | None = None,
        base_value: float = 1.0,
    ) -> PortfolioScenarioAnalysis:
        """Evaluate a one-period shock scenario for this universe.

        Parameters
        ----------
        shocks : Mapping[str, float]
            Asset-level shock returns in decimal units. Missing universe symbols
            receive a zero shock; unknown symbols are rejected.
        weights : Mapping[str, float] or Sequence[float], optional
            Portfolio weights to evaluate. Equal universe weights are used when
            omitted.
        base_value : float, default=1.0
            Starting portfolio value used to compute the ending scenario value.

        Returns
        -------
        PortfolioScenarioAnalysis
            Shock, weight, contribution, portfolio return, and ending-value
            diagnostics.
        """
        self._require_two_assets()
        normalized_shocks = {
            str(key).strip().upper(): float(value) for key, value in shocks.items()
        }
        unknown = sorted(set(normalized_shocks) - set(self.universe.symbols))
        if unknown:
            raise PortfolioValidationError(f"unknown shock symbols: {', '.join(unknown)}")
        shock_series = pd.Series(0.0, index=self.universe.symbols, dtype=float)
        for symbol, shock in normalized_shocks.items():
            shock_series.loc[symbol] = shock
        if not np.all(np.isfinite(shock_series.to_numpy(dtype=float))):
            raise PortfolioValidationError("shocks must be finite decimal returns.")
        if weights is None:
            weight_vector = np.repeat(1.0 / len(self.universe.symbols), len(self.universe.symbols))
        else:
            weight_vector = self._coerce_weights(weights)
        weight_series = pd.Series(weight_vector, index=self.universe.symbols, dtype=float)
        validated_base_value = float(base_value)
        if not np.isfinite(validated_base_value) or validated_base_value <= 0:
            raise PortfolioValidationError("base_value must be finite and positive.")
        contributions = weight_series * shock_series
        portfolio_return = float(contributions.sum())
        return PortfolioScenarioAnalysis(
            shocks=shock_series.to_dict(),
            weights=weight_series,
            contributions=contributions,
            portfolio_return=portfolio_return,
            base_value=validated_base_value,
            ending_value=float(validated_base_value * (1.0 + portfolio_return)),
        )

    def _inputs(
        self,
        *,
        kind: ReturnKind,
        start: str | date | None,
        end: str | date | None,
        period: str | None,
        interval: str,
        auto_adjust: bool,
        periods_per_year: int,
    ) -> tuple[pd.Series, pd.DataFrame, int]:
        """Estimate portfolio inputs from the universe's aligned return panel.

        Returns
        -------
        annualized_expected_returns : pandas.Series
            Arithmetic mean returns annualized by ``periods_per_year`` and
            ordered by the universe symbols.
        annualized_covariance_matrix : pandas.DataFrame
            Annualized covariance matrix with matching row and column order.
        return_observation_count : int
            Number of complete aligned return observations used for estimation.

        Raises
        ------
        InsufficientHistoryError
            If fewer than two complete aligned return rows are available.
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
        if len(aligned_return_panel) < 2:
            raise InsufficientHistoryError("At least two aligned return observations are required.")
        annualized_expected_returns = annualized_mean_returns_from_returns(
            aligned_return_panel,
            periods=periods_per_year,
        )
        annualized_covariance_matrix = annualized_covariance_from_returns(
            aligned_return_panel,
            periods=periods_per_year,
        )
        return (
            annualized_expected_returns,
            annualized_covariance_matrix,
            len(aligned_return_panel),
        )

    def _result(
        self,
        weights: np.ndarray,
        annualized_expected_returns: pd.Series,
        annualized_covariance_matrix: pd.DataFrame,
        risk_free_rate: float,
        return_observation_count: int,
        method: str,
    ) -> PortfolioResult:
        """Build a :class:`PortfolioResult` from estimated moments and weights.

        Parameters
        ----------
        weights : numpy.ndarray
            Finite asset-weight vector ordered by ``self.universe.symbols``.
        annualized_expected_returns : pandas.Series
            Annualized arithmetic mean returns in the same symbol order.
        annualized_covariance_matrix : pandas.DataFrame
            Annualized covariance matrix in the same symbol order.
        risk_free_rate : float
            Annualized arithmetic risk-free rate in decimal units.
        return_observation_count : int
            Number of complete return observations used to estimate moments.
        method : str
            Allocation method label retained in the resulting record.

        Returns
        -------
        PortfolioResult
            Immutable result containing named weights and annualized portfolio
            statistics.
        """
        validated_risk_free_rate = float(risk_free_rate)
        if not np.isfinite(validated_risk_free_rate):
            raise PortfolioValidationError("risk_free_rate must be finite.")
        portfolio_expected_return = portfolio_return(
            weights, annualized_expected_returns.to_numpy()
        )
        portfolio_annualized_volatility = portfolio_volatility(
            weights, annualized_covariance_matrix.to_numpy()
        )
        portfolio_sharpe_ratio = portfolio_sharpe(
            portfolio_expected_return,
            portfolio_annualized_volatility,
            validated_risk_free_rate,
        )
        return PortfolioResult(
            symbols=self.universe.symbols,
            weights={
                symbol: float(weight)
                for symbol, weight in zip(self.universe.symbols, weights, strict=True)
            },
            expected_return=portfolio_expected_return,
            volatility=portfolio_annualized_volatility,
            sharpe_ratio=portfolio_sharpe_ratio,
            risk_free_rate=validated_risk_free_rate,
            observations=return_observation_count,
            method=method,
        )

    def _coerce_weights(self, weights: Mapping[str, float] | Sequence[float]) -> np.ndarray:
        """Convert a user allocation to a validated universe-ordered vector.

        Parameters
        ----------
        weights : Mapping[str, float] or Sequence[float]
            Mapping keyed by universe symbol, or a vector in exact universe
            order. Values must be finite and sum to one within ``1e-8``.

        Returns
        -------
        numpy.ndarray
            One-dimensional float vector aligned to ``self.universe.symbols``.

        Raises
        ------
        PortfolioValidationError
            If symbols, dimensionality, finite values, or the full-investment
            constraint are invalid.
        """
        if isinstance(weights, Mapping):
            normalized = {str(key).strip().upper(): float(value) for key, value in weights.items()}
            required = set(self.universe.symbols)
            if set(normalized) != required:
                missing = sorted(required - set(normalized))
                extra = sorted(set(normalized) - required)
                pieces = []
                if missing:
                    pieces.append(f"missing symbols: {', '.join(missing)}")
                if extra:
                    pieces.append(f"unknown symbols: {', '.join(extra)}")
                raise PortfolioValidationError("; ".join(pieces))
            weight_vector = np.array(
                [normalized[symbol] for symbol in self.universe.symbols], dtype=float
            )
        else:
            if isinstance(weights, str):
                raise PortfolioValidationError("weights must be numeric, not a string.")
            weight_vector = np.asarray(list(weights), dtype=float)
            if len(weight_vector) != len(self.universe.symbols):
                raise PortfolioValidationError("weights length must match the universe size.")
        if weight_vector.ndim != 1 or not np.all(np.isfinite(weight_vector)):
            raise PortfolioValidationError(
                "weights must be a finite one-dimensional weight_vector."
            )
        if not np.isclose(weight_vector.sum(), 1.0, atol=1e-8):
            raise PortfolioValidationError("weights must sum to 1.")
        return weight_vector

    def _require_two_assets(self) -> None:
        """Ensure the requested optimizer has at least two assets.

        Raises
        ------
        PortfolioValidationError
            If the universe contains fewer than two symbols.
        """
        if len(self.universe.symbols) < 2:
            raise PortfolioValidationError(
                "At least two assets are required for portfolio optimization."
            )


# Backward-compatible alias for the original Phase-2 namespace class name.
MarketUniversePortfolio = UniversePortfolioAnalytics
