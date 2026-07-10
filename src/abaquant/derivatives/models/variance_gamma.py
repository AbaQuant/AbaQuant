"""Variance-Gamma option pricing model.

Purpose
-------
The module uses a Variance-Gamma characteristic function and Fourier inversion to value European options and derive an implied-volatility smile.

Conventions
-----------
sigma, theta, and nu follow the implementation parameterization; maturity is in years and rates are decimal annual quantities.

References
----------
[ 1 ] Madan, D. B., P. P. Carr, and E. C. Chang (1998), "The Variance Gamma Process and Option Pricing".
[ 2 ] Carr, P., and D. B. Madan (1999), "Option Valuation Using the Fast Fourier Transform".
"""

from __future__ import annotations

import numpy as np

from ..numerics.carr_madan_fft import carr_madan_option_price
from ..numerics.implied_volatility import implied_volatility_black_scholes
from .diagnostics import OptionDiagnosticsMixin


class VarianceGammaProcessModel(OptionDiagnosticsMixin):
    """Variance-gamma process model for European option valuation.

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
        Diffusion-scale parameter in the variance-gamma process.
    drift_parameter : float
        Variance-gamma asymmetry or drift parameter :math:`\\theta`.
    activity_rate : float
        Variance-gamma activity parameter :math:`\\nu`.
    dividend_yield : float, default=0.0
        Continuous annual dividend or carry yield in decimal units.
    """

    def __init__(
        self,
        spot_price,
        strike_price,
        maturity_years,
        risk_free_rate,
        volatility,
        drift_parameter,
        activity_rate,
        dividend_yield=0.0,
    ):
        """Initialize the variance-gamma process model state.

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
            Diffusion-scale parameter in the variance-gamma process.
        drift_parameter : float
            Variance-gamma asymmetry or drift parameter :math:`\\theta`.
        activity_rate : float
            Variance-gamma activity parameter :math:`\\nu`.
        dividend_yield : float, default=0.0
            Continuous annual dividend or carry yield in decimal units.
        """
        self.spot_price = spot_price
        self.strike_price = strike_price
        self.maturity_years = maturity_years
        self.risk_free_rate = risk_free_rate
        self.volatility = volatility
        self.drift_parameter = drift_parameter
        self.activity_rate = activity_rate
        self.dividend_yield = dividend_yield

    def _omega(self):
        """Perform an internal calculation used by the documented public workflow.

        Returns
        -------
        object
            Result of the  omega workflow.
        """
        return (1 / self.activity_rate) * np.log(
            1
            - self.drift_parameter * self.activity_rate
            - 0.5 * self.volatility**2 * self.activity_rate
        )

    def characteristic_function(self, u):
        """Evaluate the model characteristic function at the supplied Fourier argument.

        Parameters
        ----------
        u : float or array-like
            Fourier argument at which the characteristic function is evaluated.

        Returns
        -------
        object
            Result of the characteristic function workflow.
        """
        omega = self._omega()
        drift_term = (
            1j
            * u
            * (
                np.log(self.spot_price)
                + (self.risk_free_rate - self.dividend_yield + omega) * self.maturity_years
            )
        )
        vg_term = -(self.maturity_years / self.activity_rate) * np.log(
            1
            - 1j * u * self.drift_parameter * self.activity_rate
            + 0.5 * self.volatility**2 * self.activity_rate * u**2
        )
        return np.exp(drift_term + vg_term)

    def _char_func(self, u):
        """Evaluate an internal characteristic-function representation used by numerical pricing.

        Parameters
        ----------
        u : float or array-like
            Fourier argument at which the characteristic function is evaluated.

        Returns
        -------
        object
            Result of the  char func workflow.
        """
        return self.characteristic_function(u)

    def _price_via_fft(self, option_type="call", N=4096, eta=0.25):
        """Perform an internal calculation used by the documented public workflow.

        Parameters
        ----------
        option_type : str, default='call'
            Option type label, normally ``"call"`` or ``"put"``.
        N : int, default=4096
            Number of binomial time steps.
        eta : float, default=0.25
            Fourier-grid spacing in the Carr--Madan implementation.

        Returns
        -------
        float
            Computed  price via fft in the units implied by the documented inputs.

        Notes
        -----
        Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
        """
        return carr_madan_option_price(
            self.characteristic_function,
            self.spot_price,
            self.strike_price,
            self.maturity_years,
            self.risk_free_rate,
            self.dividend_yield,
            option_type,
            n_grid=N,
            eta=eta,
        )

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
        return self._price_via_fft("call")

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
        return self._price_via_fft("put")

    def implied_vol(self, option_type="call"):
        """Return the Black--Scholes--Merton implied volatility associated with the model price.

        Parameters
        ----------
        option_type : str, default='call'
            Option type label, normally ``"call"`` or ``"put"``.

        Returns
        -------
        object
            Result of the implied vol workflow.

        Notes
        -----
        Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
        """
        price = self.call_price() if option_type == "call" else self.put_price()
        return implied_volatility_black_scholes(
            price,
            self.spot_price,
            self.strike_price,
            self.maturity_years,
            self.risk_free_rate,
            self.dividend_yield,
            option_type,
        )

    def vol_smile(self, strikes, option_type="call"):
        """Evaluate the model-implied volatility across the supplied strike grid.

        Parameters
        ----------
        strikes : float or array-like
            Strike-price grid in the same currency units as the underlying or forward.
        option_type : str, default='call'
            Option type label, normally ``"call"`` or ``"put"``.

        Returns
        -------
        numpy.ndarray
            Numeric array ordered consistently with the supplied strikes, time grid, assets, or state labels.

        Notes
        -----
        Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
        """
        ivs = []
        for strike in strikes:
            eng = VarianceGammaProcessModel(
                self.spot_price,
                strike,
                self.maturity_years,
                self.risk_free_rate,
                self.volatility,
                self.drift_parameter,
                self.activity_rate,
                self.dividend_yield,
            )
            iv = eng.implied_vol(option_type)
            ivs.append(iv * 100 if not np.isnan(iv) else np.nan)
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
