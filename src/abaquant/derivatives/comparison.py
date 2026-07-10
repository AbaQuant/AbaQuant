"""Cross-model European option comparison.

Purpose
-------
The module evaluates several pricing models with a shared market input set to support model-comparison workflows.

Conventions
-----------
Spot and strike share currency units; maturity is in years; rates, yields, and volatility are annualized decimals.

References
----------
[ 1 ] Black, F., and M. Scholes (1973), "The Pricing of Options and Corporate Liabilities"; Merton, R. C. (1973), "Theory of Rational Option Pricing".
[ 2 ] Cox, J. C., S. A. Ross, and M. Rubinstein (1979), "Option Pricing: A Simplified Approach".
[ 3 ] Heston, S. L. (1993), "A Closed-Form Solution for Options with Stochastic Volatility".
[ 4 ] Merton, R. C. (1976), "Option Pricing When Underlying Stock Returns Are Discontinuous".
"""

from __future__ import annotations

from .models.binomial import CoxRossRubinsteinModel
from .models.black_scholes import BlackScholesMertonModel
from .models.heston import HestonStochasticVolatilityModel
from .models.merton import MertonJumpDiffusionModel


def compare_all_models(
    S,
    K,
    T,
    r,
    sigma,
    q=0.0,
    heston_params=None,
    merton_params=None,
    crr_N=200,
    crr_american=False,
):
    """Price a vanilla option under several models using shared market inputs.

    Parameters
    ----------
    S, K, T, r, sigma : float
        Legacy formula notation for spot price, strike price, maturity in
        years, continuously compounded risk-free rate, and annualized decimal
        volatility. The canonical model constructors use descriptive names.
    q : float, default=0.0
        Continuous annual dividend or carry yield in decimal units.
    heston_params : mapping[str, float] or None, default=None
        Optional Heston parameters. Accepted legacy keys are ``"v0"``,
        ``"kappa"``, ``"theta"``, ``"xi"``, and ``"rho"``. When omitted,
        the comparison applies the module's deterministic illustrative values.
    merton_params : mapping[str, float] or None, default=None
        Optional jump-diffusion parameters. Accepted legacy keys are
        ``"lam"``, ``"mu_j"``, and ``"sigma_j"``.
    crr_N : int, default=200
        Number of Cox--Ross--Rubinstein lattice steps.
    crr_american : bool, default=False
        Whether the binomial price applies early-exercise logic.

    Returns
    -------
    dict[str, dict[str, float]]
        Mapping from model label to call and put values. The legacy result keys
        ``"BSM"``, ``"CRR"``, ``"Heston"``, and ``"Merton"`` are preserved
        for backward compatibility.

    Notes
    -----
    This is a valuation comparison, not a calibration routine. Default Heston
    and Merton parameters are illustrative and should not be interpreted as
    market-calibrated estimates.
    """
    spot_price = S
    strike_price = K
    maturity_years = T
    risk_free_rate = r
    volatility = sigma
    dividend_yield = q
    number_of_tree_steps = crr_N
    allow_early_exercise = crr_american

    model_prices: dict[str, dict[str, float]] = {}

    black_scholes_model = BlackScholesMertonModel(
        spot_price=spot_price,
        strike_price=strike_price,
        maturity_years=maturity_years,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=dividend_yield,
    )
    model_prices["BSM"] = {
        "call": black_scholes_model.call_price(),
        "put": black_scholes_model.put_price(),
    }

    cox_ross_rubinstein_model = CoxRossRubinsteinModel(
        spot_price=spot_price,
        strike_price=strike_price,
        maturity_years=maturity_years,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=dividend_yield,
        number_of_steps=number_of_tree_steps,
        allow_early_exercise=allow_early_exercise,
    )
    model_prices["CRR"] = {
        "call": cox_ross_rubinstein_model.call_price(),
        "put": cox_ross_rubinstein_model.put_price(),
    }

    if heston_params is None:
        heston_parameters = {
            "v0": volatility**2,
            "kappa": 2.0,
            "theta": volatility**2,
            "xi": 0.3,
            "rho": -0.7,
        }
    else:
        heston_parameters = heston_params
    heston_model = HestonStochasticVolatilityModel(
        spot_price=spot_price,
        strike_price=strike_price,
        maturity_years=maturity_years,
        risk_free_rate=risk_free_rate,
        dividend_yield=dividend_yield,
        initial_variance=heston_parameters["v0"],
        variance_mean_reversion_speed=heston_parameters["kappa"],
        long_run_variance=heston_parameters["theta"],
        volatility_of_variance=heston_parameters["xi"],
        price_variance_correlation=heston_parameters["rho"],
    )
    model_prices["Heston"] = {
        "call": heston_model.call_price(),
        "put": heston_model.put_price(),
    }

    if merton_params is None:
        jump_diffusion_parameters = {
            "lam": 1.0,
            "mu_j": -0.1,
            "sigma_j": 0.15,
        }
    else:
        jump_diffusion_parameters = merton_params
    merton_jump_diffusion_model = MertonJumpDiffusionModel(
        spot_price=spot_price,
        strike_price=strike_price,
        maturity_years=maturity_years,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=dividend_yield,
        jump_intensity=jump_diffusion_parameters["lam"],
        mean_log_jump_size=jump_diffusion_parameters["mu_j"],
        jump_log_volatility=jump_diffusion_parameters["sigma_j"],
    )
    model_prices["Merton"] = {
        "call": merton_jump_diffusion_model.call_price(),
        "put": merton_jump_diffusion_model.put_price(),
    }

    return model_prices
