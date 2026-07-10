Derivatives
===========

The derivatives namespace contains pricing functions, object-oriented
models, payoff strategies, numerical simulations, and calibration
workflows.

Mathematical frame
------------------

Most derivative pricing routines implement the discounted expected
payoff idea:

.. math::


   V_0 = e^{-rT}\mathbb{E}^{\mathbb{Q}}[\Pi(S_T)]

where :math:`\Pi(S_T)` is the terminal payoff and :math:`\mathbb{Q}` is
a risk-neutral pricing measure.

Vanilla pricing
---------------

.. code:: python

   from abaquant.derivatives import black_scholes, black_76, implied_volatility_bsm

   call = black_scholes(100.0, 105.0, 0.04, 0.22, 1.0, is_call=True)
   future_call = black_76(102.0, 100.0, 0.04, 0.20, 1.0, is_call=True)
   implied_vol = implied_volatility_bsm(call, 100.0, 105.0, 0.04, 1.0)

Use functional pricing when you need compact calculations inside
vectorized or tabular workflows.

Greeks
------

.. code:: python

   from abaquant.derivatives import calculate_greeks, second_order_greeks

   first_order = calculate_greeks(100.0, 105.0, 0.04, 0.22, 1.0, is_call=True)
   second_order = second_order_greeks(100.0, 105.0, 0.04, 0.0, 0.22, 1.0, is_call=True)

Common first-order Greeks:

===== =============================
Greek Interpretation
===== =============================
Delta sensitivity to spot.
Gamma sensitivity of delta to spot.
Vega  sensitivity to volatility.
Theta sensitivity to time decay.
Rho   sensitivity to interest rate.
===== =============================

Model classes
-------------

.. code:: python

   from abaquant.derivatives import BlackScholesMertonModel

   model = BlackScholesMertonModel(
       spot_price=100.0,
       strike_price=105.0,
       maturity_years=1.0,
       risk_free_rate=0.04,
       volatility=0.22,
       dividend_yield=0.01,
   )

   price = model.price("call")
   greeks = model.greeks()
   diagnostics = model.diagnostics(option_type="call")
   scenario_grid = model.scenario_grid(
       spot_prices=[90.0, 100.0, 110.0],
       volatilities=[0.18, 0.22, 0.26],
       option_type="call",
   )

Use model classes when you want reusable state, diagnostics, reports,
visualizations, or scenario grids.

Advanced model families
-----------------------

+-----------------------+-----------------------+-----------------------+
| Model                 | Use case              | Main risk             |
+=======================+=======================+=======================+
| Bachelier             | Normal underlying     | Normal volatility     |
|                       | dynamics, negative    | convention differs    |
|                       | rates or negative     | from lognormal        |
|                       | underlyings.          | volatility.           |
+-----------------------+-----------------------+-----------------------+
| Heston                | Stochastic volatility | Calibration can be    |
|                       | and volatility        | non-unique or         |
|                       | clustering.           | unstable.             |
+-----------------------+-----------------------+-----------------------+
| Merton jump diffusion | Discontinuous price   | Jump intensity and    |
|                       | jumps.                | jump-size estimates   |
|                       |                       | are difficult.        |
+-----------------------+-----------------------+-----------------------+
| SABR                  | Implied-volatility    | Hagan approximation   |
|                       | smile and skew        | can break in extreme  |
|                       | interpolation.        | regimes.              |
+-----------------------+-----------------------+-----------------------+
| NIG and               | Heavy tails and       | Parameter             |
| Variance-Gamma        | skewed return         | interpretation and    |
|                       | distributions.        | calibration risk.     |
+-----------------------+-----------------------+-----------------------+

.. code:: python

   from abaquant.derivatives.advanced import HestonModel, SABRModel, MertonModel

Trees
-----

.. code:: python

   from abaquant.derivatives import binomial_tree, crr_binomial_tree

   price, tree = binomial_tree(
       100.0,
       100.0,
       1.0,
       0.05,
       0.20,
       80,
       option_type="put",
       american=True,
   )
   crr_price, stock_tree, option_tree = crr_binomial_tree(
       100.0,
       100.0,
       0.05,
       0.20,
       1.0,
       80,
       is_call=True,
   )

Tree methods are useful for American exercise and educational inspection
of state lattices.

Exotics
-------

Representative exotic helpers include:

.. code:: python

   from abaquant.derivatives import (
       cash_or_nothing_options,
       asset_or_nothing_options,
       geometric_asian_options,
       down_and_out_barrier_option,
       exchange_options,
   )

Exotic helpers use compact closed-form or approximate formulas where
available. Always check the formula convention before comparing against
another system.

Option strategies
-----------------

.. code:: python

   from abaquant.derivatives import OptionStrategy

   strategy = OptionStrategy.bull_call_spread(
       lower_strike=100.0,
       upper_strike=115.0,
       lower_premium=6.0,
       upper_premium=2.0,
   )

   profile = strategy.profile(points=101)
   break_evens = strategy.break_even_points()

Common predefined constructors include spreads, straddles, strangles,
butterflies, condors, and protective puts.

Calibration
-----------

.. code:: python

   from abaquant.derivatives.calibration import BSMFlatVolCalibration, SABRSmileCalibration

   # Use calibration classes when you have market observations in a structured table.
   # The returned CalibrationResult stores fitted parameters and diagnostics.

Calibration minimizes model-versus-market errors. Treat fitted
parameters as conditional estimates, not physical truths.

Visualization and reports
-------------------------

.. code:: python

   fig = model.visualize(chart="price_surface", option_type="call")
   report = model.report(option_type="call")
   report.save("reports", "bsm_call", formats=("markdown", "html"))

Available chart names vary by model and result type. See the
visualization examples for concrete galleries.
