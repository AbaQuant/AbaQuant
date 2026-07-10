"""Cox--Ross--Rubinstein binomial-tree option pricing.

Purpose
-------
The module implements a recombining lattice model for European and American vanilla options, including selected tree diagnostics.

Conventions
-----------
Maturity is in years; N is an integer step count; rates, yields, and volatility are decimal annual values.

References
----------
[ 1 ] Cox, J. C., S. A. Ross, and M. Rubinstein (1979), "Option Pricing: A Simplified Approach".
"""

from __future__ import annotations

import numpy as np

from .diagnostics import OptionDiagnosticsMixin


class CoxRossRubinsteinModel(OptionDiagnosticsMixin):
    """Recombining Cox--Ross--Rubinstein lattice model for vanilla options.

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
        Annualized lognormal volatility in decimal units.
    dividend_yield : float, default=0.0
        Continuous annual dividend or carry yield in decimal units.
    number_of_steps : int, default=200
        Number of recombining time steps in the lattice.
    allow_early_exercise : bool, default=False
        Whether the lattice applies the American early-exercise condition.
    """

    def __init__(
        self,
        spot_price,
        strike_price,
        maturity_years,
        risk_free_rate,
        volatility,
        dividend_yield=0.0,
        number_of_steps=200,
        allow_early_exercise=False,
    ):
        """Initialize a Cox--Ross--Rubinstein option-pricing lattice.

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
            Annualized lognormal volatility in decimal units.
        dividend_yield : float, default=0.0
            Continuous annual dividend or carry yield in decimal units.
        number_of_steps : int, default=200
            Number of recombining time steps in the lattice.
        allow_early_exercise : bool, default=False
            Whether the lattice applies the American early-exercise condition.
        """
        self.spot_price = spot_price
        self.strike_price = strike_price
        self.maturity_years = maturity_years
        self.risk_free_rate = risk_free_rate
        self.volatility = volatility
        self.dividend_yield = dividend_yield
        self.number_of_steps = number_of_steps
        self.allow_early_exercise = allow_early_exercise

    def _tree_params(self):
        """Return one-step Cox--Ross--Rubinstein lattice quantities.

        Returns
        -------
        tuple[float, float, float, float, float]
            ``(time_step_years, up_factor, down_factor,
            risk_neutral_up_probability, discount_factor)``. The probability
            is the risk-neutral probability of an up move over one time step.

        Notes
        -----
        The method does not clip the risk-neutral probability. Inputs that
        violate the lattice no-arbitrage condition therefore remain visible to
        downstream valuation logic.
        """
        time_step_years = self.maturity_years / self.number_of_steps
        up_factor = np.exp(self.volatility * np.sqrt(time_step_years))
        down_factor = 1.0 / up_factor
        risk_neutral_up_probability = (
            np.exp((self.risk_free_rate - self.dividend_yield) * time_step_years) - down_factor
        ) / (up_factor - down_factor)
        discount_factor = np.exp(-self.risk_free_rate * time_step_years)
        return (
            time_step_years,
            up_factor,
            down_factor,
            risk_neutral_up_probability,
            discount_factor,
        )

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
        (
            _time_step_years,
            up_factor,
            down_factor,
            risk_neutral_up_probability,
            discount_factor,
        ) = self._tree_params()
        number_of_steps = self.number_of_steps

        # Each terminal node is indexed by its count of downward movements.
        terminal_underlying_prices = (
            self.spot_price
            * (up_factor ** np.arange(number_of_steps, -1, -1))
            * (down_factor ** np.arange(0, number_of_steps + 1))
        )

        if option_type == "call":
            terminal_option_values = np.maximum(
                terminal_underlying_prices - self.strike_price,
                0.0,
            )
        else:
            terminal_option_values = np.maximum(
                self.strike_price - terminal_underlying_prices,
                0.0,
            )

        option_values = terminal_option_values
        current_underlying_prices = terminal_underlying_prices
        for _backward_step in range(number_of_steps):
            continuation_values = discount_factor * (
                risk_neutral_up_probability * option_values[:-1]
                + (1.0 - risk_neutral_up_probability) * option_values[1:]
            )
            if self.allow_early_exercise:
                # Move one node level backward before evaluating intrinsic value.
                current_underlying_prices = current_underlying_prices[:-1] / up_factor
                if option_type == "call":
                    intrinsic_values = np.maximum(
                        current_underlying_prices - self.strike_price,
                        0.0,
                    )
                else:
                    intrinsic_values = np.maximum(
                        self.strike_price - current_underlying_prices,
                        0.0,
                    )
                option_values = np.maximum(continuation_values, intrinsic_values)
            else:
                option_values = continuation_values

        return float(option_values[0])

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

    def full_tree(self, option_type="call", max_display=7):
        """Return the displayed portion of the recombining binomial valuation tree.

        Parameters
        ----------
        option_type : str, default='call'
            Option type label, normally ``"call"`` or ``"put"``.
        max_display : int, default=7
            Maximum number of tree levels retained for display.

        Returns
        -------
        tuple[list[list[float]], list[list[float] | None]]
            ``(underlying_price_tree, option_value_tree)``. Each outer-list
            position represents a time step and each inner-list position
            represents the number of downward moves at that step.

        Notes
        -----
        Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
        """
        (
            _time_step_years,
            up_factor,
            down_factor,
            risk_neutral_up_probability,
            discount_factor,
        ) = self._tree_params()
        displayed_step_count = min(self.number_of_steps, max_display)

        underlying_price_tree = [
            [0.0] * (step_index + 1) for step_index in range(displayed_step_count + 1)
        ]
        for step_index in range(displayed_step_count + 1):
            for downward_move_count in range(step_index + 1):
                underlying_price_tree[step_index][downward_move_count] = (
                    self.spot_price
                    * (up_factor ** (step_index - downward_move_count))
                    * (down_factor**downward_move_count)
                )

        terminal_underlying_prices = underlying_price_tree[displayed_step_count]
        if option_type == "call":
            terminal_option_values = [
                max(underlying_price - self.strike_price, 0.0)
                for underlying_price in terminal_underlying_prices
            ]
        else:
            terminal_option_values = [
                max(self.strike_price - underlying_price, 0.0)
                for underlying_price in terminal_underlying_prices
            ]

        option_value_tree = [None] * displayed_step_count + [terminal_option_values]
        for step_index in range(displayed_step_count - 1, -1, -1):
            option_values_at_step = []
            for downward_move_count in range(step_index + 1):
                continuation_value = discount_factor * (
                    risk_neutral_up_probability
                    * option_value_tree[step_index + 1][downward_move_count]
                    + (1.0 - risk_neutral_up_probability)
                    * option_value_tree[step_index + 1][downward_move_count + 1]
                )
                if self.allow_early_exercise:
                    underlying_price = underlying_price_tree[step_index][downward_move_count]
                    intrinsic_value = (
                        max(underlying_price - self.strike_price, 0.0)
                        if option_type == "call"
                        else max(self.strike_price - underlying_price, 0.0)
                    )
                    continuation_value = max(continuation_value, intrinsic_value)
                option_values_at_step.append(continuation_value)
            option_value_tree[step_index] = option_values_at_step

        return underlying_price_tree, option_value_tree

    def delta(self, option_type="call"):
        """Estimate option delta from the first binomial-tree step.

        Parameters
        ----------
        option_type : str, default='call'
            Option type label, normally ``"call"`` or ``"put"``.

        Returns
        -------
        float
            Computed delta in the units implied by the documented inputs.
        """
        time_step_years, up_factor, down_factor, _probability, _discount = self._tree_params()
        upward_underlying_price = self.spot_price * up_factor
        downward_underlying_price = self.spot_price * down_factor
        upward_subtree_model = CoxRossRubinsteinModel(
            spot_price=upward_underlying_price,
            strike_price=self.strike_price,
            maturity_years=self.maturity_years - time_step_years,
            risk_free_rate=self.risk_free_rate,
            volatility=self.volatility,
            dividend_yield=self.dividend_yield,
            number_of_steps=self.number_of_steps - 1,
            allow_early_exercise=self.allow_early_exercise,
        )
        downward_subtree_model = CoxRossRubinsteinModel(
            spot_price=downward_underlying_price,
            strike_price=self.strike_price,
            maturity_years=self.maturity_years - time_step_years,
            risk_free_rate=self.risk_free_rate,
            volatility=self.volatility,
            dividend_yield=self.dividend_yield,
            number_of_steps=self.number_of_steps - 1,
            allow_early_exercise=self.allow_early_exercise,
        )
        upward_option_value = upward_subtree_model.price(option_type)
        downward_option_value = downward_subtree_model.price(option_type)
        return (upward_option_value - downward_option_value) / (
            upward_underlying_price - downward_underlying_price
        )

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


