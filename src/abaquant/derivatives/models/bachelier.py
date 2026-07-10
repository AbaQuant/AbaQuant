"""Bachelier normal-volatility option pricing.

Purpose
-------
The module implements European option prices and Greeks under a normally distributed discounted underlying.

Conventions
-----------
Normal volatility has price units per square-root year. Rates and continuous dividend yields are decimal annual rates; maturity is in years.

References
----------
[ 1 ] Bachelier, L. (1900), "Theorie de la Speculation".
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm

from ..numerics.implied_volatility import implied_normal_volatility
from .black_scholes import BlackScholesMertonModel
from .diagnostics import OptionDiagnosticsMixin


class NormalBachelierModel(OptionDiagnosticsMixin):
    """Bachelier normal-volatility model for European vanilla options.

    Parameters
    ----------
    spot_price : float or array-like
        Current underlying asset price in currency units.
    strike_price : float or array-like
        Option exercise price in currency units.
    maturity_years : float or array-like
        Time to expiration in years.
    risk_free_rate : float or array-like
        Continuously compounded annual risk-free rate in decimal units.
    normal_volatility : float or array-like
        Annualized normal volatility in price units per square-root year.
    dividend_yield : float, default=0.0
        Continuously compounded annual dividend or carry yield in decimal units.
    """

    def __init__(
        self,
        spot_price,
        strike_price,
        maturity_years,
        risk_free_rate,
        normal_volatility,
        dividend_yield=0.0,
    ):
        """Initialize the Bachelier normal-volatility model state.

        Parameters
        ----------
        spot_price : float or array-like
            Current underlying asset price in currency units.
        strike_price : float or array-like
            Option exercise price in currency units.
        maturity_years : float or array-like
            Time to expiration in years.
        risk_free_rate : float or array-like
            Continuously compounded annual risk-free rate in decimal units.
        normal_volatility : float or array-like
            Annualized normal volatility in price units per square-root year.
        dividend_yield : float, default=0.0
            Continuously compounded annual dividend or carry yield in decimal units.
        """
        self.spot_price = spot_price
        self.strike_price = strike_price
        self.maturity_years = maturity_years
        self.risk_free_rate = risk_free_rate
        self.normal_volatility = normal_volatility
        self.dividend_yield = dividend_yield

    def _d(self):
        """Compute the internal standardized pricing statistic used by the model.

        Returns
        -------
        object
            Result of the  d workflow.
        """
        if self.maturity_years <= 0 or self.normal_volatility <= 0:
            return 0.0
        return (
            self.spot_price * np.exp(-self.dividend_yield * self.maturity_years)
            - self.strike_price * np.exp(-self.risk_free_rate * self.maturity_years)
        ) / (self.normal_volatility * np.sqrt(self.maturity_years))

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
        F = self.spot_price * np.exp(
            (self.risk_free_rate - self.dividend_yield) * self.maturity_years
        )
        vol = self.normal_volatility * np.sqrt(self.maturity_years)
        d = (F - self.strike_price) / vol
        return np.exp(-self.risk_free_rate * self.maturity_years) * (
            (F - self.strike_price) * norm.cdf(d) + vol * norm.pdf(d)
        )

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
        F = self.spot_price * np.exp(
            (self.risk_free_rate - self.dividend_yield) * self.maturity_years
        )
        vol = self.normal_volatility * np.sqrt(self.maturity_years)
        d = (F - self.strike_price) / vol
        return np.exp(-self.risk_free_rate * self.maturity_years) * (
            (self.strike_price - F) * norm.cdf(-d) + vol * norm.pdf(d)
        )

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
        F = self.spot_price * np.exp(
            (self.risk_free_rate - self.dividend_yield) * self.maturity_years
        )
        vol = self.normal_volatility * np.sqrt(self.maturity_years)
        d = (F - self.strike_price) / vol if vol > 0 else 0.0
        disc = np.exp(-self.risk_free_rate * self.maturity_years)

        call_delta = disc * norm.cdf(d)
        put_delta = disc * (norm.cdf(d) - 1)
        gamma = (
            disc * norm.pdf(d) / (self.normal_volatility * np.sqrt(self.maturity_years))
            if self.maturity_years > 0
            else 0.0
        )
        vega = disc * np.sqrt(self.maturity_years) * norm.pdf(d)  # per unit sigma_n
        call_theta = (
            (
                -disc * self.normal_volatility * norm.pdf(d) / (2 * np.sqrt(self.maturity_years))
                - self.risk_free_rate * self.call_price()
            )
            / 365
            if self.maturity_years > 0
            else 0.0
        )

        return {
            "call_delta": call_delta,
            "put_delta": put_delta,
            "gamma": gamma,
            "vega": vega,
            "call_theta": call_theta,
        }

    def implied_normal_vol(self, market_price, option_type="call", tol=1e-8):
        """Return the Bachelier normal implied volatility associated with the model price.

        Parameters
        ----------
        market_price : float or array-like
            Observed option premium in the same currency units as spot and strike.
        option_type : str, default='call'
            Option type label, normally ``"call"`` or ``"put"``.
        tol : float, default=1e-08
            Numerical convergence tolerance.

        Returns
        -------
        object
            Result of the implied normal vol workflow.

        Notes
        -----
        Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
        """
        return implied_normal_volatility(
            market_price,
            self.spot_price,
            self.strike_price,
            self.maturity_years,
            self.risk_free_rate,
            self.dividend_yield,
            option_type,
            tol,
        )

    def lognormal_vol(self):
        """Compute the result defined by ``lognormal_vol`` under this module's documented convention.

        Returns
        -------
        object
            Result of the lognormal vol workflow.

        Notes
        -----
        Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
        """
        bsm = BlackScholesMertonModel(
            self.spot_price,
            self.strike_price,
            self.maturity_years,
            self.risk_free_rate,
            0.3,
            self.dividend_yield,
        )
        price = self.call_price()
        return bsm.implied_vol(price, "call")

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
        return np.array([self.normal_volatility for _ in strikes])

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
