"""Monte Carlo Black--Scholes--Merton option valuation.

Purpose
-------
The module simulates lognormal terminal prices and estimates European option values with optional variance-reduction techniques.

Conventions
-----------
Maturity is in years; rates, yields, and volatility are decimal annual values; n_paths is the number of simulated paths.

References
----------
[ 1 ] Glasserman, P. (2004), Monte Carlo Methods in Financial Mathematics.
[ 2 ] Black, F., and M. Scholes (1973), "The Pricing of Options and Corporate Liabilities"; Merton, R. C. (1973), "Theory of Rational Option Pricing".
"""

from __future__ import annotations

import numpy as np

from .models.black_scholes import BlackScholesMertonModel
from .validation import validate_option_type


def monte_carlo_bsm(
    S,
    K,
    T,
    r,
    sigma,
    q=0.0,
    option_type="call",
    n_paths=50_000,
    seed=42,
    antithetic=True,
    control_variate=True,
):
    """Estimate a European option value with Black--Scholes--Merton simulation.

    Parameters
    ----------
    S : float
        Legacy formula notation for the current spot price. New class-based
        workflows expose this input as ``spot_price``.
    K : float
        Legacy formula notation for the option strike price.
    T : float
        Legacy formula notation for maturity in years.
    r : float
        Legacy formula notation for the continuously compounded annual
        risk-free rate in decimal units.
    sigma : float
        Legacy formula notation for annualized lognormal volatility in decimal
        units; for example, ``0.20`` denotes 20% annualized volatility.
    q : float, default=0.0
        Continuous annual dividend or carry yield in decimal units.
    option_type : {"call", "put"}, default="call"
        Option payoff to simulate.
    n_paths : int, default=50000
        Requested number of terminal-price paths. With antithetic variates,
        the effective path count equals the generated draw count.
    seed : int or None, default=42
        Seed passed to NumPy's random-number generator. Use ``None`` for a
        non-reproducible stream.
    antithetic : bool, default=True
        Whether each standard-normal draw is paired with its negative.
    control_variate : bool, default=True
        Whether discounted terminal underlying value is used as a control
        variate with known expectation ``S * exp(-q * T)``.

    Returns
    -------
    dict[str, float | int]
        Dictionary with these fields:

        - ``"price"``: Monte Carlo option-value estimate.
        - ``"std_error"``: estimated standard error of the final estimator.
        - ``"ci_95_lo"`` and ``"ci_95_hi"``: normal-approximation 95%
          confidence interval.
        - ``"n_paths"``: requested simulation path count.
        - ``"bsm_price"``: analytical Black--Scholes--Merton benchmark.
        - ``"error_vs_bsm"``: absolute difference from that benchmark.

    Notes
    -----
    The routine simulates only terminal prices and therefore values European
    payoffs. It does not support path-dependent or early-exercise features.
    The short public parameter names are retained for formula familiarity and
    backward compatibility; all internal state uses descriptive identifiers.

    References
    ----------
    Glasserman, P. (2004). *Monte Carlo Methods in Financial Mathematics*.
    """
    validate_option_type(option_type)

    # Keep the established formula signature while using explicit internal
    # names throughout the simulation and reporting workflow.
    spot_price = S
    strike_price = K
    maturity_years = T
    risk_free_rate = r
    volatility = sigma
    dividend_yield = q
    requested_path_count = n_paths

    random_number_generator = np.random.default_rng(seed)
    if antithetic:
        base_draw_count = requested_path_count // 2
        standard_normal_draws = random_number_generator.standard_normal(base_draw_count)
        antithetic_draws = np.concatenate([standard_normal_draws, -standard_normal_draws])
        if len(antithetic_draws) < requested_path_count:
            antithetic_draws = np.concatenate(
                [antithetic_draws, random_number_generator.standard_normal(1)]
            )
        standard_normal_draws = antithetic_draws
    else:
        standard_normal_draws = random_number_generator.standard_normal(requested_path_count)

    effective_path_count = len(standard_normal_draws)
    terminal_underlying_prices = spot_price * np.exp(
        (risk_free_rate - dividend_yield - 0.5 * volatility**2) * maturity_years
        + volatility * np.sqrt(maturity_years) * standard_normal_draws
    )
    analytical_pricer = BlackScholesMertonModel(
        spot_price=spot_price,
        strike_price=strike_price,
        maturity_years=maturity_years,
        risk_free_rate=risk_free_rate,
        volatility=volatility,
        dividend_yield=dividend_yield,
    )
    if option_type == "call":
        option_payoffs = np.maximum(terminal_underlying_prices - strike_price, 0.0)
        analytical_benchmark_price = analytical_pricer.call_price()
    else:
        option_payoffs = np.maximum(strike_price - terminal_underlying_prices, 0.0)
        analytical_benchmark_price = analytical_pricer.put_price()

    discounted_option_payoffs = np.exp(-risk_free_rate * maturity_years) * option_payoffs
    if control_variate:
        discounted_terminal_prices = (
            np.exp(-risk_free_rate * maturity_years) * terminal_underlying_prices
        )
        expected_discounted_terminal_price = spot_price * np.exp(-dividend_yield * maturity_years)
        control_variate_variance = np.var(discounted_terminal_prices, ddof=1)
        control_variate_coefficient = (
            np.cov(discounted_option_payoffs, discounted_terminal_prices, ddof=1)[0, 1]
            / control_variate_variance
            if control_variate_variance > 0.0
            else 0.0
        )
        pricing_estimator = discounted_option_payoffs - control_variate_coefficient * (
            discounted_terminal_prices - expected_discounted_terminal_price
        )
    else:
        pricing_estimator = discounted_option_payoffs

    estimated_option_price = float(np.mean(pricing_estimator))
    estimated_standard_error = float(
        np.std(pricing_estimator, ddof=1) / np.sqrt(effective_path_count)
    )
    normal_95_critical_value = 1.96
    return {
        "price": estimated_option_price,
        "std_error": estimated_standard_error,
        "ci_95_lo": float(
            estimated_option_price - normal_95_critical_value * estimated_standard_error
        ),
        "ci_95_hi": float(
            estimated_option_price + normal_95_critical_value * estimated_standard_error
        ),
        "n_paths": requested_path_count,
        "bsm_price": float(analytical_benchmark_price),
        "error_vs_bsm": float(abs(estimated_option_price - analytical_benchmark_price)),
    }
