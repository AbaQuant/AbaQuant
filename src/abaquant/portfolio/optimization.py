"""Static portfolio allocation strategies.

Purpose
-------
The module implements a collection of fully invested allocation and optimization rules, including mean--variance, risk-parity, downside-risk, entropy, and Black--Litterman-style routines.

Conventions
-----------
Input returns are periodic simple returns. The periods argument annualizes selected statistics. Unless allow_short is true, allocations are constrained to non-negative weights that sum to one.

Scope and limitations
---------------------
Most strategies are in-sample optimizations. Solver success, covariance conditioning, and objective non-convexity may affect results.

References
----------
[ 1 ] Markowitz, H. (1952), "Portfolio Selection".
[ 2 ] Sharpe, W. F. (1966), "Mutual Fund Performance".
[ 3 ] Rockafellar, R. T., and S. Uryasev (2000), "Optimization of Conditional Value-at-Risk".
[ 4 ] Lopez de Prado, M. (2016), "Building Diversified Portfolios that Outperform Out of Sample".
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from abaquant.core import DataProvenance

from .hierarchical import hierarchical_risk_parity
from .solvers import solve_slsqp_weights

TRADING_DAYS = 252


@dataclass(frozen=True)
class PortfolioScenarioAnalysis:
    """One-period portfolio shock scenario analysis.

    Parameters
    ----------
    shocks : Mapping[str, float]
        Asset-level shock returns in decimal units, keyed by asset symbol.
    weights : pd.Series
        Portfolio weights aligned to the optimizer asset order.
    contributions : pd.Series
        Asset-level contribution to portfolio return, equal to weight times
        shock return.
    portfolio_return : float
        Total one-period shocked portfolio return.
    base_value : float
        Starting portfolio value used to compute ``ending_value``.
    ending_value : float
        Portfolio value after applying the one-period shocked return.
    """

    shocks: Mapping[str, float]
    weights: pd.Series
    contributions: pd.Series
    portfolio_return: float
    base_value: float = 1.0
    ending_value: float = 1.0
    provenance: DataProvenance | None = None

    def __post_init__(self) -> None:
        """Store defensive pandas copies for the scenario analysis."""
        object.__setattr__(self, "weights", self.weights.copy(deep=True))
        object.__setattr__(self, "contributions", self.contributions.copy(deep=True))
        object.__setattr__(self, "shocks", dict(self.shocks))
        if self.provenance is None:
            object.__setattr__(
                self,
                "provenance",
                DataProvenance(
                    provider="derived",
                    dataset="portfolio_scenario_analysis",
                    source_labels=tuple(str(label) for label in self.weights.index),
                    transformation_steps=(
                        "portfolio shock mapping",
                        "return contribution calculation",
                    ),
                    request={"base_value": self.base_value, "asset_count": len(self.weights)},
                ),
            )

    def as_frame(self) -> pd.DataFrame:
        """Return asset-level shock, weight, and contribution rows."""
        return pd.DataFrame(
            {
                "shock": pd.Series(self.shocks, dtype=float),
                "weight": self.weights,
                "contribution": self.contributions,
            }
        ).loc[self.weights.index]

    def as_dict(self) -> dict[str, object]:
        """Return a serialization-friendly portfolio scenario mapping."""
        return {
            "portfolio_return": self.portfolio_return,
            "base_value": self.base_value,
            "ending_value": self.ending_value,
            "asset_rows": self.as_frame().to_dict("index"),
            "provenance": self.provenance.as_dict(),
        }

    def scenario_analysis(
        self,
        shocks: Mapping[str, float],
        *,
        weights: Sequence[float] | pd.Series | Mapping[str, float] | None = None,
        base_value: float = 1.0,
    ) -> PortfolioScenarioAnalysis:
        """Evaluate a one-period asset-shock scenario for a portfolio.

        Parameters
        ----------
        shocks : Mapping[str, float]
            Asset-level shock returns in decimal units, keyed by asset symbol.
            Missing symbols receive a zero shock; unknown symbols are rejected.
        weights : sequence, pandas.Series, mapping, optional
            Allocation to evaluate. Equal weights are used when omitted.
        base_value : float, default=1.0
            Starting portfolio value used to compute the ending value.

        Returns
        -------
        PortfolioScenarioAnalysis
            Asset-level shocks, weights, return contributions, total portfolio
            return, and ending value.
        """
        symbols = list(self.context.asset_symbols)
        normalized_shocks = {str(key): float(value) for key, value in shocks.items()}
        unknown = sorted(set(normalized_shocks) - set(symbols))
        if unknown:
            raise ValueError(f"Unknown shock symbols: {', '.join(unknown)}.")
        shock_series = pd.Series(0.0, index=symbols, dtype=float)
        for symbol, value in normalized_shocks.items():
            shock_series.loc[symbol] = value
        if not np.all(np.isfinite(shock_series.to_numpy(dtype=float))):
            raise ValueError("shocks must be finite decimal returns.")
        if weights is None:
            weight_series = pd.Series(1.0 / len(symbols), index=symbols, dtype=float)
        elif isinstance(weights, pd.Series):
            weight_series = weights.reindex(symbols).astype(float)
        elif isinstance(weights, Mapping):
            normalized_weights = {str(key): float(value) for key, value in weights.items()}
            if set(normalized_weights) != set(symbols):
                raise ValueError("weight mapping must contain exactly the allocator assets.")
            weight_series = pd.Series(normalized_weights, dtype=float).reindex(symbols)
        else:
            weight_array = np.asarray(list(weights), dtype=float)
            if weight_array.shape != (len(symbols),):
                raise ValueError("weights must contain one value per asset.")
            weight_series = pd.Series(weight_array, index=symbols, dtype=float)
        if not np.all(np.isfinite(weight_series.to_numpy(dtype=float))):
            raise ValueError("weights must be finite.")
        if not np.isclose(float(weight_series.sum()), 1.0, atol=1e-8):
            raise ValueError("weights must sum to one.")
        validated_base_value = float(base_value)
        if not np.isfinite(validated_base_value) or validated_base_value <= 0:
            raise ValueError("base_value must be finite and positive.")
        contributions = weight_series * shock_series
        portfolio_return = float(contributions.sum())
        return PortfolioScenarioAnalysis(
            shocks=shock_series.to_dict(),
            weights=weight_series,
            contributions=contributions,
            portfolio_return=portfolio_return,
            base_value=validated_base_value,
            ending_value=float(validated_base_value * (1.0 + portfolio_return)),
            provenance=DataProvenance(
                provider="derived",
                dataset="portfolio_scenario_analysis",
                source_labels=tuple(symbols),
                transformation_steps=("portfolio shock mapping", "return contribution calculation"),
                request={
                    "base_value": validated_base_value,
                    "shock_symbols": tuple(sorted(normalized_shocks)),
                    "portfolio_input_provenance": self.context.provenance.as_dict(),
                },
            ),
        )

    def backtest(
        self,
        *,
        weights: str | Sequence[float] | pd.Series | Mapping[str, float] = "equal_weight",
        rebalance: str = "monthly",
        transaction_cost_bps: float = 0.0,
        slippage_bps: float = 0.0,
        fixed_transaction_cost: float = 0.0,
        initial_capital: float = 1.0,
        benchmark: str | Sequence[float] | pd.Series | Mapping[str, float] | None = "equal_weight",
        lookback: int = 63,
        min_history: int = 2,
    ):
        """Run a deterministic periodically rebalanced portfolio backtest.

        Parameters
        ----------
        weights : str or sequence or pandas.Series or mapping, default="equal_weight"
            Target allocation policy. Supported string policies include
            ``"equal_weight"``, ``"buy_and_hold"``, and
            ``"inverse_volatility"``. Mappings are keyed by asset symbol;
            sequences are interpreted in optimizer asset order.
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
        benchmark : str or sequence or pandas.Series or mapping or None, default="equal_weight"
            Benchmark used for active-return diagnostics. A pandas Series is
            interpreted as precomputed benchmark returns.
        lookback : int, default=63
            Historical window used by dynamic policies such as
            ``"inverse_volatility"``.
        min_history : int, default=2
            Minimum observations required before dynamic policy estimates are
            used.

        Returns
        -------
        PortfolioBacktestResult
            Simulated equity curve, drawdowns, returns, weights, trades,
            turnover, transaction costs, benchmark diagnostics, and summaries.
        """
        from abaquant.portfolio.backtesting import run_rebalanced_backtest

        return run_rebalanced_backtest(
            self.context.periodic_returns,
            weights=weights,
            rebalance=rebalance,
            transaction_cost_bps=transaction_cost_bps,
            slippage_bps=slippage_bps,
            fixed_transaction_cost=fixed_transaction_cost,
            initial_capital=initial_capital,
            annual_risk_free_rate=self.context.annual_risk_free_rate,
            periods_per_year=self.context.periods_per_year,
            benchmark=benchmark,
            lookback=lookback,
            min_history=min_history,
            allow_short=self.context.allow_short_positions,
        )

    def visualize(
        self,
        *,
        chart: str = "contributions",
        backend: str | None = None,
        theme=None,
        save_path: str | Path | None = None,
        filename: str | None = None,
    ):
        """Return a figure for this portfolio scenario analysis.

        Parameters
        ----------
        chart : {"contributions", "shocks", "waterfall"}, default="contributions"
            Scenario diagnostic to visualize.
        backend : {"matplotlib", "plotly"}, optional
            Figure backend override.
        theme : VisualizationTheme, optional
            Per-call style override.
        save_path : str or pathlib.Path, optional
            Explicit export path.
        filename : str, optional
            Filename relative to the active theme's save directory.
        """
        from abaquant.visualization import visualize_portfolio_scenario

        return visualize_portfolio_scenario(
            self,
            chart=chart,
            backend=backend,
            theme=theme,
            save_path=save_path,
            filename=filename,
        )


class PortfolioComputation:
    """Static in-sample allocation model for a panel of periodic asset returns.

    Parameters
    ----------
    periodic_returns : pandas.DataFrame
        Periodic simple returns with observations in rows and assets in columns.
    annual_risk_free_rate : float, default=0.0
        Annual risk-free rate in decimal units used by excess-return objectives.
    allow_short_positions : bool, default=False
        Whether allocation optimizers may use negative asset weights.
    periods_per_year : int, default=252
        Number of periodic observations used to annualize return and covariance
        estimates.

    Attributes
    ----------
    periodic_returns : pandas.DataFrame
        Complete-case periodic return observations used by the optimizer.
    asset_symbols : list[str]
        Asset labels in optimizer-vector order.
    annualized_mean_returns : pandas.Series
        Arithmetic mean periodic returns multiplied by ``periods_per_year``.
    annualized_covariance_matrix : pandas.DataFrame
        Sample covariance matrix multiplied by ``periods_per_year``.
    """

    def __init__(
        self,
        periodic_returns: pd.DataFrame,
        annual_risk_free_rate: float = 0.0,
        allow_short_positions: bool = False,
        periods_per_year: int = TRADING_DAYS,
    ):
        """Initialize a static portfolio optimizer from periodic return observations.

        Parameters
        ----------
        periodic_returns : pandas.DataFrame
            Periodic simple returns with observations in rows and assets in columns.
        annual_risk_free_rate : float, default=0.0
            Annual risk-free rate in decimal units used by excess-return objectives.
        allow_short_positions : bool, default=False
            Whether allocation optimizers may use negative asset weights.
        periods_per_year : int, default=252
            Number of periodic observations used to annualize return and covariance
            estimates.
        """
        self.periodic_returns = periodic_returns.dropna()
        self.asset_symbols = list(self.periodic_returns.columns)
        self.asset_count = len(self.asset_symbols)
        self.annual_risk_free_rate = annual_risk_free_rate
        self.periods_per_year = periods_per_year
        self.allow_short_positions = allow_short_positions

        self.annualized_mean_returns = self.periodic_returns.mean() * periods_per_year
        self.annualized_covariance_matrix = self.periodic_returns.cov() * periods_per_year
        self.correlation_matrix = self.periodic_returns.corr()
        self.provenance = DataProvenance(
            provider="manual",
            dataset="portfolio_optimization_inputs",
            source_labels=tuple(self.asset_symbols),
            reporting_date=(
                self.periodic_returns.index[-1].date().isoformat()
                if len(self.periodic_returns.index)
                and hasattr(self.periodic_returns.index[-1], "date")
                else None
            ),
            transformation_steps=(
                "periodic return panel validation",
                "annualized moments calculation",
                "correlation matrix calculation",
            ),
            request={
                "observations": len(self.periodic_returns),
                "assets": tuple(self.asset_symbols),
                "annual_risk_free_rate": annual_risk_free_rate,
                "periods_per_year": periods_per_year,
                "allow_short_positions": allow_short_positions,
            },
        )

        if allow_short_positions:
            self.minimum_weight, self.maximum_weight = -1.0, 1.0
        else:
            self.minimum_weight, self.maximum_weight = 0.0, 1.0

    # ------------------------------------------------------------------
    # Internal optimization utilities
    # ------------------------------------------------------------------
    def _minimize(self, objective, bounds=None, constraints=None, x0=None) -> np.ndarray:
        """Solve a constrained portfolio-weight objective with the configured bounds.

        Parameters
        ----------
        objective : float or array-like
            Objective function passed to the numerical optimizer.
        bounds : object or None, default=None
            Allocation bounds in the format accepted by the underlying optimizer.
        constraints : object or None, default=None
            Constraint specification passed to the numerical optimizer.
        x0 : object or None, default=None
            Optional initial point for numerical optimization.

        Returns
        -------
        np.ndarray
            Result of the  minimize calculation.
        """
        return solve_slsqp_weights(
            objective,
            self.asset_count,
            self.minimum_weight,
            self.maximum_weight,
            bounds=bounds,
            constraints=constraints,
            x0=x0,
        )

    # ------------------------------------------------------------------
    # 1. Equal Weight
    # ------------------------------------------------------------------
    def equal_weight(self) -> np.ndarray:
        """Construct or evaluate an equally weighted fully invested portfolio.

        Returns
        -------
        numpy.ndarray
            Numeric array ordered consistently with the supplied strikes, time grid, assets, or state labels.
        """
        return np.repeat(1.0 / self.asset_count, self.asset_count)

    # ------------------------------------------------------------------
    # 2. Maximum Sharpe
    # ------------------------------------------------------------------
    def max_sharpe(self) -> np.ndarray:
        """Construct a bounded maximum-Sharpe-ratio portfolio.

        Returns
        -------
        np.ndarray
            Result of the max sharpe calculation.

        Notes
        -----
        This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
        """
        mu, cov = self.annualized_mean_returns.values, self.annualized_covariance_matrix.values

        def neg_sharpe(w):
            """Compute the result defined by ``neg_sharpe`` under this module's documented convention.

            Parameters
            ----------
            w : float or array-like
                Numeric portfolio-weight vector in the established asset order.

            Returns
            -------
            object
                Result of the neg sharpe workflow.

            Notes
            -----
            This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
            """
            ret = w @ mu
            vol = np.sqrt(max(w @ cov @ w, 1e-12))
            return -(ret - self.annual_risk_free_rate) / vol

        return self._minimize(neg_sharpe)

    # ------------------------------------------------------------------
    # 3. Minimum Variance
    # ------------------------------------------------------------------
    def min_variance(self) -> np.ndarray:
        """Compute the result defined by ``min_variance`` under this module's documented convention.

        Returns
        -------
        np.ndarray
            Result of the min variance calculation.

        Notes
        -----
        This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
        """
        cov = self.annualized_covariance_matrix.values
        return self._minimize(lambda w: w @ cov @ w)

    # ------------------------------------------------------------------
    # 4. Risk Parity (ERC)
    # ------------------------------------------------------------------
    def risk_parity(self) -> np.ndarray:
        """Compute an equal-risk-contribution portfolio allocation.

        Returns
        -------
        np.ndarray
            Result of the risk parity calculation.

        Notes
        -----
        This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
        """
        cov = self.annualized_covariance_matrix.values
        target = 1.0 / self.asset_count

        def erc_objective(w):
            """Compute the result defined by ``erc_objective`` under this module's documented convention.

            Parameters
            ----------
            w : float or array-like
                Numeric portfolio-weight vector in the established asset order.

            Returns
            -------
            object
                Result of the erc objective workflow.
            """
            port_var = w @ cov @ w
            if port_var <= 1e-12:
                return 1e6
            contrib = w * (cov @ w) / port_var
            return np.sum((contrib - target) ** 2)

        bounds = tuple((1e-4, 1.0) for _ in range(self.asset_count))
        return self._minimize(erc_objective, bounds=bounds)

    # ------------------------------------------------------------------
    # 5. Inverse Volatility
    # ------------------------------------------------------------------
    def inverse_volatility(self) -> np.ndarray:
        """Compute weights inversely proportional to asset volatility.

        Returns
        -------
        np.ndarray
            Result of the inverse volatility calculation.
        """
        vol = np.sqrt(np.diag(self.annualized_covariance_matrix.values))
        vol = np.where(vol == 0, 1e-8, vol)
        inv = 1.0 / vol
        return inv / inv.sum()

    # ------------------------------------------------------------------
    # 6. Inverse Variance
    # ------------------------------------------------------------------
    def inverse_variance(self) -> np.ndarray:
        """Compute weights inversely proportional to asset variance.

        Returns
        -------
        np.ndarray
            Result of the inverse variance calculation.

        Notes
        -----
        This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
        """
        var = np.diag(self.annualized_covariance_matrix.values)
        var = np.where(var == 0, 1e-8, var)
        inv = 1.0 / var
        return inv / inv.sum()

    # ------------------------------------------------------------------
    # 7. Maximum Diversification
    # ------------------------------------------------------------------
    def max_diversification(self) -> np.ndarray:
        """Optimize the diversification ratio under the configured constraints.

        Returns
        -------
        np.ndarray
            Result of the max diversification calculation.
        """
        sigma = np.sqrt(np.diag(self.annualized_covariance_matrix.values))
        cov = self.annualized_covariance_matrix.values

        def neg_div(w):
            """Compute the result defined by ``neg_div`` under this module's documented convention.

            Parameters
            ----------
            w : float or array-like
                Numeric portfolio-weight vector in the established asset order.

            Returns
            -------
            object
                Result of the neg div workflow.
            """
            port_vol = np.sqrt(max(w @ cov @ w, 1e-12))
            return -(w @ sigma) / port_vol

        return self._minimize(neg_div)

    # ------------------------------------------------------------------
    # 8. Minimum CVaR
    # ------------------------------------------------------------------
    def min_cvar(self, alpha: float = 0.05) -> np.ndarray:
        """Optimize a portfolio for minimum historical conditional value at risk.

        Parameters
        ----------
        alpha : float, default=0.05
            Model-specific alpha parameter; consult the module convention.

        Returns
        -------
        np.ndarray
            Result of the min cvar calculation.
        """
        R = self.periodic_returns.values

        def cvar_obj(w):
            """Compute the result defined by ``cvar_obj`` under this module's documented convention.

            Parameters
            ----------
            w : float or array-like
                Numeric portfolio-weight vector in the established asset order.

            Returns
            -------
            object
                Result of the cvar obj workflow.
            """
            pr = R @ w
            var = np.quantile(pr, alpha)
            tail = pr[pr <= var]
            return -tail.mean() if len(tail) > 0 else -var

        return self._minimize(cvar_obj)

    # ------------------------------------------------------------------
    # 9. Maximum Sortino
    # ------------------------------------------------------------------
    def max_sortino(self) -> np.ndarray:
        """Optimize a portfolio for maximum Sortino ratio.

        Returns
        -------
        np.ndarray
            Result of the max sortino calculation.
        """
        R = self.periodic_returns.values
        rf_d = (1 + self.annual_risk_free_rate) ** (1 / self.periods_per_year) - 1

        def neg_sortino(w):
            """Compute the result defined by ``neg_sortino`` under this module's documented convention.

            Parameters
            ----------
            w : float or array-like
                Numeric portfolio-weight vector in the established asset order.

            Returns
            -------
            object
                Result of the neg sortino workflow.
            """
            pr = R @ w
            downside = pr[pr < rf_d] - rf_d
            dd = (
                max(np.sqrt(np.mean(downside**2)) * np.sqrt(self.periods_per_year), 1e-8)
                if len(downside) > 0
                else 1e-8
            )
            return -(pr.mean() * self.periods_per_year - self.annual_risk_free_rate) / dd

        return self._minimize(neg_sortino)

    # ------------------------------------------------------------------
    # 10. Maximum Calmar
    # ------------------------------------------------------------------
    def max_calmar(self) -> np.ndarray:
        """Optimize a portfolio for maximum Calmar ratio.

        Returns
        -------
        np.ndarray
            Result of the max calmar calculation.
        """
        R = self.periodic_returns.values

        def neg_calmar(w):
            """Compute the result defined by ``neg_calmar`` under this module's documented convention.

            Parameters
            ----------
            w : float or array-like
                Numeric portfolio-weight vector in the established asset order.

            Returns
            -------
            object
                Result of the neg calmar workflow.
            """
            pr = R @ w
            cum = np.cumprod(1 + pr)
            mdd = abs(((cum - np.maximum.accumulate(cum)) / np.maximum.accumulate(cum)).min())
            mdd = max(mdd, 1e-8)
            return -(pr.mean() * self.periods_per_year) / mdd

        return self._minimize(neg_calmar)

    # ------------------------------------------------------------------
    # 11. Hierarchical Risk Parity (HRP)
    # ------------------------------------------------------------------
    def hrp(self) -> np.ndarray:
        """Compute Hierarchical Risk Parity weights from the optimizer return data.

        Returns
        -------
        np.ndarray
            Result of the hrp calculation.
        """
        return hierarchical_risk_parity(
            self.annualized_covariance_matrix, self.correlation_matrix, self.asset_symbols
        )

    # ------------------------------------------------------------------
    # 12. Maxima Decorrelacion
    # ------------------------------------------------------------------
    def max_decorrelation(self) -> np.ndarray:
        """Optimize an allocation that minimizes average portfolio correlation.

        Returns
        -------
        np.ndarray
            Result of the max decorrelation calculation.
        """
        corr = self.correlation_matrix.values
        return self._minimize(lambda w: w @ corr @ w)

    # ------------------------------------------------------------------
    # 13. Minimum CDaR
    # ------------------------------------------------------------------
    def min_cdar(self, alpha: float = 0.05) -> np.ndarray:
        """Optimize a portfolio for minimum conditional drawdown at risk.

        Parameters
        ----------
        alpha : float, default=0.05
            Model-specific alpha parameter; consult the module convention.

        Returns
        -------
        np.ndarray
            Result of the min cdar calculation.
        """
        R = self.periodic_returns.values

        def cdar_obj(w):
            """Compute the result defined by ``cdar_obj`` under this module's documented convention.

            Parameters
            ----------
            w : float or array-like
                Numeric portfolio-weight vector in the established asset order.

            Returns
            -------
            object
                Result of the cdar obj workflow.
            """
            cum = np.cumprod(1 + R @ w)
            losses = -((cum - np.maximum.accumulate(cum)) / np.maximum.accumulate(cum))
            var_dd = np.quantile(losses, 1 - alpha)
            tail = losses[losses >= var_dd]
            return tail.mean() if len(tail) > 0 else var_dd

        return self._minimize(cdar_obj)

    # ------------------------------------------------------------------
    # 14. Target Volatility (10%)
    # ------------------------------------------------------------------
    def target_volatility(self, target_vol: float = 0.10) -> np.ndarray:
        """Find an allocation whose volatility is close to the requested target.

        Parameters
        ----------
        target_vol : float, default=0.1
            Target annualized portfolio volatility in decimal units.

        Returns
        -------
        np.ndarray
            Result of the target volatility calculation.
        """
        mu, cov = self.annualized_mean_returns.values, self.annualized_covariance_matrix.values
        constraints = (
            {"type": "eq", "fun": lambda w: np.sum(w) - 1},
            {"type": "ineq", "fun": lambda w: target_vol - np.sqrt(max(w @ cov @ w, 0))},
        )
        w = self._minimize(lambda w: -(w @ mu), constraints=constraints)
        if np.sqrt(w @ cov @ w) > target_vol * 1.5:
            return self.min_variance()
        return w

    # ------------------------------------------------------------------
    # 15. Maximum Return (long-only, without a risk constraint)
    # ------------------------------------------------------------------
    def max_return(self) -> np.ndarray:
        """Maximize estimated portfolio return under configured constraints.

        Returns
        -------
        np.ndarray
            Result of the max return calculation.
        """
        mu = self.annualized_mean_returns.values

        # Pure concentration in the asset with the highest expected return
        # suavizada con regularizacion L2 para evitar solucion degenerada
        def neg_ret_reg(w):
            """Compute the result defined by ``neg_ret_reg`` under this module's documented convention.

            Parameters
            ----------
            w : float or array-like
                Numeric portfolio-weight vector in the established asset order.

            Returns
            -------
            object
                Result of the neg ret reg workflow.
            """
            return -(w @ mu) + 0.01 * np.sum(w**2)

        return self._minimize(neg_ret_reg)

    # ------------------------------------------------------------------
    # 16. Minimum Negative Skewness (maximizes positive asymmetry)
    # ------------------------------------------------------------------
    def min_neg_skewness(self) -> np.ndarray:
        """Optimize a portfolio to reduce negative skewness exposure.

        Returns
        -------
        np.ndarray
            Result of the min neg skewness calculation.
        """
        R = self.periodic_returns.values

        def neg_skew_obj(w):
            """Compute the result defined by ``neg_skew_obj`` under this module's documented convention.

            Parameters
            ----------
            w : float or array-like
                Numeric portfolio-weight vector in the established asset order.

            Returns
            -------
            object
                Result of the neg skew obj workflow.
            """
            pr = R @ w
            std = pr.std()
            if std < 1e-10:
                return 0.0
            return -float(((pr - pr.mean()) ** 3).mean() / std**3)

        return self._minimize(neg_skew_obj)

    # ------------------------------------------------------------------
    # 17. Kelly fraction
    # ------------------------------------------------------------------
    def kelly_fraction(self) -> np.ndarray:
        """Optimize the implemented expected-log-growth Kelly criterion.

        Returns
        -------
        np.ndarray
            Result of the kelly fraction calculation.
        """
        R = self.periodic_returns.values

        def neg_log_growth(w):
            """Compute the result defined by ``neg_log_growth`` under this module's documented convention.

            Parameters
            ----------
            w : float or array-like
                Numeric portfolio-weight vector in the established asset order.

            Returns
            -------
            object
                Result of the neg log growth workflow.
            """
            pr = R @ w
            if np.any(pr <= -1):
                return 1e8
            return -np.mean(np.log1p(pr))

        return self._minimize(neg_log_growth)

    # ------------------------------------------------------------------
    # 18. Black--Litterman equilibrium prior without active investor views.
    # ------------------------------------------------------------------
    def black_litterman(self) -> np.ndarray:
        """Compute the implemented equilibrium-prior Black--Litterman allocation without investor views.

        Returns
        -------
        np.ndarray
            Result of the black litterman calculation.
        """
        cov = self.annualized_covariance_matrix.values
        # Approximate market weights; equal weight is used as the available proxy.
        w_mkt = np.repeat(1.0 / self.asset_count, self.asset_count)
        # Market-implied risk-aversion coefficient used by the implementation.
        mkt_ret = float(w_mkt @ self.annualized_mean_returns.values)
        mkt_vol = float(np.sqrt(w_mkt @ cov @ w_mkt))
        lam = (mkt_ret - self.annual_risk_free_rate) / (mkt_vol**2) if mkt_vol > 0 else 3.0
        lam = np.clip(lam, 0.5, 10.0)
        # Equilibrium returns (Pi)
        pi = lam * cov @ w_mkt
        # Sin views: mu_BL = pi
        mu_bl = pi

        # Optimizacion con mu_BL
        def neg_sharpe_bl(w):
            """Compute the result defined by ``neg_sharpe_bl`` under this module's documented convention.

            Parameters
            ----------
            w : float or array-like
                Numeric portfolio-weight vector in the established asset order.

            Returns
            -------
            object
                Result of the neg sharpe bl workflow.

            Notes
            -----
            This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
            """
            ret = w @ mu_bl
            vol = np.sqrt(max(w @ cov @ w, 1e-12))
            return -(ret - self.annual_risk_free_rate) / vol

        return self._minimize(neg_sharpe_bl)

    # ------------------------------------------------------------------
    # 19. Minimum tail kurtosis: minimize portfolio tail kurtosis.
    # ------------------------------------------------------------------
    def min_tail_kurtosis(self) -> np.ndarray:
        """Optimize a portfolio to reduce downside-tail kurtosis.

        Returns
        -------
        np.ndarray
            Result of the min tail kurtosis calculation.
        """
        R = self.periodic_returns.values

        def kurtosis_obj(w):
            """Compute the result defined by ``kurtosis_obj`` under this module's documented convention.

            Parameters
            ----------
            w : float or array-like
                Numeric portfolio-weight vector in the established asset order.

            Returns
            -------
            float
                Computed kurtosis obj in the units implied by the documented inputs.
            """
            pr = R @ w
            std = pr.std()
            if std < 1e-10:
                return 0.0
            return float(((pr - pr.mean()) ** 4).mean() / std**4)

        return self._minimize(kurtosis_obj)

    # ------------------------------------------------------------------
    # 20. Maximum Omega ratio with the daily risk-free rate as threshold.
    # ------------------------------------------------------------------
    def max_omega(self, threshold: float | None = None) -> np.ndarray:
        """Optimize the Omega ratio relative to the supplied periodic threshold.

        Parameters
        ----------
        threshold : float | None, default=None
            Periodic return threshold used by the Omega-ratio objective.

        Returns
        -------
        np.ndarray
            Result of the max omega calculation.
        """
        R = self.periodic_returns.values
        thr = (
            threshold
            if threshold is not None
            else (1 + self.annual_risk_free_rate) ** (1 / self.periods_per_year) - 1
        )

        def neg_omega(w):
            """Compute the result defined by ``neg_omega`` under this module's documented convention.

            Parameters
            ----------
            w : float or array-like
                Numeric portfolio-weight vector in the established asset order.

            Returns
            -------
            object
                Result of the neg omega workflow.
            """
            pr = R @ w
            excess = pr - thr
            gains = excess[excess > 0].sum()
            losses = -excess[excess < 0].sum()
            if losses < 1e-10:
                return -1e6 if gains > 0 else 0.0
            return -(gains / losses)

        return self._minimize(neg_omega)

    # ------------------------------------------------------------------
    # 21. Maximum Weight Entropy (Shannon-entropy diversification)
    # ------------------------------------------------------------------
    def max_entropy(self) -> np.ndarray:
        """Optimize diversified weights using the implemented entropy--variance objective.

        Returns
        -------
        np.ndarray
            Result of the max entropy calculation.
        """
        cov = self.annualized_covariance_matrix.values
        eps = 1e-10

        def neg_entropy_obj(w):
            """Compute the result defined by ``neg_entropy_obj`` under this module's documented convention.

            Parameters
            ----------
            w : float or array-like
                Numeric portfolio-weight vector in the established asset order.

            Returns
            -------
            object
                Result of the neg entropy obj workflow.
            """
            w_pos = np.clip(w, eps, None)
            w_pos = w_pos / w_pos.sum()
            entropy = -np.sum(w_pos * np.log(w_pos))
            port_var = w @ cov @ w
            # Smooth risk penalty and entropy reward
            return -entropy + 2.0 * port_var

        return self._minimize(neg_entropy_obj)

    # ------------------------------------------------------------------
    # Dispatcher
    # ------------------------------------------------------------------
    def optimize(self, strategy: str, **kwargs) -> np.ndarray:
        """Run the named portfolio-allocation strategy.

        Parameters
        ----------
        strategy : str
            Name of the portfolio-allocation strategy to execute.
        kwargs : float or array-like
            Additional keyword arguments forwarded to the selected strategy.

        Returns
        -------
        np.ndarray
            Result of the optimize calculation.

        Notes
        -----
        This is an analytical in-sample calculation. It does not by itself model transaction costs, execution effects, taxes, or future return uncertainty.
        """
        strategies = self.available_strategies()
        if strategy not in strategies:
            raise ValueError(f"Estrategia desconocida: {strategy}")
        return strategies[strategy](**kwargs) if kwargs else strategies[strategy]()

    def available_strategies(self) -> dict:
        """Return the allocation strategy names accepted by optimize.

        Returns
        -------
        list[str]
            Available labels in the order supplied by the provider or defined by the implementation.
        """
        return {
            "Equal Weight (1/N)": self.equal_weight,
            "Maximum Sharpe": self.max_sharpe,
            "Minimum Variance": self.min_variance,
            "Risk Parity (ERC)": self.risk_parity,
            "Inverse Volatility": self.inverse_volatility,
            "Inverse Variance": self.inverse_variance,
            "Maximum Diversification": self.max_diversification,
            "Minimum CVaR": self.min_cvar,
            "Maximum Sortino": self.max_sortino,
            "Maximum Calmar": self.max_calmar,
            "Hierarchical Risk Parity (HRP)": self.hrp,
            "Maximum Decorrelation": self.max_decorrelation,
            "Minimum CDaR": self.min_cdar,
            "Target Volatility (10%)": self.target_volatility,
            "Maximum Return": self.max_return,
            "Minimum Negative Skewness": self.min_neg_skewness,
            "Kelly Fraction": self.kelly_fraction,
            "Black-Litterman (equilibrium)": self.black_litterman,
            "Minimum Tail Kurtosis": self.min_tail_kurtosis,
            "Maximum Omega Ratio": self.max_omega,
            "Maximum Entropy": self.max_entropy,
        }

    def weights_to_series(self, w: np.ndarray) -> pd.Series:
        """Return a weight vector indexed by the optimizer asset labels.

        Parameters
        ----------
        w : np.ndarray
            Numeric portfolio-weight vector in the established asset order.

        Returns
        -------
        pandas.Series
            Portfolio weights indexed by the optimizer asset labels.
        """
        return pd.Series(w, index=self.asset_symbols)


STRATEGY_NAMES = [
    "Equal Weight (1/N)",
    "Maximum Sharpe",
    "Minimum Variance",
    "Risk Parity (ERC)",
    "Inverse Volatility",
    "Inverse Variance",
    "Maximum Diversification",
    "Minimum CVaR",
    "Maximum Sortino",
    "Maximum Calmar",
    "Hierarchical Risk Parity (HRP)",
    "Maximum Decorrelation",
    "Minimum CDaR",
    "Target Volatility (10%)",
    "Maximum Return",
    "Minimum Negative Skewness",
    "Kelly Fraction",
    "Black-Litterman (equilibrium)",
    "Minimum Tail Kurtosis",
    "Maximum Omega Ratio",
    "Maximum Entropy",
]


class PortfolioEstimationContext(PortfolioComputation):
    """Validated in-sample returns, moments, and constraints for allocation methods."""


class _AllocationFamily:
    """Base class exposing one immutable estimation context to a strategy family."""

    def __init__(self, context: PortfolioEstimationContext) -> None:
        self.context = context


class MeanVarianceAllocator(_AllocationFamily):
    """Mean--variance and full-investment allocation methods."""

    def equal_weight(self) -> np.ndarray:
        """Return equal fully invested asset weights."""
        return self.context.equal_weight()

    def maximum_sharpe(self) -> np.ndarray:
        """Return the in-sample maximum-Sharpe allocation."""
        return self.context.max_sharpe()

    def minimum_variance(self) -> np.ndarray:
        """Return the constrained global minimum-variance allocation."""
        return self.context.min_variance()

    def maximum_return(self) -> np.ndarray:
        """Return the constrained maximum-return allocation."""
        return self.context.max_return()


class RiskBasedAllocator(_AllocationFamily):
    """Risk-budget, diversification, hierarchy, and concentration allocation methods."""

    def risk_parity(self) -> np.ndarray:
        """Return equal-risk-contribution weights."""
        return self.context.risk_parity()

    def inverse_volatility(self) -> np.ndarray:
        """Return weights inversely proportional to asset volatility."""
        return self.context.inverse_volatility()

    def inverse_variance(self) -> np.ndarray:
        """Return weights inversely proportional to asset variance."""
        return self.context.inverse_variance()

    def maximum_diversification(self) -> np.ndarray:
        """Return the maximum-diversification allocation."""
        return self.context.max_diversification()

    def maximum_decorrelation(self) -> np.ndarray:
        """Return the maximum-decorrelation allocation."""
        return self.context.max_decorrelation()

    def hierarchical_risk_parity(self) -> np.ndarray:
        """Return hierarchical risk-parity weights."""
        return self.context.hrp()

    def maximum_entropy(self) -> np.ndarray:
        """Return the maximum-entropy allocation."""
        return self.context.max_entropy()


class DownsideRiskAllocator(_AllocationFamily):
    """Tail-loss and downside-performance allocation methods."""

    def minimum_cvar(self, alpha: float = 0.05) -> np.ndarray:
        """Return the allocation minimizing conditional value at risk."""
        return self.context.min_cvar(alpha)

    def minimum_cdar(self, alpha: float = 0.05) -> np.ndarray:
        """Return the allocation minimizing conditional drawdown at risk."""
        return self.context.min_cdar(alpha)

    def maximum_sortino(self) -> np.ndarray:
        """Return the in-sample maximum-Sortino allocation."""
        return self.context.max_sortino()

    def maximum_calmar(self) -> np.ndarray:
        """Return the in-sample maximum-Calmar allocation."""
        return self.context.max_calmar()

    def minimum_tail_kurtosis(self) -> np.ndarray:
        """Return the allocation minimizing tail kurtosis."""
        return self.context.min_tail_kurtosis()

    def maximum_omega(self, threshold: float | None = None) -> np.ndarray:
        """Return the allocation maximizing the Omega ratio."""
        return self.context.max_omega(threshold)


class PortfolioAllocator:
    """Facade that composes specialized static portfolio allocation families.

    Public allocation methods are intentionally namespaced: ``mean_variance``,
    ``risk_based``, and ``downside_risk``. This prevents one class from
    accumulating unrelated optimization responsibilities.
    """

    def __init__(
        self,
        periodic_returns: pd.DataFrame,
        annual_risk_free_rate: float = 0.0,
        allow_short_positions: bool = False,
        periods_per_year: int = TRADING_DAYS,
    ) -> None:
        self.context = PortfolioEstimationContext(
            periodic_returns, annual_risk_free_rate, allow_short_positions, periods_per_year
        )
        self.mean_variance = MeanVarianceAllocator(self.context)
        self.risk_based = RiskBasedAllocator(self.context)
        self.downside_risk = DownsideRiskAllocator(self.context)

    def allocate(self, family: str, method: str, **kwargs) -> np.ndarray:
        """Run one explicitly selected allocation-family method."""
        families = {
            "mean_variance": self.mean_variance,
            "risk_based": self.risk_based,
            "downside_risk": self.downside_risk,
        }
        if family not in families:
            raise ValueError(f"Unknown allocation family: {family!r}.")
        callable_method = getattr(families[family], method, None)
        if callable_method is None or not callable(callable_method):
            raise ValueError(f"Unknown method {method!r} for {family!r}.")
        return callable_method(**kwargs)

    def weights_to_series(self, weights: np.ndarray) -> pd.Series:
        """Index an allocation vector by the context asset order."""
        return self.context.weights_to_series(weights)

    def scenario_analysis(
        self,
        shocks: Mapping[str, float],
        *,
        weights: Sequence[float] | pd.Series | Mapping[str, float] | None = None,
        base_value: float = 1.0,
    ) -> PortfolioScenarioAnalysis:
        """Evaluate a one-period asset-shock scenario for a portfolio.

        Parameters
        ----------
        shocks : Mapping[str, float]
            Asset-level shock returns in decimal units, keyed by asset symbol.
            Missing symbols receive a zero shock; unknown symbols are rejected.
        weights : sequence, pandas.Series, mapping, optional
            Allocation to evaluate. Equal weights are used when omitted.
        base_value : float, default=1.0
            Starting portfolio value used to compute the ending value.

        Returns
        -------
        PortfolioScenarioAnalysis
            Asset-level shocks, weights, return contributions, total portfolio
            return, and ending value.
        """
        symbols = list(self.context.asset_symbols)
        normalized_shocks = {str(key): float(value) for key, value in shocks.items()}
        unknown = sorted(set(normalized_shocks) - set(symbols))
        if unknown:
            raise ValueError(f"Unknown shock symbols: {', '.join(unknown)}.")
        shock_series = pd.Series(0.0, index=symbols, dtype=float)
        for symbol, value in normalized_shocks.items():
            shock_series.loc[symbol] = value
        if not np.all(np.isfinite(shock_series.to_numpy(dtype=float))):
            raise ValueError("shocks must be finite decimal returns.")
        if weights is None:
            weight_series = pd.Series(1.0 / len(symbols), index=symbols, dtype=float)
        elif isinstance(weights, pd.Series):
            weight_series = weights.reindex(symbols).astype(float)
        elif isinstance(weights, Mapping):
            normalized_weights = {str(key): float(value) for key, value in weights.items()}
            if set(normalized_weights) != set(symbols):
                raise ValueError("weight mapping must contain exactly the allocator assets.")
            weight_series = pd.Series(normalized_weights, dtype=float).reindex(symbols)
        else:
            weight_array = np.asarray(list(weights), dtype=float)
            if weight_array.shape != (len(symbols),):
                raise ValueError("weights must contain one value per asset.")
            weight_series = pd.Series(weight_array, index=symbols, dtype=float)
        if not np.all(np.isfinite(weight_series.to_numpy(dtype=float))):
            raise ValueError("weights must be finite.")
        if not np.isclose(float(weight_series.sum()), 1.0, atol=1e-8):
            raise ValueError("weights must sum to one.")
        validated_base_value = float(base_value)
        if not np.isfinite(validated_base_value) or validated_base_value <= 0:
            raise ValueError("base_value must be finite and positive.")
        contributions = weight_series * shock_series
        portfolio_return = float(contributions.sum())
        return PortfolioScenarioAnalysis(
            shocks=shock_series.to_dict(),
            weights=weight_series,
            contributions=contributions,
            portfolio_return=portfolio_return,
            base_value=validated_base_value,
            ending_value=float(validated_base_value * (1.0 + portfolio_return)),
            provenance=DataProvenance(
                provider="derived",
                dataset="portfolio_scenario_analysis",
                source_labels=tuple(symbols),
                transformation_steps=("portfolio shock mapping", "return contribution calculation"),
                request={
                    "base_value": validated_base_value,
                    "shock_symbols": tuple(sorted(normalized_shocks)),
                    "portfolio_input_provenance": self.context.provenance.as_dict(),
                },
            ),
        )

    def backtest(
        self,
        *,
        weights: str | Sequence[float] | pd.Series | Mapping[str, float] = "equal_weight",
        rebalance: str = "monthly",
        transaction_cost_bps: float = 0.0,
        slippage_bps: float = 0.0,
        fixed_transaction_cost: float = 0.0,
        initial_capital: float = 1.0,
        benchmark: str | Sequence[float] | pd.Series | Mapping[str, float] | None = "equal_weight",
        lookback: int = 63,
        min_history: int = 2,
    ):
        """Run a deterministic periodically rebalanced portfolio backtest.

        Parameters
        ----------
        weights : str or sequence or pandas.Series or mapping, default="equal_weight"
            Target allocation policy. Supported string policies include
            ``"equal_weight"``, ``"buy_and_hold"``, and
            ``"inverse_volatility"``. Mappings are keyed by asset symbol;
            sequences are interpreted in optimizer asset order.
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
        benchmark : str or sequence or pandas.Series or mapping or None, default="equal_weight"
            Benchmark used for active-return diagnostics. A pandas Series is
            interpreted as precomputed benchmark returns.
        lookback : int, default=63
            Historical window used by dynamic policies such as
            ``"inverse_volatility"``.
        min_history : int, default=2
            Minimum observations required before dynamic policy estimates are
            used.

        Returns
        -------
        PortfolioBacktestResult
            Simulated equity curve, drawdowns, returns, weights, trades,
            turnover, transaction costs, benchmark diagnostics, and summaries.
        """
        from abaquant.portfolio.backtesting import run_rebalanced_backtest

        return run_rebalanced_backtest(
            self.context.periodic_returns,
            weights=weights,
            rebalance=rebalance,
            transaction_cost_bps=transaction_cost_bps,
            slippage_bps=slippage_bps,
            fixed_transaction_cost=fixed_transaction_cost,
            initial_capital=initial_capital,
            annual_risk_free_rate=self.context.annual_risk_free_rate,
            periods_per_year=self.context.periods_per_year,
            benchmark=benchmark,
            lookback=lookback,
            min_history=min_history,
            allow_short=self.context.allow_short_positions,
        )

    def report(self, *, backtest_kwargs: Mapping[str, object] | None = None):
        """Return an exportable report for this portfolio allocator.

        Parameters
        ----------
        backtest_kwargs : Mapping[str, object], optional
            Keyword arguments forwarded to ``backtest()`` when producing the
            default report backtest summary.

        Returns
        -------
        ExportableReport
            Report object with Markdown, HTML, and PDF export methods.
        """
        from abaquant.reports import build_portfolio_allocator_report

        return build_portfolio_allocator_report(self, backtest_kwargs=backtest_kwargs)

    def visualize(
        self,
        *,
        weights=None,
        chart: str = "cumulative_returns",
        backend: str | None = None,
        theme=None,
        save_path=None,
        filename=None,
    ):
        """Return a figure for weights, cumulative return, or correlation.

        Parameters
        ----------
        weights : array-like or pandas.Series, optional
            Allocation vector for weight-dependent plots. Equal weights are used
            when omitted.
        chart : {"weights", "cumulative_returns", "correlation"}, default="cumulative_returns"
            Portfolio diagnostic to visualize.
        backend : {"matplotlib", "plotly"}, default="matplotlib"
            Figure backend; the method never calls ``show()``.
        """
        from abaquant.visualization import visualize_portfolio_allocator

        return visualize_portfolio_allocator(
            self,
            weights=weights,
            chart=chart,
            backend=backend,
            theme=theme,
            save_path=save_path,
            filename=filename,
        )
