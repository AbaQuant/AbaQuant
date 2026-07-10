Financial mathematics
=====================

The ``abaquant.financial_math`` namespace contains deterministic finance
and actuarial building blocks: time value of money, rate conversions,
annuities, bonds, loans, cash-flow valuation, corporate finance, equity
valuation, portfolio primitives, and simple VaR helpers.

Time value of money
-------------------

.. code:: python

   from abaquant.financial_math import future_value, present_value

   fv = future_value(1000.0, rate=0.05, periods=5)
   pv = present_value(1276.2815625, rate=0.05, periods=5)

Core relation:

.. math::


   FV = PV(1+i)^n,
   \qquad
   PV=\frac{FV}{(1+i)^n}.

For continuous compounding:

.. math::


   FV=PV e^{rt},
   \qquad
   PV=FV e^{-rt}.

Rate conversion
---------------

.. code:: python

   from abaquant.financial_math import (
       nominal_to_effective_rate,
       effective_to_nominal_rate,
       nominal_to_continuous_rate,
   )

   effective = nominal_to_effective_rate(0.06, compounds_per_year=12)
   nominal = effective_to_nominal_rate(effective, compounds_per_year=12)
   continuous = nominal_to_continuous_rate(0.06, compounds_per_year=12)

Nominal-to-effective conversion:

.. math::


   i_{\text{eff}}=\left(1+\frac{j}{m}\right)^m-1.

Annuities and perpetuities
--------------------------

.. code:: python

   from abaquant.financial_math import effective_annuity_present_value, perpetuity_present_value

   annuity_pv = effective_annuity_present_value(payment=100.0, period_rate=0.05, periods=10)
   perpetuity_pv = perpetuity_present_value(payment=100.0, rate=0.05)

Level annuity present value:

.. math::


   a_{\overline{n}|}=\frac{1-v^n}{i},
   \qquad v=(1+i)^{-1}.

Bonds
-----

.. code:: python

   from abaquant.financial_math import bond_price, bond_yield, bond_risk

   price, coupon_pv, redemption_pv, total_coupon = bond_price(
       face_value=1000.0,
       coupon_rate_per_period=0.05,
       redemption_value=1000.0,
       yield_per_period=0.045,
       periods=10,
   )
   yield_to_maturity = bond_yield(
       price=price,
       face_value=1000.0,
       coupon_rate_per_period=0.05,
       redemption_value=1000.0,
       periods=10,
   )
   modified_duration, macaulay_duration, convexity = bond_risk(
       face_value=1000.0,
       coupon_rate_per_period=0.05,
       redemption_value=1000.0,
       yield_per_period=0.045,
       periods=10,
       payments_per_year=1,
   )

Bond price is the present value of coupons plus principal:

.. math::


   P=\sum_{t=1}^{n}\frac{C}{(1+y)^t}+\frac{F}{(1+y)^n}.

Loans
-----

.. code:: python

   from abaquant.financial_math import amortization_schedule

   schedule = amortization_schedule(principal=250000.0, period_rate=0.055 / 12.0, periods=360)

The returned table decomposes each payment into interest, principal
repayment, and remaining balance.

Corporate finance
-----------------

.. code:: python

   from abaquant.financial_math import (
       capm_cost_of_equity,
       weighted_average_cost_of_capital,
       dcf_valuation,
   )

   ke = capm_cost_of_equity(risk_free_rate=0.04, beta=1.2, market_return=0.09)
   wacc = weighted_average_cost_of_capital(
       cost_of_equity=ke,
       equity_weight=0.60,
       cost_of_debt=0.055,
       tax_rate=0.21,
   )
   value = dcf_valuation(
       fcf_base=80.0,
       projection_growth=0.05,
       terminal_growth=0.025,
       discount_rate=wacc,
       projection_years=5,
       net_debt=120.0,
       shares_outstanding=25.0,
   )

CAPM:

.. math::


   E[R_i]=r_f+\beta_i(E[R_m]-r_f).

Equity valuation
----------------

.. code:: python

   from abaquant.financial_math import gordon_shapiro_valuation, multiples_valuation

   value = gordon_shapiro_valuation(next_dividend=2.5, required_return=0.09, growth_rate=0.03)
   peer_value = multiples_valuation(value_metric=12.0, target_multiple=18.0)

Gordon growth model:

.. math::


   P_0=\frac{D_1}{k-g},\qquad k>g.

Portfolio primitives
--------------------

.. code:: python

   from abaquant.financial_math import (
       simple_returns_from_prices,
       annualized_mean_returns_from_returns,
       annualized_covariance_from_returns,
       maximum_sharpe_weights,
   )

   returns = simple_returns_from_prices(prices)
   mu = annualized_mean_returns_from_returns(returns)
   cov = annualized_covariance_from_returns(returns)
   weights = maximum_sharpe_weights(mu.to_numpy(), cov.to_numpy(), risk_free_rate=0.02)

For higher-level allocation workflows, prefer
``abaquant.portfolio.PortfolioAllocator``.

VaR helpers
-----------

.. code:: python

   from abaquant.financial_math import parametric_var, monte_carlo_var_cvar

   var_amount, z_score, period_return, period_volatility = parametric_var(
       portfolio_value=1_000_000.0,
       annual_return=0.08,
       annual_volatility=0.18,
       confidence_level=0.95,
       horizon_days=10,
   )

``parametric_var()`` returns the VaR amount, normal z-score,
horizon-scaled expected return, and horizon-scaled volatility. It does
**not** return CVaR. Use ``monte_carlo_var_cvar()`` for a simple
simulation-based VaR/CVaR pair.
