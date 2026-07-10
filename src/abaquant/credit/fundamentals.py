"""Grouped financial-statement inputs and transparent credit-proxy metrics."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from math import isfinite
from pathlib import Path

import numpy as np
import pandas as pd

from abaquant.core import DataProvenance

MetricValue = float | int | str | None


@dataclass(frozen=True)
class ReportedValue:
    """One reported financial value with statement provenance."""

    value: float
    reporting_date: date | None = None
    currency: str | None = None
    source: str = "manual"
    source_label: str | None = None


@dataclass(frozen=True)
class BalanceSheetInputs:
    """Balance-sheet values for one reporting date in a consistent currency."""

    total_debt: float | None = None
    total_equity: float | None = None
    current_assets: float | None = None
    inventory: float | None = None
    current_liabilities: float | None = None
    cash_and_cash_equivalents: float | None = None
    total_assets: float | None = None
    total_liabilities: float | None = None
    retained_earnings: float | None = None
    long_term_debt: float | None = None
    shares_outstanding: float | None = None


@dataclass(frozen=True)
class IncomeStatementInputs:
    """Income-statement values for one reporting period in a consistent currency."""

    revenue: float | None = None
    gross_profit: float | None = None
    ebit: float | None = None
    ebitda: float | None = None
    interest_expense: float | None = None
    net_income: float | None = None


@dataclass(frozen=True)
class CashFlowInputs:
    """Cash-flow values for one reporting period in a consistent currency."""

    operating_cash_flow: float | None = None


@dataclass(frozen=True)
class PriorPeriodInputs:
    """Comparable values from the immediately preceding reporting period."""

    total_assets: float | None = None
    net_income: float | None = None
    long_term_debt: float | None = None
    current_assets: float | None = None
    current_liabilities: float | None = None
    shares_outstanding: float | None = None
    gross_profit: float | None = None
    revenue: float | None = None


@dataclass(frozen=True)
class MarketEquityObservation:
    """Market-capitalization observation with its observation date."""

    market_value_equity: float | None = None
    observation_date: date | None = None
    currency: str | None = None


@dataclass(frozen=True)
class CreditHistoricalSeries:
    """Comparable historical earnings and leverage observations, oldest first."""

    earnings_history: Sequence[float] = ()
    leverage_history: Sequence[float] = ()


@dataclass(frozen=True)
class CreditAnalysisInputs:
    """Grouped, immutable inputs for fundamental credit-proxy calculations.

    The current, prior-period, market-equity, and historical values are kept in
    separate groups to make reporting-period provenance explicit.
    """

    balance_sheet: BalanceSheetInputs
    income_statement: IncomeStatementInputs
    cash_flow_statement: CashFlowInputs
    prior_period: PriorPeriodInputs | None = None
    market_equity: MarketEquityObservation | None = None
    historical_series: CreditHistoricalSeries | None = None
    reporting_currency: str | None = None
    reporting_period: str | None = None
    provenance: DataProvenance | None = None

    def __post_init__(self) -> None:
        """Validate finite numeric inputs and normalize historical sequences."""
        for group in (
            self.balance_sheet,
            self.income_statement,
            self.cash_flow_statement,
            self.prior_period,
            self.market_equity,
        ):
            if group is None:
                continue
            for field_name, value in vars(group).items():
                if field_name in {"observation_date", "currency"}:
                    continue
                if value is not None and not _is_finite_number(value):
                    raise ValueError(f"{field_name} must be finite when supplied.")
        history = self.historical_series or CreditHistoricalSeries()
        normalized = CreditHistoricalSeries(
            earnings_history=_normalize_history(history.earnings_history, "earnings_history"),
            leverage_history=_normalize_history(history.leverage_history, "leverage_history"),
        )
        object.__setattr__(self, "historical_series", normalized)
        if self.provenance is None:
            object.__setattr__(
                self,
                "provenance",
                DataProvenance(
                    provider="manual",
                    dataset="credit_analysis_inputs",
                    currency=self.reporting_currency,
                    reporting_date=self.reporting_period,
                    transformation_steps=("grouped credit input validation",),
                ),
            )

    # Read-only projections keep metric formulas compact while preserving grouped construction.
    @property
    def total_debt(self):
        """Return current total debt from the balance-sheet input group."""
        return self.balance_sheet.total_debt

    @property
    def total_equity(self):
        """Return current total equity from the balance-sheet input group."""
        return self.balance_sheet.total_equity

    @property
    def current_assets(self):
        """Return current assets from the balance-sheet input group."""
        return self.balance_sheet.current_assets

    @property
    def inventory(self):
        """Return inventory from the balance-sheet input group."""
        return self.balance_sheet.inventory

    @property
    def current_liabilities(self):
        """Return current liabilities from the balance-sheet input group."""
        return self.balance_sheet.current_liabilities

    @property
    def cash_and_cash_equivalents(self):
        """Return cash and cash equivalents from the balance-sheet input group."""
        return self.balance_sheet.cash_and_cash_equivalents

    @property
    def total_assets(self):
        """Return current total assets from the balance-sheet input group."""
        return self.balance_sheet.total_assets

    @property
    def total_liabilities(self):
        """Return current total liabilities from the balance-sheet input group."""
        return self.balance_sheet.total_liabilities

    @property
    def retained_earnings(self):
        """Return retained earnings from the balance-sheet input group."""
        return self.balance_sheet.retained_earnings

    @property
    def long_term_debt(self):
        """Return long-term debt from the balance-sheet input group."""
        return self.balance_sheet.long_term_debt

    @property
    def shares_outstanding(self):
        """Return current shares outstanding from the balance-sheet input group."""
        return self.balance_sheet.shares_outstanding

    @property
    def ebit(self):
        """Return EBIT from the income-statement input group."""
        return self.income_statement.ebit

    @property
    def ebitda(self):
        """Return EBITDA from the income-statement input group."""
        return self.income_statement.ebitda

    @property
    def interest_expense(self):
        """Return interest expense from the income-statement input group."""
        return self.income_statement.interest_expense

    @property
    def revenue(self):
        """Return current revenue from the income-statement input group."""
        return self.income_statement.revenue

    @property
    def net_income(self):
        """Return current net income from the income-statement input group."""
        return self.income_statement.net_income

    @property
    def gross_profit(self):
        """Return current gross profit from the income-statement input group."""
        return self.income_statement.gross_profit

    @property
    def operating_cash_flow(self):
        """Return operating cash flow from the cash-flow input group."""
        return self.cash_flow_statement.operating_cash_flow

    @property
    def market_value_equity(self):
        """Return observed market equity, or ``None`` when it was not supplied."""
        return None if self.market_equity is None else self.market_equity.market_value_equity

    @property
    def earnings_history(self):
        """Return the normalized historical earnings sequence."""
        return self.historical_series.earnings_history

    @property
    def leverage_history(self):
        """Return the normalized historical leverage sequence."""
        return self.historical_series.leverage_history

    def _prior(self, name: str):
        """Return one prior-period value or ``None`` when unavailable."""
        return None if self.prior_period is None else getattr(self.prior_period, name)

    @property
    def previous_total_assets(self):
        """Return prior-period total assets, or ``None`` when unavailable."""
        return self._prior("total_assets")

    @property
    def previous_net_income(self):
        """Return prior-period net income, or ``None`` when unavailable."""
        return self._prior("net_income")

    @property
    def previous_long_term_debt(self):
        """Return prior-period long-term debt, or ``None`` when unavailable."""
        return self._prior("long_term_debt")

    @property
    def previous_current_assets(self):
        """Return prior-period current assets, or ``None`` when unavailable."""
        return self._prior("current_assets")

    @property
    def previous_current_liabilities(self):
        """Return prior-period current liabilities, or ``None`` when unavailable."""
        return self._prior("current_liabilities")

    @property
    def previous_shares_outstanding(self):
        """Return prior-period shares outstanding, or ``None`` when unavailable."""
        return self._prior("shares_outstanding")

    @property
    def previous_gross_profit(self):
        """Return prior-period gross profit, or ``None`` when unavailable."""
        return self._prior("gross_profit")

    @property
    def previous_revenue(self):
        """Return prior-period revenue, or ``None`` when unavailable."""
        return self._prior("revenue")


@dataclass(frozen=True)
class CreditScenarioAnalysis:
    """Multiplier scenario grid for a fundamental credit-proxy assessment.

    Parameters
    ----------
    data : pandas.DataFrame
        Long-form scenario table containing the multipliers and selected credit
        metrics after each perturbed recalculation.
    base_assessment : CreditProxyAssessment
        Assessment used as the base case for all multiplier shocks.
    """

    data: pd.DataFrame
    base_assessment: CreditProxyAssessment
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
                    dataset="credit_scenario_analysis",
                    source_labels=self.base_assessment.provenance.source_labels,
                    currency=self.base_assessment.provenance.currency,
                    reporting_date=self.base_assessment.provenance.reporting_date,
                    transformation_steps=(
                        "credit multiplier scenario grid",
                        "credit proxy metric recalculation",
                    ),
                    request={
                        "rows": len(self.data),
                        "base_assessment": self.base_assessment.provenance.as_dict(),
                    },
                ),
            )

    def as_dict(self) -> dict[str, object]:
        """Return a serialization-friendly credit scenario mapping."""
        return {
            "base_score": self.base_assessment.synthetic_credit_proxy_score,
            "base_band": self.base_assessment.synthetic_credit_proxy_band,
            "records": self.data.to_dict("records"),
            "provenance": self.provenance.as_dict(),
        }

    def report(self):
        """Return an exportable report for this credit-proxy assessment.

        Returns
        -------
        ExportableReport
            Report object with Markdown, HTML, and PDF export methods.
        """
        from abaquant.reports import build_credit_report

        return build_credit_report(self)

    def visualize(
        self,
        *,
        metric: str = "synthetic_credit_proxy_score",
        chart: str = "heatmap",
        backend: str | None = None,
        theme=None,
        save_path: str | Path | None = None,
        filename: str | None = None,
    ):
        """Return a figure for this credit multiplier scenario grid.

        Parameters
        ----------
        metric : str, default="synthetic_credit_proxy_score"
            Numeric scenario metric to display.
        chart : {"heatmap", "curves", "bar"}, default="heatmap"
            Visual form for the scenario table.
        backend : {"matplotlib", "plotly"}, optional
            Figure backend override.
        theme : VisualizationTheme, optional
            Per-call style override.
        save_path : str or pathlib.Path, optional
            Explicit export path.
        filename : str, optional
            Filename relative to the active theme's save directory.
        """
        from abaquant.visualization import visualize_credit_scenario

        return visualize_credit_scenario(
            self,
            metric=metric,
            chart=chart,
            backend=backend,
            theme=theme,
            save_path=save_path,
            filename=filename,
        )


@dataclass(frozen=True)
class CreditProxyAssessment:
    """Transparent result of fundamental credit-proxy calculations.

    Attributes
    ----------
    metrics : Mapping[str, MetricValue]
        Ratio, score, trend, and diagnostic values. Missing inputs produce
        ``None`` for affected metrics rather than estimated substitute values.
    piotroski_signals : Mapping[str, int | None]
        Nine individually documented F-score binary signals. ``None`` indicates
        an unavailable signal because its required inputs were not supplied.
    synthetic_credit_proxy_score : float | None
        Completeness-normalized heuristic score on a 0--100 scale. It is not a
        credit rating or probability of default.
    synthetic_credit_proxy_band : str
        Plain-language proxy band derived from the score, or ``"unavailable"``.
    available_score_weight : float
        Maximum heuristic weight supported by the supplied inputs before score
        normalization. A low value indicates limited metric coverage.
    disclosures : tuple[str, ...]
        Mandatory limitations and model-use disclosures.
    """

    metrics: Mapping[str, MetricValue]
    piotroski_signals: Mapping[str, int | None]
    synthetic_credit_proxy_score: float | None
    synthetic_credit_proxy_band: str
    available_score_weight: float
    disclosures: tuple[str, ...]
    inputs: CreditAnalysisInputs | None = None
    provenance: DataProvenance | None = None

    def __post_init__(self) -> None:
        """Attach derived provenance to credit assessments when omitted."""
        if self.provenance is None:
            input_provenance = self.inputs.provenance if self.inputs is not None else None
            source_labels = input_provenance.source_labels if input_provenance is not None else ()
            request = {
                "input_provenance": input_provenance.as_dict()
                if input_provenance is not None
                else None,
                "available_score_weight": self.available_score_weight,
            }
            object.__setattr__(
                self,
                "provenance",
                DataProvenance(
                    provider="derived",
                    dataset="credit_proxy_assessment",
                    source_labels=source_labels,
                    currency=self.inputs.reporting_currency if self.inputs is not None else None,
                    reporting_date=self.inputs.reporting_period
                    if self.inputs is not None
                    else None,
                    transformation_steps=(
                        "credit metric calculation",
                        "Piotroski signal calculation",
                        "synthetic credit proxy scoring",
                    ),
                    request=request,
                ),
            )

    def scenario_analysis(
        self,
        *,
        debt_multiplier: Sequence[float] = (1.0,),
        ebitda_multiplier: Sequence[float] = (1.0,),
        ebit_multiplier: Sequence[float] = (1.0,),
        interest_expense_multiplier: Sequence[float] = (1.0,),
    ) -> CreditScenarioAnalysis:
        """Recalculate credit-proxy metrics over statement-input multipliers.

        Parameters
        ----------
        debt_multiplier : Sequence[float], default=(1.0,)
            Multipliers applied to total debt and long-term debt.
        ebitda_multiplier : Sequence[float], default=(1.0,)
            Multipliers applied to EBITDA.
        ebit_multiplier : Sequence[float], default=(1.0,)
            Multipliers applied to EBIT.
        interest_expense_multiplier : Sequence[float], default=(1.0,)
            Multipliers applied to interest expense.

        Returns
        -------
        CreditScenarioAnalysis
            Long-form scenario grid containing selected recomputed metrics.

        Raises
        ------
        ValueError
            If this assessment was not built with retained input provenance.
        """
        if self.inputs is None:
            raise ValueError(
                "Credit scenario analysis requires an assessment built by "
                "calculate_credit_proxy_metrics(), which retains the original inputs."
            )
        return _credit_scenario_analysis(
            self,
            debt_multiplier=debt_multiplier,
            ebitda_multiplier=ebitda_multiplier,
            ebit_multiplier=ebit_multiplier,
            interest_expense_multiplier=interest_expense_multiplier,
        )

    def as_dict(self) -> dict[str, MetricValue]:
        """Return a flat, serialization-friendly mapping of assessment outputs.

        Returns
        -------
        dict[str, MetricValue]
            Metric values plus the synthetic proxy score, band, coverage weight,
            and semicolon-separated disclosures.
        """
        flattened = dict(self.metrics)
        flattened["synthetic_credit_proxy_score"] = self.synthetic_credit_proxy_score
        flattened["synthetic_credit_proxy_band"] = self.synthetic_credit_proxy_band
        flattened["available_score_weight"] = self.available_score_weight
        flattened["disclosures"] = "; ".join(self.disclosures)
        return flattened

    def report(self):
        """Return an exportable report for this credit-proxy assessment.

        Returns
        -------
        ExportableReport
            Report object with Markdown, HTML, and PDF export methods.
        """
        from abaquant.reports import build_credit_report

        return build_credit_report(self)

    def visualize(
        self,
        *,
        chart: str = "metrics",
        backend: str | None = None,
        theme=None,
        save_path=None,
        filename=None,
    ):
        """Return a figure for this credit-proxy assessment.

        Parameters
        ----------
        chart : {"metrics", "score"}, default="metrics"
            Numeric metric comparison or synthetic-score chart.
        backend : {"matplotlib", "plotly"}, default="matplotlib"
            Figure backend; the returned figure is not displayed automatically.
        """
        from abaquant.visualization import visualize_credit_assessment

        return visualize_credit_assessment(
            self, chart=chart, backend=backend, theme=theme, save_path=save_path, filename=filename
        )


def calculate_credit_proxy_metrics(inputs: CreditAnalysisInputs) -> CreditProxyAssessment:
    r"""Calculate manual fundamental credit-proxy metrics.

    Parameters
    ----------
    inputs : CreditAnalysisInputs
        Manual statement and market-value inputs measured consistently in one
        currency and reporting-period convention.

    Returns
    -------
    CreditProxyAssessment
        Ratios, traditional Altman Z-score, Piotroski F-score and components,
        earnings volatility, leverage trend, and a clearly labeled synthetic
        proxy score.

    Notes
    -----
    Definitions include:

    .. math::

        \mathrm{Debt\!\text{-}\!to\!\text{-}Equity} = D / E,
        \qquad
        \mathrm{Current\ Ratio} = CA / CL,

    .. math::

        \mathrm{Interest\ Coverage} = EBIT / I,
        \qquad
        \mathrm{Net\ Debt}/EBITDA = (D - C) / EBITDA.

    The traditional Altman formulation is

    .. math::

        Z = 1.2X_1 + 1.4X_2 + 3.3X_3 + 0.6X_4 + 1.0X_5,

    where the component definitions are reported in the returned metrics.
    The synthetic score normalizes only across components that can be computed
    from supplied inputs; it should therefore be compared only alongside
    ``available_score_weight`` and the disclosures.

    References
    ----------
    Altman (1968); Piotroski (2000).
    """
    debt_to_equity = _safe_ratio(inputs.total_debt, inputs.total_equity)
    current_ratio = _safe_ratio(inputs.current_assets, inputs.current_liabilities)
    quick_assets = _difference(inputs.current_assets, inputs.inventory)
    quick_ratio = _safe_ratio(quick_assets, inputs.current_liabilities)
    interest_coverage = _safe_ratio(inputs.ebit, inputs.interest_expense)
    net_debt = _difference(inputs.total_debt, inputs.cash_and_cash_equivalents)
    net_debt_to_ebitda = _safe_ratio(net_debt, inputs.ebitda)
    operating_cash_flow_to_total_debt = _safe_ratio(inputs.operating_cash_flow, inputs.total_debt)
    altman_z_score, altman_components = _calculate_altman_z_score(inputs)
    piotroski_score, piotroski_signals = _calculate_piotroski_f_score(inputs)
    earnings_standard_deviation, earnings_volatility = _earnings_volatility(inputs.earnings_history)
    leverage_trend_change, leverage_trend = _leverage_trend(inputs.leverage_history)

    metrics: dict[str, MetricValue] = {
        "debt_to_equity": debt_to_equity,
        "current_ratio": current_ratio,
        "quick_ratio": quick_ratio,
        "interest_coverage": interest_coverage,
        "net_debt": net_debt,
        "net_debt_to_ebitda": net_debt_to_ebitda,
        "operating_cash_flow_to_total_debt": operating_cash_flow_to_total_debt,
        "altman_z_score": altman_z_score,
        "altman_working_capital_to_total_assets": altman_components[
            "working_capital_to_total_assets"
        ],
        "altman_retained_earnings_to_total_assets": altman_components[
            "retained_earnings_to_total_assets"
        ],
        "altman_ebit_to_total_assets": altman_components["ebit_to_total_assets"],
        "altman_market_value_equity_to_total_liabilities": altman_components[
            "market_value_equity_to_total_liabilities"
        ],
        "altman_revenue_to_total_assets": altman_components["revenue_to_total_assets"],
        "piotroski_f_score": piotroski_score,
        "earnings_standard_deviation": earnings_standard_deviation,
        "earnings_volatility": earnings_volatility,
        "leverage_trend_change": leverage_trend_change,
        "leverage_trend": leverage_trend,
    }
    proxy_score, proxy_band, available_weight = _synthetic_score(
        debt_to_equity=debt_to_equity,
        current_ratio=current_ratio,
        quick_ratio=quick_ratio,
        interest_coverage=interest_coverage,
        net_debt_to_ebitda=net_debt_to_ebitda,
        operating_cash_flow_to_total_debt=operating_cash_flow_to_total_debt,
        altman_z_score=altman_z_score,
        piotroski_f_score=piotroski_score,
        leverage_trend=leverage_trend,
    )
    disclosures = (
        "Synthetic credit proxy score is a heuristic balance-sheet indicator, not a credit rating or probability of default.",
        "Altman Z-score is reported using the traditional public-company formulation and may not be appropriate for non-manufacturing, financial, or private firms.",
        "Manual inputs must be comparable in currency, consolidation perimeter, and reporting period.",
        "Missing inputs are not estimated; affected metrics and score components are omitted from coverage-normalized scoring.",
    )
    return CreditProxyAssessment(
        metrics=metrics,
        piotroski_signals=piotroski_signals,
        synthetic_credit_proxy_score=proxy_score,
        synthetic_credit_proxy_band=proxy_band,
        available_score_weight=available_weight,
        disclosures=disclosures,
        inputs=inputs,
        provenance=DataProvenance(
            provider="derived",
            dataset="credit_proxy_assessment",
            source_labels=inputs.provenance.source_labels,
            currency=inputs.reporting_currency,
            reporting_date=inputs.reporting_period,
            transformation_steps=(
                "credit metric calculation",
                "Altman Z-score calculation",
                "Piotroski F-score calculation",
                "synthetic credit proxy scoring",
            ),
            request={"input_provenance": inputs.provenance.as_dict()},
        ),
    )


def _finite_multipliers(values: Sequence[float], name: str) -> list[float]:
    """Return a non-empty finite multiplier list for credit scenarios."""
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be a numeric sequence, not a string.")
    normalized = [float(value) for value in values]
    if not normalized:
        raise ValueError(f"{name} must contain at least one value.")
    if not all(isfinite(value) for value in normalized):
        raise ValueError(f"{name} must contain finite values.")
    if any(value < 0 for value in normalized):
        raise ValueError(f"{name} must contain non-negative multipliers.")
    return normalized


def _scale_optional(value: float | None, multiplier: float) -> float | None:
    """Scale a nullable accounting value by one scenario multiplier."""
    return None if value is None else float(value * multiplier)


def _scenario_inputs(
    inputs: CreditAnalysisInputs,
    *,
    debt_multiplier: float,
    ebitda_multiplier: float,
    ebit_multiplier: float,
    interest_expense_multiplier: float,
) -> CreditAnalysisInputs:
    """Return a new grouped credit input object after applying multipliers."""
    balance_sheet = BalanceSheetInputs(
        total_debt=_scale_optional(inputs.balance_sheet.total_debt, debt_multiplier),
        total_equity=inputs.balance_sheet.total_equity,
        current_assets=inputs.balance_sheet.current_assets,
        inventory=inputs.balance_sheet.inventory,
        current_liabilities=inputs.balance_sheet.current_liabilities,
        cash_and_cash_equivalents=inputs.balance_sheet.cash_and_cash_equivalents,
        total_assets=inputs.balance_sheet.total_assets,
        total_liabilities=inputs.balance_sheet.total_liabilities,
        retained_earnings=inputs.balance_sheet.retained_earnings,
        long_term_debt=_scale_optional(inputs.balance_sheet.long_term_debt, debt_multiplier),
        shares_outstanding=inputs.balance_sheet.shares_outstanding,
    )
    income_statement = IncomeStatementInputs(
        revenue=inputs.income_statement.revenue,
        gross_profit=inputs.income_statement.gross_profit,
        ebit=_scale_optional(inputs.income_statement.ebit, ebit_multiplier),
        ebitda=_scale_optional(inputs.income_statement.ebitda, ebitda_multiplier),
        interest_expense=_scale_optional(
            inputs.income_statement.interest_expense, interest_expense_multiplier
        ),
        net_income=inputs.income_statement.net_income,
    )
    return CreditAnalysisInputs(
        balance_sheet=balance_sheet,
        income_statement=income_statement,
        cash_flow_statement=inputs.cash_flow_statement,
        prior_period=inputs.prior_period,
        market_equity=inputs.market_equity,
        historical_series=inputs.historical_series,
        reporting_currency=inputs.reporting_currency,
        reporting_period=inputs.reporting_period,
    )


def _credit_scenario_analysis(
    assessment: CreditProxyAssessment,
    *,
    debt_multiplier: Sequence[float],
    ebitda_multiplier: Sequence[float],
    ebit_multiplier: Sequence[float],
    interest_expense_multiplier: Sequence[float],
) -> CreditScenarioAnalysis:
    """Build a credit multiplier scenario table from retained base inputs."""
    base_inputs = assessment.inputs
    if base_inputs is None:
        raise ValueError("assessment.inputs is required for credit scenario analysis.")
    debt_multipliers = _finite_multipliers(debt_multiplier, "debt_multiplier")
    ebitda_multipliers = _finite_multipliers(ebitda_multiplier, "ebitda_multiplier")
    ebit_multipliers = _finite_multipliers(ebit_multiplier, "ebit_multiplier")
    interest_multipliers = _finite_multipliers(
        interest_expense_multiplier, "interest_expense_multiplier"
    )
    rows: list[dict[str, MetricValue]] = []
    for debt_value in debt_multipliers:
        for ebitda_value in ebitda_multipliers:
            for ebit_value in ebit_multipliers:
                for interest_value in interest_multipliers:
                    scenario_inputs = _scenario_inputs(
                        base_inputs,
                        debt_multiplier=debt_value,
                        ebitda_multiplier=ebitda_value,
                        ebit_multiplier=ebit_value,
                        interest_expense_multiplier=interest_value,
                    )
                    scenario_assessment = calculate_credit_proxy_metrics(scenario_inputs)
                    metrics = scenario_assessment.metrics
                    rows.append(
                        {
                            "debt_multiplier": debt_value,
                            "ebitda_multiplier": ebitda_value,
                            "ebit_multiplier": ebit_value,
                            "interest_expense_multiplier": interest_value,
                            "debt_to_equity": metrics.get("debt_to_equity"),
                            "interest_coverage": metrics.get("interest_coverage"),
                            "net_debt_to_ebitda": metrics.get("net_debt_to_ebitda"),
                            "altman_z_score": metrics.get("altman_z_score"),
                            "piotroski_f_score": metrics.get("piotroski_f_score"),
                            "synthetic_credit_proxy_score": scenario_assessment.synthetic_credit_proxy_score,
                            "synthetic_credit_proxy_band": scenario_assessment.synthetic_credit_proxy_band,
                            "available_score_weight": scenario_assessment.available_score_weight,
                        }
                    )
    return CreditScenarioAnalysis(data=pd.DataFrame(rows), base_assessment=assessment)


def _calculate_altman_z_score(
    inputs: CreditAnalysisInputs,
) -> tuple[float | None, dict[str, float | None]]:
    """Compute the traditional five-factor public-company Altman Z-score."""
    working_capital = _difference(inputs.current_assets, inputs.current_liabilities)
    components = {
        "working_capital_to_total_assets": _safe_ratio(working_capital, inputs.total_assets),
        "retained_earnings_to_total_assets": _safe_ratio(
            inputs.retained_earnings, inputs.total_assets
        ),
        "ebit_to_total_assets": _safe_ratio(inputs.ebit, inputs.total_assets),
        "market_value_equity_to_total_liabilities": _safe_ratio(
            inputs.market_value_equity, inputs.total_liabilities
        ),
        "revenue_to_total_assets": _safe_ratio(inputs.revenue, inputs.total_assets),
    }
    if any(component is None for component in components.values()):
        return None, components
    z_score = (
        1.2 * components["working_capital_to_total_assets"]
        + 1.4 * components["retained_earnings_to_total_assets"]
        + 3.3 * components["ebit_to_total_assets"]
        + 0.6 * components["market_value_equity_to_total_liabilities"]
        + 1.0 * components["revenue_to_total_assets"]
    )
    return float(z_score), components


def _calculate_piotroski_f_score(
    inputs: CreditAnalysisInputs,
) -> tuple[int | None, dict[str, int | None]]:
    """Calculate the nine binary Piotroski F-score signals without imputation."""
    current_return_on_assets = _safe_ratio(inputs.net_income, inputs.total_assets)
    previous_return_on_assets = _safe_ratio(
        inputs.previous_net_income, inputs.previous_total_assets
    )
    current_leverage = _safe_ratio(inputs.long_term_debt, inputs.total_assets)
    previous_leverage = _safe_ratio(inputs.previous_long_term_debt, inputs.previous_total_assets)
    current_liquidity = _safe_ratio(inputs.current_assets, inputs.current_liabilities)
    previous_liquidity = _safe_ratio(
        inputs.previous_current_assets, inputs.previous_current_liabilities
    )
    current_gross_margin = _safe_ratio(inputs.gross_profit, inputs.revenue)
    previous_gross_margin = _safe_ratio(inputs.previous_gross_profit, inputs.previous_revenue)
    current_asset_turnover = _safe_ratio(inputs.revenue, inputs.total_assets)
    previous_asset_turnover = _safe_ratio(inputs.previous_revenue, inputs.previous_total_assets)

    signals: dict[str, int | None] = {
        "positive_return_on_assets": _binary_greater_than(current_return_on_assets, 0.0),
        "positive_operating_cash_flow": _binary_greater_than(inputs.operating_cash_flow, 0.0),
        "improving_return_on_assets": _binary_change_greater_than(
            current_return_on_assets, previous_return_on_assets, 0.0
        ),
        "cash_flow_exceeds_net_income": _binary_greater_than(
            inputs.operating_cash_flow, inputs.net_income
        ),
        "declining_leverage": _binary_change_less_than(current_leverage, previous_leverage, 0.0),
        "improving_current_ratio": _binary_change_greater_than(
            current_liquidity, previous_liquidity, 0.0
        ),
        "no_share_issuance": _binary_change_less_than_or_equal(
            inputs.shares_outstanding, inputs.previous_shares_outstanding, 0.0
        ),
        "improving_gross_margin": _binary_change_greater_than(
            current_gross_margin, previous_gross_margin, 0.0
        ),
        "improving_asset_turnover": _binary_change_greater_than(
            current_asset_turnover, previous_asset_turnover, 0.0
        ),
    }
    if any(signal is None for signal in signals.values()):
        return None, signals
    return int(sum(int(signal) for signal in signals.values() if signal is not None)), signals


def _earnings_volatility(earnings_history: Sequence[float]) -> tuple[float | None, float | None]:
    """Return sample earnings standard deviation and coefficient of variation."""
    if len(earnings_history) < 2:
        return None, None
    earnings_array = np.asarray(earnings_history, dtype=float)
    average_earnings = float(np.mean(earnings_array))
    standard_deviation = float(np.std(earnings_array, ddof=1))
    if np.isclose(average_earnings, 0.0):
        return standard_deviation, None
    return standard_deviation, float(standard_deviation / abs(average_earnings))


def _leverage_trend(leverage_history: Sequence[float]) -> tuple[float | None, str]:
    """Return relative first-to-last debt-to-equity change and qualitative direction."""
    if len(leverage_history) < 2:
        return None, "unavailable"
    first_ratio = float(leverage_history[0])
    last_ratio = float(leverage_history[-1])
    if np.isclose(first_ratio, 0.0):
        absolute_change = last_ratio - first_ratio
        if np.isclose(absolute_change, 0.0):
            return 0.0, "stable"
        return absolute_change, "worsening" if absolute_change > 0 else "improving"
    relative_change = (last_ratio - first_ratio) / abs(first_ratio)
    if abs(relative_change) <= 0.05:
        return float(relative_change), "stable"
    return float(relative_change), "worsening" if relative_change > 0 else "improving"


def _synthetic_score(**metrics: MetricValue) -> tuple[float | None, str, float]:
    """Aggregate available metric signals into a transparent coverage-normalized proxy score."""
    score_points = 0.0
    available_weight = 0.0

    def add_tiered(
        metric: MetricValue,
        weight: float,
        thresholds: Sequence[tuple[float, float]],
        *,
        lower_is_better: bool = False,
    ) -> None:
        """Add one available metric component using ordered credit-quality tiers."""
        nonlocal score_points, available_weight
        if metric is None or not isinstance(metric, (int, float)):
            return
        available_weight += weight
        numeric_metric = float(metric)
        for threshold, fraction in thresholds:
            qualifies = (
                numeric_metric <= threshold if lower_is_better else numeric_metric >= threshold
            )
            if qualifies:
                score_points += weight * fraction
                return

    add_tiered(
        metrics["debt_to_equity"],
        12.0,
        ((0.5, 1.0), (1.0, 0.75), (2.0, 0.40)),
        lower_is_better=True,
    )
    add_tiered(metrics["current_ratio"], 10.0, ((2.0, 1.0), (1.5, 0.80), (1.0, 0.40)))
    add_tiered(metrics["quick_ratio"], 8.0, ((1.0, 1.0), (0.75, 0.50)))
    add_tiered(
        metrics["interest_coverage"], 15.0, ((8.0, 1.0), (4.0, 0.80), (2.0, 0.47), (1.0, 0.20))
    )
    add_tiered(
        metrics["net_debt_to_ebitda"],
        12.0,
        ((1.0, 1.0), (2.5, 0.75), (4.0, 0.33)),
        lower_is_better=True,
    )
    add_tiered(
        metrics["operating_cash_flow_to_total_debt"],
        10.0,
        ((0.30, 1.0), (0.15, 0.70), (0.05, 0.30)),
    )
    add_tiered(metrics["altman_z_score"], 15.0, ((2.99, 1.0), (1.81, 0.53)))
    add_tiered(metrics["piotroski_f_score"], 10.0, ((8.0, 1.0), (6.0, 0.80), (4.0, 0.40)))

    leverage_direction = metrics["leverage_trend"]
    if leverage_direction != "unavailable":
        available_weight += 4.0
        if leverage_direction == "improving":
            score_points += 4.0
        elif leverage_direction == "stable":
            score_points += 2.0

    if available_weight <= 0.0:
        return None, "unavailable", 0.0
    normalized_score = round(100.0 * score_points / available_weight, 2)
    if normalized_score >= 80.0:
        band = "strong_balance_sheet_proxy"
    elif normalized_score >= 65.0:
        band = "moderate_credit_proxy"
    elif normalized_score >= 45.0:
        band = "elevated_credit_risk_proxy"
    else:
        band = "speculative_credit_proxy"
    return normalized_score, band, available_weight


def _safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    """Return a finite ratio only when both values and denominator are usable."""
    if numerator is None or denominator is None:
        return None
    denominator_value = float(denominator)
    if denominator_value <= 0.0:
        return None
    result = float(numerator) / denominator_value
    return result if isfinite(result) else None


def _difference(left: float | None, right: float | None) -> float | None:
    """Return a difference only when both operands are supplied."""
    if left is None or right is None:
        return None
    result = float(left) - float(right)
    return result if isfinite(result) else None


def _binary_greater_than(value: float | None, threshold: float | None) -> int | None:
    """Return a binary signal for a strict comparison, preserving missingness."""
    if value is None or threshold is None:
        return None
    return int(float(value) > float(threshold))


def _binary_change_greater_than(
    current: float | None, previous: float | None, threshold: float
) -> int | None:
    """Return a binary signal for a positive period-over-period change."""
    if current is None or previous is None:
        return None
    return int(float(current) - float(previous) > threshold)


def _binary_change_less_than(
    current: float | None, previous: float | None, threshold: float
) -> int | None:
    """Return a binary signal for a negative period-over-period change."""
    if current is None or previous is None:
        return None
    return int(float(current) - float(previous) < threshold)


def _binary_change_less_than_or_equal(
    current: float | None, previous: float | None, threshold: float
) -> int | None:
    """Return a binary signal for a non-positive period-over-period change."""
    if current is None or previous is None:
        return None
    return int(float(current) - float(previous) <= threshold)


def _normalize_history(values: Sequence[float], field_name: str) -> tuple[float, ...]:
    """Validate and convert a numeric historical sequence to an immutable tuple."""
    normalized_values = tuple(float(value) for value in values)
    if not all(isfinite(value) for value in normalized_values):
        raise ValueError(f"{field_name} must contain only finite values.")
    return normalized_values


def _is_finite_number(value: object) -> bool:
    """Return whether a value can be represented as a finite float."""
    try:
        return isfinite(float(value))
    except (TypeError, ValueError):
        return False


__all__ = [
    "CreditAnalysisInputs",
    "CreditProxyAssessment",
    "CreditScenarioAnalysis",
    "MetricValue",
    "calculate_credit_proxy_metrics",
]
