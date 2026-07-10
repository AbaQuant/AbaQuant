"""Integrated portfolio and credit risk dashboard.

Purpose
-------
This module combines portfolio return diagnostics, risk-contribution
estimates, optional backtest drawdowns, asset correlations, and fundamental
credit-proxy assessments into one applied dashboard object.

Conventions
-----------
Portfolio returns are periodic simple returns. Volatility and covariance
figures are annualized with ``periods_per_year``. Risk contributions use the
standard variance-covariance decomposition where each asset contribution to
portfolio volatility is ``weight_i * (Sigma * weight)_i / portfolio_volatility``.

Scope and limitations
---------------------
The dashboard is an aggregation and reporting layer. It does not replace
point-in-time data controls, portfolio construction, model validation, or
investment advice. Credit inputs remain the transparent synthetic proxy scores
produced elsewhere in AbaQuant.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from abaquant.core import DataProvenance, merge_provenance


@dataclass(frozen=True)
class RiskDashboardSummary:
    """Compact summary of an integrated risk dashboard.

    Parameters
    ----------
    portfolio : Mapping[str, float | str | None]
        Scalar portfolio and backtest diagnostics.
    risk_contribution : Mapping[str, float | str | None]
        Concentration diagnostics derived from volatility contributions.
    credit : Mapping[str, object]
        Aggregate credit-proxy score diagnostics.
    correlation : Mapping[str, float | None]
        Aggregate asset-correlation diagnostics.
    """

    portfolio: Mapping[str, float | str | None]
    risk_contribution: Mapping[str, float | str | None]
    credit: Mapping[str, object]
    correlation: Mapping[str, float | None]
    provenance: DataProvenance | None = None

    def as_dict(self) -> dict[str, object]:
        """Return a serialization-friendly nested summary mapping."""
        payload = {
            "portfolio": dict(self.portfolio),
            "risk_contribution": dict(self.risk_contribution),
            "credit": dict(self.credit),
            "correlation": dict(self.correlation),
        }
        if self.provenance is not None:
            payload["provenance"] = self.provenance.as_dict()
        return payload


class RiskDashboard:
    """Combine portfolio risk, backtest, correlation, and credit diagnostics.

    Parameters
    ----------
    portfolio : object
        Portfolio source. Supported inputs are a pandas return DataFrame, a
        ``PortfolioAllocator``-style object exposing ``context.periodic_returns``,
        a ``PortfolioBacktestResult``-style object exposing ``returns()``, or an
        object exposing ``backtest()``.
    credit_assessments : Mapping[str, object], optional
        Fundamental credit-proxy assessments keyed by asset symbol. Assessment
        objects may expose ``synthetic_credit_proxy_score``,
        ``synthetic_credit_proxy_band``, ``available_score_weight``, and
        ``metrics``; dictionary-like rows with the same keys are also accepted.
    weights : sequence, pandas.Series, or mapping, optional
        Portfolio weights used for static risk-contribution diagnostics. Equal
        weights are used when omitted.
    backtest : object, optional
        Precomputed backtest result. If omitted and ``portfolio`` exposes a
        ``backtest`` method, a deterministic default backtest is created.
    annual_risk_free_rate : float, default=0.0
        Annualized risk-free rate used when summary metrics must be computed
        directly from returns rather than delegated to a backtest result.
    periods_per_year : int, default=252
        Number of return observations interpreted as one year.
    """

    def __init__(
        self,
        portfolio: object,
        credit_assessments: Mapping[str, object] | None = None,
        *,
        weights: Sequence[float] | pd.Series | Mapping[str, float] | None = None,
        backtest: object | None = None,
        annual_risk_free_rate: float | None = None,
        periods_per_year: int | None = None,
    ) -> None:
        self.portfolio = portfolio
        self.credit_assessments = dict(credit_assessments or {})
        self.returns_frame = _extract_returns_frame(portfolio)
        self.asset_symbols = list(self.returns_frame.columns)
        self.periods_per_year = _resolve_periods_per_year(portfolio, periods_per_year)
        self.annual_risk_free_rate = _resolve_risk_free_rate(portfolio, annual_risk_free_rate)
        self.weights = _coerce_weights(weights, self.asset_symbols)
        self.backtest_result = backtest if backtest is not None else _default_backtest(portfolio)
        source_records = [
            getattr(getattr(portfolio, "context", portfolio), "provenance", None),
            getattr(self.backtest_result, "provenance", None),
            *(
                getattr(assessment, "provenance", None)
                for assessment in self.credit_assessments.values()
            ),
        ]
        self.provenance = merge_provenance(
            source_records,
            provider="derived",
            dataset="risk_dashboard",
            transformation_steps=(
                "portfolio summary aggregation",
                "risk contribution calculation",
                "credit score aggregation",
                "correlation analysis",
            ),
            request={
                "asset_count": len(self.asset_symbols),
                "credit_assessment_count": len(self.credit_assessments),
                "has_backtest": self.backtest_result is not None,
            },
        )

    def summary(self) -> dict[str, object]:
        """Return nested portfolio, risk-contribution, credit, and correlation summaries."""
        return RiskDashboardSummary(
            portfolio=self.portfolio_summary(),
            risk_contribution=self.risk_contribution_summary(),
            credit=self.credit_summary(),
            correlation=self.correlation_summary(),
        ).as_dict()

    def portfolio_summary(self) -> dict[str, float | str | None]:
        """Return scalar portfolio performance and drawdown diagnostics."""
        if self.backtest_result is not None and callable(
            getattr(self.backtest_result, "summary", None)
        ):
            summary = dict(self.backtest_result.summary())
            summary.setdefault("source", "backtest")
            return summary
        returns = self.portfolio_returns().dropna()
        if returns.empty:
            return {
                "source": "returns",
                "total_return": 0.0,
                "annualized_return": 0.0,
                "annualized_volatility": 0.0,
                "sharpe_ratio": np.nan,
                "sortino_ratio": np.nan,
                "max_drawdown": 0.0,
                "value_at_risk_95": np.nan,
                "conditional_value_at_risk_95": np.nan,
            }
        equity = self.equity_curve()
        total_return = float(equity.iloc[-1] / equity.iloc[0] - 1.0)
        annualized_return = float(returns.mean() * self.periods_per_year)
        volatility = (
            float(returns.std(ddof=1) * np.sqrt(self.periods_per_year)) if len(returns) > 1 else 0.0
        )
        risk_free_periodic = self.annual_risk_free_rate / self.periods_per_year
        excess = returns - risk_free_periodic
        sharpe = (
            float(excess.mean() * self.periods_per_year / volatility) if volatility > 0 else np.nan
        )
        downside = returns[returns < risk_free_periodic]
        downside_deviation = (
            float(downside.std(ddof=1) * np.sqrt(self.periods_per_year))
            if len(downside) > 1
            else 0.0
        )
        sortino = (
            float(excess.mean() * self.periods_per_year / downside_deviation)
            if downside_deviation > 0
            else np.nan
        )
        drawdowns = self.drawdown()
        var_95 = float(returns.quantile(0.05))
        cvar_95 = float(returns[returns <= var_95].mean()) if (returns <= var_95).any() else var_95
        return {
            "source": "returns",
            "total_return": total_return,
            "annualized_return": annualized_return,
            "annualized_volatility": volatility,
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "max_drawdown": float(drawdowns.min()) if len(drawdowns) else 0.0,
            "value_at_risk_95": var_95,
            "conditional_value_at_risk_95": cvar_95,
        }

    def portfolio_returns(self) -> pd.Series:
        """Return weighted periodic portfolio returns."""
        return pd.Series(
            self.returns_frame.to_numpy(dtype=float) @ self.weights.to_numpy(dtype=float),
            index=self.returns_frame.index,
            name="portfolio_return",
        )

    def equity_curve(self, initial_value: float = 1.0) -> pd.Series:
        """Return the dashboard portfolio equity curve."""
        if self.backtest_result is not None and callable(
            getattr(self.backtest_result, "equity_curve", None)
        ):
            return self.backtest_result.equity_curve()
        validated_initial = float(initial_value)
        if not np.isfinite(validated_initial) or validated_initial <= 0:
            raise ValueError("initial_value must be finite and positive.")
        curve = validated_initial * (1.0 + self.portfolio_returns().fillna(0.0)).cumprod()
        return curve.rename("equity")

    def drawdown(self) -> pd.Series:
        """Return portfolio drawdowns from the backtest or weighted returns."""
        if self.backtest_result is not None and callable(
            getattr(self.backtest_result, "drawdowns", None)
        ):
            return self.backtest_result.drawdowns()
        equity = self.equity_curve()
        return (equity / equity.cummax() - 1.0).rename("drawdown")

    def correlation(self) -> pd.DataFrame:
        """Return the asset return correlation matrix."""
        return self.returns_frame.corr()

    def correlation_summary(self) -> dict[str, float | None]:
        """Return aggregate asset-correlation diagnostics."""
        correlation = self.correlation()
        if len(correlation.columns) <= 1:
            return {
                "average_pairwise_correlation": None,
                "minimum_pairwise_correlation": None,
                "maximum_pairwise_correlation": None,
            }
        mask = np.triu(np.ones(correlation.shape, dtype=bool), k=1)
        values = correlation.where(mask).stack().astype(float)
        if values.empty:
            return {
                "average_pairwise_correlation": None,
                "minimum_pairwise_correlation": None,
                "maximum_pairwise_correlation": None,
            }
        return {
            "average_pairwise_correlation": float(values.mean()),
            "minimum_pairwise_correlation": float(values.min()),
            "maximum_pairwise_correlation": float(values.max()),
        }

    def risk_contribution(self) -> pd.DataFrame:
        """Return variance-covariance asset risk contributions."""
        covariance = self.returns_frame.cov() * self.periods_per_year
        covariance = covariance.reindex(
            index=self.asset_symbols, columns=self.asset_symbols
        ).fillna(0.0)
        weights = self.weights.reindex(self.asset_symbols).astype(float)
        weight_array = weights.to_numpy(dtype=float)
        covariance_array = covariance.to_numpy(dtype=float)
        portfolio_variance = float(weight_array @ covariance_array @ weight_array)
        if portfolio_variance <= 0.0 or not np.isfinite(portfolio_variance):
            contribution = pd.Series(0.0, index=self.asset_symbols, dtype=float)
            marginal = pd.Series(0.0, index=self.asset_symbols, dtype=float)
            percent = pd.Series(np.nan, index=self.asset_symbols, dtype=float)
            volatility = 0.0
        else:
            volatility = float(np.sqrt(portfolio_variance))
            marginal = pd.Series(
                covariance_array @ weight_array / volatility, index=self.asset_symbols
            )
            contribution = weights * marginal
            percent = contribution / volatility
        frame = pd.DataFrame(
            {
                "weight": weights,
                "marginal_volatility_contribution": marginal,
                "annualized_volatility_contribution": contribution,
                "percent_risk_contribution": percent,
            }
        )
        return frame.sort_values("annualized_volatility_contribution", ascending=False)

    def risk_contribution_summary(self) -> dict[str, float | str | None]:
        """Return concentration diagnostics from the risk-contribution table."""
        contributions = self.risk_contribution()
        if contributions.empty:
            return {
                "portfolio_annualized_volatility": 0.0,
                "largest_risk_contributor": None,
                "largest_percent_risk_contribution": None,
                "effective_number_of_assets": None,
            }
        percent = contributions["percent_risk_contribution"].dropna()
        effective_assets = (
            float(1.0 / np.square(percent.to_numpy(dtype=float)).sum())
            if not percent.empty and np.square(percent.to_numpy(dtype=float)).sum() > 0
            else None
        )
        top_asset = str(contributions.index[0])
        return {
            "portfolio_annualized_volatility": float(
                contributions["annualized_volatility_contribution"].sum()
            ),
            "largest_risk_contributor": top_asset,
            "largest_percent_risk_contribution": float(
                contributions.iloc[0]["percent_risk_contribution"]
            )
            if pd.notna(contributions.iloc[0]["percent_risk_contribution"])
            else None,
            "effective_number_of_assets": effective_assets,
        }

    def credit_scores(self) -> pd.DataFrame:
        """Return a credit-proxy score table for all supplied assessments."""
        rows: list[dict[str, object]] = []
        for symbol, assessment in self.credit_assessments.items():
            metrics = _assessment_metrics(assessment)
            rows.append(
                {
                    "symbol": str(symbol),
                    "synthetic_credit_proxy_score": _assessment_value(
                        assessment, "synthetic_credit_proxy_score"
                    ),
                    "synthetic_credit_proxy_band": _assessment_value(
                        assessment, "synthetic_credit_proxy_band"
                    ),
                    "available_score_weight": _assessment_value(
                        assessment, "available_score_weight"
                    ),
                    "debt_to_equity": metrics.get("debt_to_equity"),
                    "current_ratio": metrics.get("current_ratio"),
                    "interest_coverage": metrics.get("interest_coverage"),
                    "net_debt_to_ebitda": metrics.get("net_debt_to_ebitda"),
                    "altman_z_score": metrics.get("altman_z_score"),
                    "piotroski_f_score": metrics.get("piotroski_f_score"),
                }
            )
        if not rows:
            return pd.DataFrame(
                columns=[
                    "synthetic_credit_proxy_score",
                    "synthetic_credit_proxy_band",
                    "available_score_weight",
                    "debt_to_equity",
                    "current_ratio",
                    "interest_coverage",
                    "net_debt_to_ebitda",
                    "altman_z_score",
                    "piotroski_f_score",
                ]
            )
        return pd.DataFrame(rows).set_index("symbol")

    def credit_summary(self) -> dict[str, object]:
        """Return aggregate diagnostics for supplied credit-proxy assessments."""
        scores = self.credit_scores()
        if scores.empty:
            return {
                "assessment_count": 0,
                "average_score": None,
                "minimum_score": None,
                "maximum_score": None,
                "lowest_score_symbol": None,
                "highest_score_symbol": None,
                "bands": {},
            }
        numeric_scores = pd.to_numeric(
            scores["synthetic_credit_proxy_score"], errors="coerce"
        ).dropna()
        bands = (
            scores["synthetic_credit_proxy_band"]
            .fillna("unavailable")
            .astype(str)
            .value_counts()
            .to_dict()
        )
        if numeric_scores.empty:
            return {
                "assessment_count": len(scores),
                "average_score": None,
                "minimum_score": None,
                "maximum_score": None,
                "lowest_score_symbol": None,
                "highest_score_symbol": None,
                "bands": bands,
            }
        return {
            "assessment_count": len(scores),
            "average_score": float(numeric_scores.mean()),
            "minimum_score": float(numeric_scores.min()),
            "maximum_score": float(numeric_scores.max()),
            "lowest_score_symbol": str(numeric_scores.idxmin()),
            "highest_score_symbol": str(numeric_scores.idxmax()),
            "bands": bands,
        }

    def report(self):
        """Return an exportable report for this integrated risk dashboard.

        Returns
        -------
        ExportableReport
            Report object with Markdown, HTML, and PDF export methods.
        """
        from abaquant.reports import build_risk_dashboard_report

        return build_risk_dashboard_report(self)

    def visual_report(
        self,
        *,
        charts: Sequence[str] = ("risk_contribution", "drawdown", "credit_scores", "correlation"),
        backend: str | None = None,
        theme=None,
        save_path: str | Path | None = None,
    ) -> dict[str, object]:
        """Return a dictionary of dashboard figures keyed by chart name."""
        figures: dict[str, object] = {}
        for chart in charts:
            output_filename = str(chart) if save_path is not None else None
            figures[str(chart)] = self.visualize(
                chart=str(chart),
                backend=backend,
                theme=theme,
                save_path=save_path,
                filename=output_filename,
            )
        return figures

    def visualize(
        self,
        *,
        chart: str = "risk_contribution",
        backend: str | None = None,
        theme=None,
        save_path: str | Path | None = None,
        filename: str | None = None,
    ):
        """Return a dashboard figure for risk, drawdown, credit, or correlation."""
        from abaquant.visualization import visualize_risk_dashboard

        return visualize_risk_dashboard(
            self, chart=chart, backend=backend, theme=theme, save_path=save_path, filename=filename
        )


def _extract_returns_frame(portfolio: object) -> pd.DataFrame:
    """Return a clean return DataFrame from a supported portfolio object."""
    if isinstance(portfolio, pd.DataFrame):
        frame = portfolio.copy(deep=True)
    elif callable(getattr(portfolio, "returns", None)):
        series = portfolio.returns()
        if isinstance(series, pd.Series):
            frame = pd.DataFrame({"portfolio": series.astype(float)})
        else:
            frame = pd.DataFrame(series)
    else:
        context = getattr(portfolio, "context", None)
        periodic_returns = getattr(context, "periodic_returns", None)
        if isinstance(periodic_returns, pd.DataFrame):
            frame = periodic_returns.copy(deep=True)
        else:
            raise ValueError(
                "portfolio must be a return DataFrame, a PortfolioAllocator-like object, "
                "or a backtest result exposing returns()."
            )
    if frame.empty:
        raise ValueError("portfolio returns must not be empty.")
    frame = frame.apply(pd.to_numeric, errors="coerce").dropna(how="any")
    if frame.empty:
        raise ValueError("portfolio returns must contain finite numeric observations.")
    if not isinstance(frame.index, pd.DatetimeIndex):
        frame.index = pd.date_range("2000-01-01", periods=len(frame), freq="D")
    return frame.astype(float)


def _resolve_periods_per_year(portfolio: object, periods_per_year: int | None) -> int:
    """Resolve annualization periods from explicit input or portfolio context."""
    if periods_per_year is not None:
        value = int(periods_per_year)
    else:
        context = getattr(portfolio, "context", None)
        value = int(
            getattr(context, "periods_per_year", getattr(portfolio, "periods_per_year", 252))
        )
    if value <= 0:
        raise ValueError("periods_per_year must be positive.")
    return value


def _resolve_risk_free_rate(portfolio: object, annual_risk_free_rate: float | None) -> float:
    """Resolve annualized risk-free rate from explicit input or portfolio context."""
    if annual_risk_free_rate is not None:
        value = float(annual_risk_free_rate)
    else:
        context = getattr(portfolio, "context", None)
        value = float(
            getattr(
                context, "annual_risk_free_rate", getattr(portfolio, "annual_risk_free_rate", 0.0)
            )
        )
    if not np.isfinite(value):
        raise ValueError("annual_risk_free_rate must be finite.")
    return value


def _coerce_weights(
    weights: Sequence[float] | pd.Series | Mapping[str, float] | None,
    symbols: Sequence[str],
) -> pd.Series:
    """Validate and align dashboard weights to asset symbols."""
    labels = list(symbols)
    if not labels:
        raise ValueError("at least one asset is required.")
    if weights is None:
        series = pd.Series(1.0 / len(labels), index=labels, dtype=float)
    elif isinstance(weights, pd.Series):
        series = weights.reindex(labels).astype(float)
    elif isinstance(weights, Mapping):
        unknown = sorted(set(map(str, weights)) - set(labels))
        if unknown:
            raise ValueError(f"Unknown weight symbols: {', '.join(unknown)}.")
        series = (
            pd.Series({str(key): float(value) for key, value in weights.items()}, dtype=float)
            .reindex(labels)
            .fillna(0.0)
        )
    else:
        array = np.asarray(list(weights), dtype=float)
        if array.shape != (len(labels),):
            raise ValueError("weights must contain one value per asset.")
        series = pd.Series(array, index=labels, dtype=float)
    if not np.all(np.isfinite(series.to_numpy(dtype=float))):
        raise ValueError("weights must be finite.")
    total = float(series.sum())
    if not np.isclose(total, 1.0, atol=1e-8):
        raise ValueError("weights must sum to one.")
    return series


def _default_backtest(portfolio: object) -> object | None:
    """Return a default backtest when the portfolio object supports one."""
    method = getattr(portfolio, "backtest", None)
    if callable(method):
        try:
            return method(weights="equal_weight", rebalance="monthly", benchmark="equal_weight")
        except TypeError:
            try:
                return method()
            except Exception:
                return None
        except Exception:
            return None
    return (
        portfolio
        if callable(getattr(portfolio, "summary", None))
        and callable(getattr(portfolio, "drawdowns", None))
        else None
    )


def _assessment_value(assessment: object, name: str) -> object:
    """Return one credit-assessment attribute or mapping value."""
    if isinstance(assessment, Mapping):
        return assessment.get(name)
    return getattr(assessment, name, None)


def _assessment_metrics(assessment: object) -> Mapping[str, object]:
    """Return metric mapping from a credit assessment or dictionary row."""
    if isinstance(assessment, Mapping):
        metrics = assessment.get("metrics")
        return metrics if isinstance(metrics, Mapping) else assessment
    metrics = getattr(assessment, "metrics", {})
    return metrics if isinstance(metrics, Mapping) else {}
