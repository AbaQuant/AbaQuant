"""Merton jump-diffusion option pricing model.

Purpose
-------
The module values European calls and puts by a truncated Poisson mixture of Black--Scholes--Merton terms and generates an implied-volatility smile.

Conventions
-----------
lam is the jump intensity per year; mu_j and sigma_j parameterize log-jump size; n_terms controls truncation.

References
----------
[ 1 ] Merton, R. C. (1976), "Option Pricing When Underlying Stock Returns Are Discontinuous".
"""

from __future__ import annotations

import math

import numpy as np

from .black_scholes import BlackScholesMertonModel
from .diagnostics import OptionDiagnosticsMixin


class MertonJumpDiffusionModel(OptionDiagnosticsMixin):
    """Merton jump-diffusion model for European vanilla options.

    Parameters
    ----------
    spot_price : float
        Current underlying asset price in currency units.
    strike_price : float
        Option exercise price in currency units.
    maturity_years : float
        Time to expiration in years.
    risk_free_rate : float
        Continuously compounded annual risk-free rate in decimal units.
    volatility : float
        Diffusion volatility in annualized decimal units.
    dividend_yield : float, default=0.0
        Continuous annual dividend or carry yield in decimal units.
    jump_intensity : float, default=1.0
        Poisson jump arrival intensity in events per year.
    mean_log_jump_size : float, default=0.0
        Mean jump size in log-price units.
    jump_log_volatility : float, default=0.2
        Standard deviation of log jump sizes.
    poisson_series_terms : int, default=50
        Number of terms retained in the Poisson-mixture approximation.
    """

    def __init__(
        self,
        spot_price,
        strike_price,
        maturity_years,
        risk_free_rate,
        volatility,
        dividend_yield=0.0,
        jump_intensity=1.0,
        mean_log_jump_size=0.0,
        jump_log_volatility=0.2,
        poisson_series_terms=50,
    ):
        """Initialize the Merton jump-diffusion model state.

        Parameters
        ----------
        spot_price : float
            Current underlying asset price in currency units.
        strike_price : float
            Option exercise price in currency units.
        maturity_years : float
            Time to expiration in years.
        risk_free_rate : float
            Continuously compounded annual risk-free rate in decimal units.
        volatility : float
            Diffusion volatility in annualized decimal units.
        dividend_yield : float, default=0.0
            Continuous annual dividend or carry yield in decimal units.
        jump_intensity : float, default=1.0
            Poisson jump arrival intensity in events per year.
        mean_log_jump_size : float, default=0.0
            Mean jump size in log-price units.
        jump_log_volatility : float, default=0.2
            Standard deviation of log jump sizes.
        poisson_series_terms : int, default=50
            Number of terms retained in the Poisson-mixture approximation.
        """
        self.spot_price = spot_price
        self.strike_price = strike_price
        self.maturity_years = maturity_years
        self.risk_free_rate = risk_free_rate
        self.volatility = volatility
        self.dividend_yield = dividend_yield
        self.jump_intensity = jump_intensity  # jump intensity (jumps per year)
        self.mean_log_jump_size = mean_log_jump_size  # mean log-jump size
        self.jump_log_volatility = jump_log_volatility  # jump vol
        self.poisson_series_terms = poisson_series_terms

    def _kappa(self):
        """Perform an internal calculation used by the documented public workflow.

        Returns
        -------
        object
            Result of the  kappa workflow.
        """
        return np.exp(self.mean_log_jump_size + 0.5 * self.jump_log_volatility**2) - 1

    def price(self, option_type="call"):
        """Return the model price of a call or put option.

        Parameters
        ----------
        option_type : str, default='call'
            Option type label, normally ``"call"`` or ``"put"``.

        Returns
        -------
        float
            Computed price in the units implied by the documented inputs.

        Notes
        -----
        Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
        """
        kappa = self._kappa()
        lam_prime = self.jump_intensity * (1 + kappa)
        total = 0.0

        for n in range(self.poisson_series_terms):
            # Poisson weight under lambda' = lambda(1+kappa)
            poisson_w = (
                np.exp(-lam_prime * self.maturity_years)
                * (lam_prime * self.maturity_years) ** n
                / math.factorial(n)
            )
            if poisson_w < 1e-15:
                break

            # Adjusted vol for n jumps
            sigma_n = np.sqrt(
                self.volatility**2 + n * self.jump_log_volatility**2 / self.maturity_years
            )

            # Adjusted rate: compensate for jump drift so risk-neutral condition holds
            r_n = (
                self.risk_free_rate
                - self.jump_intensity * kappa
                + n
                * (self.mean_log_jump_size + 0.5 * self.jump_log_volatility**2)
                / self.maturity_years
            )

            bsm = BlackScholesMertonModel(
                self.spot_price,
                self.strike_price,
                self.maturity_years,
                r_n,
                sigma_n,
                self.dividend_yield,
            )
            price_n = bsm.call_price() if option_type == "call" else bsm.put_price()
            total += poisson_w * price_n

        return total

    def call_price(self):
        """Return the model price of a European call option.

        Returns
        -------
        float
            Computed call price in the units implied by the documented inputs.

        Notes
        -----
        Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
        """
        return self.price("call")

    def put_price(self):
        """Return the model price of a European put option.

        Returns
        -------
        float
            Computed put price in the units implied by the documented inputs.

        Notes
        -----
        Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
        """
        return self.price("put")

    def vol_smile(self, strikes):
        """Evaluate the model-implied volatility across the supplied strike grid.

        Parameters
        ----------
        strikes : float or array-like
            Strike-price grid in the same currency units as the underlying or forward.

        Returns
        -------
        numpy.ndarray
            Numeric array ordered consistently with the supplied strikes, time grid, assets, or state labels.

        Notes
        -----
        Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
        """
        ivs = []
        for K in strikes:
            eng_m = MertonJumpDiffusionModel(
                self.spot_price,
                K,
                self.maturity_years,
                self.risk_free_rate,
                self.volatility,
                self.dividend_yield,
                self.jump_intensity,
                self.mean_log_jump_size,
                self.jump_log_volatility,
                self.poisson_series_terms,
            )
            price = eng_m.call_price()
            bsm = BlackScholesMertonModel(
                self.spot_price,
                K,
                self.maturity_years,
                self.risk_free_rate,
                0.3,
                self.dividend_yield,
            )
            iv = bsm.implied_vol(price, "call")
            ivs.append(iv)
        return np.array(ivs)

    def visualize(
        self,
        *,
        option_type: str = "call",
        chart: str = "payoff",
        backend: str | None = None,
        theme=None,
        save_path=None,
        filename=None,
        lower_spot_multiple: float = 0.5,
        upper_spot_multiple: float = 1.5,
        grid_size: int = 101,
        lower_volatility_multiple: float = 0.5,
        upper_volatility_multiple: float = 1.5,
        volatility_grid_size: int = 31,
        greek_scale: str = "raw",
    ):
        """Return a backend-native visualization of this option-pricing model.

        Parameters
        ----------
        option_type : {"call", "put"}, default="call"
            Vanilla option type used for payoff, price-profile, smile, or tree plots.
        chart : str, default="payoff"
            Visual diagnostic to create. Supported charts include payoff,
            price profile, extrinsic value, Greek curves, selected surfaces,
            volatility smile, and lattice tree when the model exposes a tree.
        backend : {"matplotlib", "plotly"}, default="matplotlib"
            Optional plotting backend. The returned figure is not shown automatically.
        lower_spot_multiple, upper_spot_multiple : float, default=0.5, 1.5
            Price-grid bounds as multiples of the strike price.
        grid_size : int, default=101
            Number of spot-grid points for non-tree plots.
        lower_volatility_multiple, upper_volatility_multiple : float, default=0.5, 1.5
            Volatility-grid bounds expressed as multiples of the model's base volatility.
        volatility_grid_size : int, default=31
            Number of volatility-grid points for surface plots.
        greek_scale : {"raw", "standardized"}, default="raw"
            Scaling mode for the multi-Greek curve chart.

        Returns
        -------
        matplotlib.figure.Figure or plotly.graph_objects.Figure
            Figure object created without mutating model state.
        """
        from abaquant.visualization import visualize_option_model

        return visualize_option_model(
            self,
            option_type=option_type,
            chart=chart,
            backend=backend,
            theme=theme,
            save_path=save_path,
            filename=filename,
            lower_spot_multiple=lower_spot_multiple,
            upper_spot_multiple=upper_spot_multiple,
            grid_size=grid_size,
            lower_volatility_multiple=lower_volatility_multiple,
            upper_volatility_multiple=upper_volatility_multiple,
            volatility_grid_size=volatility_grid_size,
            greek_scale=greek_scale,
        )


def merton_jump_statistics(
    lam: float, mu_j: float, sigma_j: float, sigma: float
) -> dict[str, float]:
    """Compute summary statistics implied by the Merton jump-diffusion parameters.

    Parameters
    ----------
    lam : float
        Jump intensity in expected jumps per year.
    mu_j : float
        Mean log jump size in the Merton jump-diffusion model.
    sigma_j : float
        Standard deviation of log jump size in decimal units.
    sigma : float
        Annualized lognormal volatility in decimal units; for example, ``0.20`` denotes 20%.

    Returns
    -------
    dict[str, object]
        Dictionary of named model outputs, metrics, or workflow results defined by the current public schema.
    """
    kappa_j = np.exp(mu_j + 0.5 * sigma_j**2) - 1.0
    return {
        "kappa_j": float(kappa_j),
        "mean_jump_pct": float(100.0 * kappa_j),
        "lambda_adjusted": float(lam * (1.0 + kappa_j)),
        "bsm_total_sigma": float(np.sqrt(sigma**2 + lam * sigma_j**2)),
    }
