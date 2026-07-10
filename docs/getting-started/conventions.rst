Conventions and notation
========================

AbaQuant uses explicit but compact financial conventions. This page
defines the common symbols and units used across the package.

Glossary
--------

+-----------------------------------+-----------------------------------+
| Term                              | Meaning                           |
+===================================+===================================+
| Annual decimal rate               | A rate such as ``0.05`` meaning   |
|                                   | 5% per year.                      |
+-----------------------------------+-----------------------------------+
| Annual decimal volatility         | A volatility such as ``0.20``     |
|                                   | meaning 20% annualized            |
|                                   | volatility.                       |
+-----------------------------------+-----------------------------------+
| Maturity                          | Time to expiration or cash-flow   |
|                                   | date, usually measured in years.  |
+-----------------------------------+-----------------------------------+
| Simple return                     | :math:`R_t = P_t/P_{t-1}-1`.      |
+-----------------------------------+-----------------------------------+
| Log return                        | :math:`r_t = \log(P_t/P_{t-1})`.  |
+-----------------------------------+-----------------------------------+
| Discount factor                   | Present-value multiplier applied  |
|                                   | to a future cash flow.            |
+-----------------------------------+-----------------------------------+
| Risk-neutral valuation            | Pricing by discounted expected    |
|                                   | payoff under a risk-neutral       |
|                                   | measure.                          |
+-----------------------------------+-----------------------------------+
| Provenance                        | Metadata describing source,       |
|                                   | provider, cache status, request,  |
|                                   | and transformations.              |
+-----------------------------------+-----------------------------------+

Rates and compounding
---------------------

Most model inputs use decimal annual rates:

.. code:: python

   risk_free_rate = 0.05  # 5% per year, not 5.0
   volatility = 0.20      # 20% annual volatility, not 20.0

Continuous discounting is commonly represented as:

.. math::


   D(T)=e^{-rT}

where:

============ =====================================
Symbol       Meaning
============ =====================================
:math:`D(T)` discount factor to maturity :math:`T`
:math:`r`    annual continuously compounded rate
:math:`T`    maturity in years
============ =====================================

The ``RateCurve.discount_factor()`` method supports continuous, annual,
and simple compounding modes.

Option notation
---------------

================ ================================================
Symbol           Meaning
================ ================================================
:math:`S_0`      spot price
:math:`K`        strike price
:math:`T`        maturity in years
:math:`r`        risk-free rate
:math:`q`        dividend yield or carry yield
:math:`\sigma`   annualized volatility
:math:`N(\cdot)` standard normal cumulative distribution function
================ ================================================

Black–Scholes–Merton call value:

.. math::


   C=S_0e^{-qT}N(d_1)-Ke^{-rT}N(d_2)

with:

.. math::


   d_1=\frac{\ln(S_0/K)+(r-q+\frac12\sigma^2)T}{\sigma\sqrt{T}},
   \qquad d_2=d_1-\sigma\sqrt{T}.

Portfolio notation
------------------

================== ======================
Symbol             Meaning
================== ======================
:math:`w`          asset-weight vector
:math:`\mu`        expected-return vector
:math:`\Sigma`     covariance matrix
:math:`r_f`        risk-free rate
:math:`\mathbf{1}` vector of ones
================== ======================

Long-only fully invested portfolios commonly satisfy:

.. math::


   \mathbf{1}^\top w=1,
   \qquad w_i\ge 0.

Expected return and variance:

.. math::


   \mu_p=w^\top\mu,
   \qquad
   \sigma_p^2=w^\top\Sigma w.

Sharpe ratio:

.. math::


   \operatorname{Sharpe}(w)=\frac{w^\top\mu-r_f}{\sqrt{w^\top\Sigma w}}.

Credit notation
---------------

+-----------------------------------+-----------------------------------+
| Symbol                            | Meaning                           |
+===================================+===================================+
| :math:`P_{ij}`                    | transition probability from       |
|                                   | rating :math:`i` to destination   |
|                                   | state :math:`j`                   |
+-----------------------------------+-----------------------------------+
| :math:`PD`                        | default probability               |
+-----------------------------------+-----------------------------------+
| :math:`LGD`                       | loss given default                |
+-----------------------------------+-----------------------------------+
| :math:`R`                         | recovery rate                     |
+-----------------------------------+-----------------------------------+
| :math:`\rho`                      | asset-correlation parameter in a  |
|                                   | one-factor copula                 |
+-----------------------------------+-----------------------------------+

The Gaussian one-factor form can be written as:

.. math::


   X_i=\sqrt{\rho}\,Z+\sqrt{1-\rho}\,\epsilon_i,

where :math:`Z` is the systematic factor and :math:`\epsilon_i` is an
idiosyncratic factor.

Sign conventions
----------------

-  Option strategy **long positions** are positive quantities.
-  Option strategy **short positions** are negative quantities.
-  Premiums are generally entered as positive paid/received amounts;
   strategy logic applies the position sign.
-  Portfolio weights are decimal fractions; ``0.25`` means 25% of
   capital.
-  Transaction costs in backtests are basis points when parameters end
   in ``_bps``.

Missing data conventions
------------------------

-  Provider facades may return empty frames or raise provider-specific
   errors when data are unavailable.
-  Financial-statement normalization may be incomplete if source facts
   do not map to canonical line items.
-  Credit proxy metrics can be unavailable when required denominator or
   historical fields are missing.
