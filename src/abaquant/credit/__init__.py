"""Public credit-risk interface.

Purpose
-------
The package exposes rating-transition, bond-valuation, portfolio-distribution, copula, CDO, CDS, and risk-measure primitives.

Conventions
-----------
Credit-state ordering, recovery assumptions, rate conventions, and loss signs are documented by the relevant callable.

References
----------
[ 1 ] Merton, R. C. (1974), "On the Pricing of Corporate Debt: The Risk Structure of Interest Rates".
[ 2 ] Li, D. X. (2000), "On Default Correlation: A Copula Function Approach".
[ 3 ] Jarrow, R. A., and S. M. Turnbull (1995), "Pricing Derivatives on Financial Securities Subject to Credit Risk".
"""

from .cdo import (
    binomial_probabilities_log,
    conditional_default_probability,
    expected_tranche_survival_given_factor,
    gauss_hermite_normal,
    log_binomial_coefficient,
    value_tranche,
)
from .cds import (
    cds_accrued_premium_table,
    cds_contingent_leg_table,
    cds_fair_spread,
    cds_premium_leg_table,
    cds_probability_table,
    value_cds,
)
from .copula import gaussian_copula_simulation, thresholds_per_bond
from .data import (
    DEFAULT_SPREADS,
    DEFAULT_TREASURY,
    ISSUER_RATINGS,
    N_DEST,
    N_ISSUER_RATINGS,
    NR_METHODS,
    RATING_IDX,
    RATINGS_DEST,
    TRADING_DAYS,
    VALUATION_RATINGS,
    _TM_RAW_17x19,
)
from .distribution import expected_value_and_sigma, independent_distribution
from .fundamentals import (
    BalanceSheetInputs,
    CashFlowInputs,
    CreditAnalysisInputs,
    CreditHistoricalSeries,
    CreditProxyAssessment,
    CreditScenarioAnalysis,
    IncomeStatementInputs,
    MarketEquityObservation,
    MetricValue,
    PriorPeriodInputs,
    ReportedValue,
    calculate_credit_proxy_metrics,
)
from .risk import (
    scale_var_cvar,
    var_cvar_from_distribution,
    var_cvar_from_simulations,
    var_cvar_parametric,
)
from .transitions import _TM_SIZE_BY_MODE, DEFAULT_TM, RATINGS_NO_D, build_transition_matrix
from .types import BondData, Distribution, RiskResult, RiskResults
from .valuation import bond_values_per_rating

__all__ = [
    "DEFAULT_SPREADS",
    "DEFAULT_TM",
    "DEFAULT_TREASURY",
    "ISSUER_RATINGS",
    "NR_METHODS",
    "N_DEST",
    "N_ISSUER_RATINGS",
    "RATINGS_DEST",
    "RATINGS_NO_D",
    "RATING_IDX",
    "TRADING_DAYS",
    "VALUATION_RATINGS",
    "_TM_SIZE_BY_MODE",
    "BalanceSheetInputs",
    "BondData",
    "CashFlowInputs",
    "CreditAnalysisInputs",
    "CreditHistoricalSeries",
    "CreditProxyAssessment",
    "CreditScenarioAnalysis",
    "Distribution",
    "IncomeStatementInputs",
    "MarketEquityObservation",
    "MetricValue",
    "PriorPeriodInputs",
    "ReportedValue",
    "RiskResult",
    "RiskResults",
    "_TM_RAW_17x19",
    "binomial_probabilities_log",
    "bond_values_per_rating",
    "build_transition_matrix",
    "calculate_credit_proxy_metrics",
    "cds_accrued_premium_table",
    "cds_contingent_leg_table",
    "cds_fair_spread",
    "cds_premium_leg_table",
    "cds_probability_table",
    "conditional_default_probability",
    "expected_tranche_survival_given_factor",
    "expected_value_and_sigma",
    "gauss_hermite_normal",
    "gaussian_copula_simulation",
    "independent_distribution",
    "log_binomial_coefficient",
    "scale_var_cvar",
    "thresholds_per_bond",
    "value_cds",
    "value_tranche",
    "var_cvar_from_distribution",
    "var_cvar_from_simulations",
    "var_cvar_parametric",
]
