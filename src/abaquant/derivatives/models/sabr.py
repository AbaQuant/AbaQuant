"""SABR implied-volatility approximation and option pricing.

Purpose
-------
The module evaluates the Hagan SABR implied-volatility approximation and converts it to approximate Black prices.

Conventions
-----------
F and K are forward and strike; alpha, beta, rho, and nu are SABR parameters; maturity is in years.

References
----------
[ 1 ] Hagan, P. S., D. Kumar, A. S. Lesniewski, and D. E. Woodward (2002), "Managing Smile Risk".
"""

from __future__ import annotations

import numpy as np

from .black_scholes import BlackScholesMertonModel
from .diagnostics import OptionDiagnosticsMixin


class SABRVolatilityModel(OptionDiagnosticsMixin):
    """SABR implied-volatility model using the Hagan approximation.

    Parameters
    ----------
    forward_price : float
        Forward price associated with the option maturity.
    strike_price : float
        Option exercise price in the same units as ``forward_price``.
    maturity_years : float
        Time to expiration in years.
    initial_volatility : float
        SABR level parameter :math:`\\alpha`.
    elasticity_parameter : float
        SABR elasticity parameter :math:`\\beta`.
    spot_forward_correlation : float
        Correlation parameter :math:`\\rho` between forward and volatility shocks.
    volatility_of_volatility : float
        SABR volatility-of-volatility parameter :math:`\\nu`.
    risk_free_rate : float, default=0.0
        Continuously compounded annual risk-free rate in decimal units.
    dividend_yield : float, default=0.0
        Continuously compounded annual dividend or carry yield in decimal units.
    spot_price : float or None, default=None
        Optional spot price used for Black--Scholes price conversion. When omitted,
        the forward price is used as the spot proxy.
    """

    def __init__(
        self,
        forward_price,
        strike_price,
        maturity_years,
        initial_volatility,
        elasticity_parameter,
        spot_forward_correlation,
        volatility_of_volatility,
        risk_free_rate=0.0,
        dividend_yield=0.0,
        spot_price=None,
    ):
        """Initialize the SABR model and its Black--Scholes conversion inputs.

        Parameters
        ----------
        forward_price : float
            Forward price associated with the option maturity.
        strike_price : float
            Option exercise price in the same units as ``forward_price``.
        maturity_years : float
            Time to expiration in years.
        initial_volatility : float
            SABR level parameter :math:`\\alpha`.
        elasticity_parameter : float
            SABR elasticity parameter :math:`\\beta`.
        spot_forward_correlation : float
            Correlation parameter :math:`\\rho` between forward and volatility shocks.
        volatility_of_volatility : float
            SABR volatility-of-volatility parameter :math:`\\nu`.
        risk_free_rate : float, default=0.0
            Continuously compounded annual risk-free rate in decimal units.
        dividend_yield : float, default=0.0
            Continuously compounded annual dividend or carry yield in decimal units.
        spot_price : float or None, default=None
            Optional spot price used for Black--Scholes price conversion.
        """
        self.forward_price = forward_price
        self.strike_price = strike_price
        self.maturity_years = maturity_years
        self.initial_volatility = initial_volatility
        self.elasticity_parameter = elasticity_parameter
        self.spot_forward_correlation = spot_forward_correlation
        self.volatility_of_volatility = volatility_of_volatility
        self.risk_free_rate = risk_free_rate
        self.dividend_yield = dividend_yield
        self.spot_price = spot_price if spot_price is not None else forward_price

    def implied_vol(self):
        """Return the Black--Scholes--Merton implied volatility associated with the model price.

        Returns
        -------
        object
            Result of the implied vol workflow.

        Notes
        -----
        Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
        """
        F, K, T = self.forward_price, self.strike_price, self.maturity_years
        alpha, beta = self.initial_volatility, self.elasticity_parameter
        rho, nu = self.spot_forward_correlation, self.volatility_of_volatility

        eps = 1e-8
        if T <= 0:
            return alpha

        FK_mid = (F * K) ** ((1 - beta) / 2)
        ln_FK = np.log(F / K) if abs(F - K) > eps else 0.0

        # Leading term
        A = alpha / (
            FK_mid * (1 + (1 - beta) ** 2 / 24 * ln_FK**2 + (1 - beta) ** 4 / 1920 * ln_FK**4)
        )

        # z and x(z) correction
        if abs(F - K) > eps:
            z = nu / alpha * FK_mid * ln_FK
            x_z = np.log((np.sqrt(1 - 2 * rho * z + z**2) + z - rho) / (1 - rho))
            B = z / x_z if abs(x_z) > eps else 1.0
        else:
            B = 1.0

        # Time-correction term
        C = (
            1
            + (
                (1 - beta) ** 2 / 24 * alpha**2 / FK_mid**2
                + rho * beta * nu * alpha / (4 * FK_mid)
                + (2 - 3 * rho**2) / 24 * nu**2
            )
            * T
        )

        return A * B * C

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
        iv = self.implied_vol()
        bsm = BlackScholesMertonModel(
            self.spot_price,
            self.strike_price,
            self.maturity_years,
            self.risk_free_rate,
            iv,
            self.dividend_yield,
        )
        return bsm.call_price()

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
        iv = self.implied_vol()
        bsm = BlackScholesMertonModel(
            self.spot_price,
            self.strike_price,
            self.maturity_years,
            self.risk_free_rate,
            iv,
            self.dividend_yield,
        )
        return bsm.put_price()

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
            eng = SABRVolatilityModel(
                self.forward_price,
                K,
                self.maturity_years,
                self.initial_volatility,
                self.elasticity_parameter,
                self.spot_forward_correlation,
                self.volatility_of_volatility,
                self.risk_free_rate,
                self.dividend_yield,
                self.spot_price,
            )
            ivs.append(eng.implied_vol())
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
