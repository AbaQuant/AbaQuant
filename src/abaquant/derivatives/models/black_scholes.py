"""Black--Scholes--Merton analytical option pricing model.

Purpose
-------
The module implements European call and put prices, standard Greeks, implied-volatility inversion, and simple smile diagnostics under constant lognormal volatility.

Conventions
-----------
Maturity is in years. Rates and continuous dividend yield are continuously compounded decimal annual rates. Volatility is annualized decimal volatility.

References
----------
[ 1 ] Black, F., and M. Scholes (1973), "The Pricing of Options and Corporate Liabilities"; Merton, R. C. (1973), "Theory of Rational Option Pricing".
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm

from ..numerics.implied_volatility import implied_volatility_black_scholes
from .diagnostics import OptionDiagnosticsMixin


class BlackScholesMertonModel(OptionDiagnosticsMixin):
    """Analytical Black--Scholes--Merton model for European vanilla options.

    Parameters
    ----------
    spot_price : float or array-like
        Current underlying asset price in currency units.
    strike_price : float or array-like
        Option exercise price in the same currency units as ``spot_price``.
    maturity_years : float or array-like
        Remaining time to expiry, measured in years.
    risk_free_rate : float or array-like
        Continuously compounded annual risk-free rate in decimal units.
    volatility : float or array-like
        Annualized lognormal volatility in decimal units.
    dividend_yield : float or array-like, default=0.0
        Continuously compounded annual dividend or carry yield in decimal units.

    Attributes
    ----------
    spot_price, strike_price, maturity_years, risk_free_rate, volatility, dividend_yield
        Canonical descriptive model inputs. Legacy textbook-symbol attributes such
        as ``S`` and ``sigma`` remain available for backward compatibility.
    """

    def __init__(
        self,
        spot_price,
        strike_price,
        maturity_years,
        risk_free_rate,
        volatility,
        dividend_yield=0.0,
    ):
        """Initialize the Black--Scholes--Merton model state.

        Parameters
        ----------
        spot_price : float or array-like
            Current underlying asset price in currency units.
        strike_price : float or array-like
            Option exercise price in the same currency units as ``spot_price``.
        maturity_years : float or array-like
            Remaining time to expiry, measured in years.
        risk_free_rate : float or array-like
            Continuously compounded annual risk-free rate in decimal units.
        volatility : float or array-like
            Annualized lognormal volatility in decimal units.
        dividend_yield : float or array-like, default=0.0
            Continuously compounded annual dividend or carry yield in decimal units.
        """
        self.spot_price = spot_price
        self.strike_price = strike_price
        self.maturity_years = maturity_years
        self.risk_free_rate = risk_free_rate
        self.volatility = volatility
        self.dividend_yield = dividend_yield

    def _d1(self):
        """Compute the internal standardized pricing statistic used by the model.

        Returns
        -------
        object
            Result of the  d1 workflow.
        """
        if self.maturity_years <= 0 or self.volatility <= 0:
            return 0.0
        return (
            np.log(self.spot_price / self.strike_price)
            + (self.risk_free_rate - self.dividend_yield + 0.5 * self.volatility**2)
            * self.maturity_years
        ) / (self.volatility * np.sqrt(self.maturity_years))

    def _d2(self):
        """Compute the internal standardized pricing statistic used by the model.

        Returns
        -------
        object
            Result of the  d2 workflow.
        """
        return self._d1() - self.volatility * np.sqrt(self.maturity_years)

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
        if self.maturity_years <= 0:
            return max(self.spot_price - self.strike_price, 0.0)
        d1, d2 = self._d1(), self._d2()
        return self.spot_price * np.exp(-self.dividend_yield * self.maturity_years) * norm.cdf(
            d1
        ) - self.strike_price * np.exp(-self.risk_free_rate * self.maturity_years) * norm.cdf(d2)

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
        if self.maturity_years <= 0:
            return max(self.strike_price - self.spot_price, 0.0)
        d1, d2 = self._d1(), self._d2()
        return self.strike_price * np.exp(-self.risk_free_rate * self.maturity_years) * norm.cdf(
            -d2
        ) - self.spot_price * np.exp(-self.dividend_yield * self.maturity_years) * norm.cdf(-d1)

    def greeks(self):
        """Return the model sensitivities implemented by this model.

        Returns
        -------
        object
            Result of the greeks workflow.

        Notes
        -----
        Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
        """
        d1, d2 = self._d1(), self._d2()
        sqrtT = np.sqrt(self.maturity_years) if self.maturity_years > 0 else 1e-10
        pdf_d1 = norm.pdf(d1)
        cdf_d1 = norm.cdf(d1)
        cdf_d2 = norm.cdf(d2)

        discount = np.exp(-self.risk_free_rate * self.maturity_years)
        div_disc = np.exp(-self.dividend_yield * self.maturity_years)

        #  Delta
        call_delta = div_disc * cdf_d1
        put_delta = div_disc * (cdf_d1 - 1)

        #  Gamma
        gamma = div_disc * pdf_d1 / (self.spot_price * self.volatility * sqrtT)

        #  Theta (per calendar day)
        call_theta = (
            -(self.spot_price * div_disc * pdf_d1 * self.volatility) / (2 * sqrtT)
            - self.risk_free_rate * self.strike_price * discount * cdf_d2
            + self.dividend_yield * self.spot_price * div_disc * cdf_d1
        ) / 365

        put_theta = (
            -(self.spot_price * div_disc * pdf_d1 * self.volatility) / (2 * sqrtT)
            + self.risk_free_rate * self.strike_price * discount * norm.cdf(-d2)
            - self.dividend_yield * self.spot_price * div_disc * norm.cdf(-d1)
        ) / 365

        #  Vega (per 1% move in vol)
        vega = self.spot_price * div_disc * pdf_d1 * sqrtT / 100

        #  Rho (per 1% move in rate)
        call_rho = self.strike_price * self.maturity_years * discount * cdf_d2 / 100
        put_rho = -self.strike_price * self.maturity_years * discount * norm.cdf(-d2) / 100

        #  Vanna
        vanna = -div_disc * pdf_d1 * d2 / self.volatility

        #  Volga / Vomma
        volga = self.spot_price * div_disc * pdf_d1 * sqrtT * d1 * d2 / self.volatility

        #  Charm (delta decay per day)
        call_charm = (
            div_disc
            * (
                pdf_d1 * (self.risk_free_rate - self.dividend_yield) / (self.volatility * sqrtT)
                - d2 / (2 * self.maturity_years) * pdf_d1
            )
        ) / 365

        return {
            "call_delta": call_delta,
            "put_delta": put_delta,
            "gamma": gamma,
            "call_theta": call_theta,
            "put_theta": put_theta,
            "vega": vega,
            "call_rho": call_rho,
            "put_rho": put_rho,
            "vanna": vanna,
            "volga": volga,
            "call_charm": call_charm,
        }

    def implied_vol(self, market_price, option_type="call", tol=1e-6, max_iter=200):
        """Return the Black--Scholes--Merton implied volatility associated with the model price.

        Parameters
        ----------
        market_price : float or array-like
            Observed option premium in the same currency units as spot and strike.
        option_type : str, default='call'
            Option type label, normally ``"call"`` or ``"put"``.
        tol : float, default=1e-06
            Numerical convergence tolerance.
        max_iter : int, default=200
            Maximum numerical-optimizer or root-finder iterations.

        Returns
        -------
        object
            Result of the implied vol workflow.

        Notes
        -----
        Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
        """
        return implied_volatility_black_scholes(
            market_price,
            self.spot_price,
            self.strike_price,
            self.maturity_years,
            self.risk_free_rate,
            self.dividend_yield,
            option_type,
            tol,
            max_iter,
        )

    def vol_smile_surface(self, strikes, maturities):
        """Evaluate the model-implied volatility across strike and maturity grids.

        Parameters
        ----------
        strikes : float or array-like
            Strike-price grid in the same currency units as the underlying or forward.
        maturities : float or array-like
            Maturity grid in years for a volatility-surface calculation.

        Returns
        -------
        pandas.DataFrame
            Tabular result with the index, column schema, units, and missing-value treatment defined by the module convention.

        Notes
        -----
        Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
        """
        surface = np.full((len(maturities), len(strikes)), self.volatility)
        return surface

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


def bsm_d1_d2_summary(
    S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0
) -> dict[str, float]:
    """Compute the result defined by ``bsm_d1_d2_summary`` under this module's documented convention.

    Parameters
    ----------
    S : float
        Current underlying spot price in currency units.
    K : float
        Option strike price in the same currency units as the underlying.
    T : float
        Time to maturity in years.
    r : float
        Continuously compounded risk-free annual rate in decimal units.
    sigma : float
        Annualized lognormal volatility in decimal units; for example, ``0.20`` denotes 20%.
    q : float, default=0.0
        Continuous dividend or carry yield in decimal annual units.

    Returns
    -------
    dict[str, float]
        Named ``d1`` and ``d2`` diagnostics for the stated Black--Scholes--Merton inputs.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """
    if T <= 0 or sigma <= 0:
        return {"d1": 0.0, "d2": 0.0}
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return {"d1": float(d1), "d2": float(d2)}