def crr_tree_parameters(
    T: float, r: float, sigma: float, q: float = 0.0, N: int = 200
) -> dict[str, float]:
    """Compute Cox--Ross--Rubinstein step parameters.

    Parameters
    ----------
    T : float
        Time to maturity in years.
    r : float
        Continuously compounded risk-free annual rate in decimal units.
    sigma : float
        Annualized lognormal volatility in decimal units; for example, ``0.20`` denotes 20%.
    q : float, default=0.0
        Continuous dividend or carry yield in decimal annual units.
    N : int, default=200
        Number of binomial time steps.

    Returns
    -------
    dict[str, float]
        Named outputs of the crr tree parameters calculation.

    Notes
    -----
    Model inputs are interpreted according to the module-level rate, maturity, and volatility conventions. Numerical outputs depend on the validity of those assumptions.
    """
    if N <= 0:
        raise ValueError("N must be positive.")
    time_step_years = T / N
    up_factor = np.exp(sigma * np.sqrt(time_step_years))
    down_factor = 1.0 / up_factor
    risk_neutral_up_probability = (np.exp((r - q) * time_step_years) - down_factor) / (
        up_factor - down_factor
    )
    discount_factor = np.exp(-r * time_step_years)
    return {
        "dt": float(time_step_years),
        "u": float(up_factor),
        "d": float(down_factor),
        "p": float(risk_neutral_up_probability),
        "disc": float(discount_factor),
    }
