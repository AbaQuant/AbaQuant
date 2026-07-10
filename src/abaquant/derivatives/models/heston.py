"""Heston stochastic-volatility option pricing model.

Purpose
-------
The module prices European options by numerical integration of the Heston characteristic function and produces a strike smile.

Conventions
-----------
v0 and theta are variances, kappa is mean-reversion speed, xi is volatility of variance, and rho is the instantaneous correlation. Maturity is in years.

References
----------
[ 1 ] Heston, S. L. (1993), "A Closed-Form Solution for Options with Stochastic Volatility".
"""

from __future__ import annotations

import numpy as np
from scipy.integrate import quad

from ..numerics.implied_volatility import implied_volatility_black_scholes
from .diagnostics import OptionDiagnosticsMixin


class HestonStochasticVolatilityModel(OptionDiagnosticsMixin):
    """Heston stochastic-volatility model for European options.

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
    dividend_yield : float
        Continuously compounded annual dividend or carry yield in decimal units.
    initial_variance : float
        Initial instantaneous variance :math:`v_0`.
    variance_mean_reversion_speed : float
        Mean-reversion speed :math:`\\kappa` of instantaneous variance.
    long_run_variance : float
        Long-run variance level :math:`\\theta`.
    volatility_of_variance : float
        Variance-process volatility :math:`\\xi`.
    price_variance_correlation : float
        Instantaneous correlation :math:`\\rho` between price and variance shocks.
    """

    def __init__(
        self,
        spot_price,
        strike_price,
        maturity_years,
        risk_free_rate,
        dividend_yield,
        initial_variance,
        variance_mean_reversion_speed,
        long_run_variance,
        volatility_of_variance,
        price_variance_correlation,
    ):
        """Initialize the Heston stochastic-volatility model state.

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
        dividend_yield : float
            Continuously compounded annual dividend or carry yield in decimal units.
        initial_variance : float
            Initial instantaneous variance :math:`v_0`.
        variance_mean_reversion_speed : float
            Mean-reversion speed :math:`\\kappa` of instantaneous variance.
        long_run_variance : float
            Long-run variance level :math:`\\theta`.
        volatility_of_variance : float
            Variance-process volatility :math:`\\xi`.
        price_variance_correlation : float
            Instantaneous correlation :math:`\\rho` between price and variance shocks.
        """
        self.spot_price = spot_price
        self.strike_price = strike_price
        self.maturity_years = maturity_years
        self.risk_free_rate = risk_free_rate
        self.dividend_yield = dividend_yield
        self.initial_variance = initial_variance  # initial variance
        self.variance_mean_reversion_speed = variance_mean_reversion_speed  # mean reversion speed
        self.long_run_variance = long_run_variance  # long-run variance
        self.volatility_of_variance = volatility_of_variance  # vol of vol
        self.price_variance_correlation = price_variance_correlation  # correlation

    def _char_func(self, phi, j):
        """Evaluate an internal characteristic-function representation used by numerical pricing.

        Parameters
        ----------
        phi : float or array-like
            Fourier integration variable.
        j : float or array-like
            Model probability index used by the Heston integration routine.

        Returns
        -------
        object
            Result of the  char func workflow.
        """
        S, K, T = self.spot_price, self.strike_price, self.maturity_years
        r, q = self.risk_free_rate, self.dividend_yield
        v0, kappa, theta, xi, rho = (
            self.initial_variance,
            self.variance_mean_reversion_speed,
            self.long_run_variance,
            self.volatility_of_variance,
            self.price_variance_correlation,
        )

        i = complex(0, 1)

        if j == 1:
            u = 0.5
            b = kappa - rho * xi
        else:
            u = -0.5
            b = kappa

        a = kappa * theta
        x = np.log(S)
        ln_K = np.log(K)

        d = np.sqrt((rho * xi * i * phi - b) ** 2 - xi**2 * (2 * u * i * phi - phi**2))

        # Use the formulation that avoids the principal value discontinuity
        g2 = (b - rho * xi * i * phi - d) / (b - rho * xi * i * phi + d)

        exp_dT = np.exp(-d * T)

        C = (r - q) * i * phi * T + (a / xi**2) * (
            (b - rho * xi * i * phi - d) * T - 2.0 * np.log((1.0 - g2 * exp_dT) / (1.0 - g2))
        )
        D = ((b - rho * xi * i * phi - d) / xi**2) * ((1.0 - exp_dT) / (1.0 - g2 * exp_dT))

        return np.exp(C + D * v0 + i * phi * (x - ln_K))

    def _integrand(self, phi, j):
        """Perform an internal calculation used by the documented public workflow.

        Parameters
        ----------
        phi : float or array-like
            Fourier integration variable.
        j : float or array-like
            Model probability index used by the Heston integration routine.

        Returns
        -------
        object
            Result of the  integrand workflow.
        """
        return np.real(self._char_func(phi, j) / (complex(0, 1) * phi))

    def _Pj(self, j, upper=200, limit=500):
        """Perform an internal calculation used by the documented public workflow.

        Parameters
        ----------
        j : float or array-like
            Model probability index used by the Heston integration routine.
        upper : int, default=200
            Upper root-search or interval bound.
        limit : int, default=500
            Maximum numerical integration subdivision count.

        Returns
        -------
        object
            Result of the  Pj workflow.
        """
        integral, _ = quad(self._integrand, 1e-6, upper, args=(j,), limit=limit)
        return 0.5 + integral / np.pi

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
        P1 = self._Pj(1)
        P2 = self._Pj(2)
        return (
            self.spot_price * np.exp(-self.dividend_yield * self.maturity_years) * P1
            - self.strike_price * np.exp(-self.risk_free_rate * self.maturity_years) * P2
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
        call = self.call_price()
        return (
            call
            - self.spot_price * np.exp(-self.dividend_yield * self.maturity_years)
            + self.strike_price * np.exp(-self.risk_free_rate * self.maturity_years)
        )

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
            eng_h = HestonStochasticVolatilityModel(
                self.spot_price,
                K,
                self.maturity_years,
                self.risk_free_rate,
                self.dividend_yield,
                self.initial_variance,
                self.variance_mean_reversion_speed,
                self.long_run_variance,
                self.volatility_of_variance,
                self.price_variance_correlation,
            )
            price = eng_h.call_price()
            iv = implied_volatility_black_scholes(
                price,
                self.spot_price,
                K,
                self.maturity_years,
                self.risk_free_rate,
                self.dividend_yield,
                "call",
            )
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
