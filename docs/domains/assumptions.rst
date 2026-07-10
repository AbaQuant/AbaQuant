Assumptions and limitations
===========================

AbaQuant models are deterministic or numerical research tools. They do
not remove market, model, estimation, liquidity, counterparty, legal,
accounting, operational, tax, or provider-data risk.

Global assumptions
------------------

-  Inputs use decimal annual rates and volatilities unless a function
   states otherwise.
-  Maturities are usually measured in years.
-  Historical estimates assume the input sample is relevant to the
   period being analyzed.
-  Optimizers assume the objective and constraints adequately represent
   the user’s decision problem.
-  Provider data are treated as inputs, not as verified truth.

Black–Scholes–Merton and Black-76
---------------------------------

Black–Scholes–Merton assumes:

-  lognormal underlying dynamics;
-  constant volatility;
-  constant risk-free rate;
-  continuous trading;
-  frictionless markets;
-  no jumps;
-  idealized borrowing and lending;
-  known continuous dividend yield when supplied.

Black-76 applies a similar lognormal assumption to forwards or futures.

Failure modes:

-  volatility smile/skew;
-  discrete dividends;
-  early exercise;
-  jumps and halts;
-  stochastic rates;
-  transaction costs and bid-ask spreads;
-  illiquid options.

Bachelier model
---------------

Bachelier assumes normal price dynamics. It can be useful when rates or
underlyings can be negative, but normal volatility is not
interchangeable with lognormal volatility.

Heston
------

Heston introduces stochastic variance. It can represent volatility
clustering and skew, but calibration is often non-convex and parameter
estimates can be unstable.

Important risks:

-  local minima;
-  parameter non-identifiability;
-  numerical integration error;
-  poor extrapolation outside observed strikes and maturities;
-  violation of parameter constraints such as positivity or Feller-type
   conditions.

SABR
----

SABR is often used to interpolate volatility smiles. Hagan-style
approximations are convenient but can become unreliable for extreme
strikes, very short maturities, or parameter regimes outside
approximation assumptions.

Jump and Levy models
--------------------

Merton jump diffusion, NIG, and Variance-Gamma add skew, kurtosis, and
discontinuities. They require more parameters than BSM and are
correspondingly more exposed to calibration error.

Exotic options
--------------

Closed-form and approximate exotic formulas are convention-sensitive.
Barrier monitoring, averaging method, rebate timing, exercise style, and
settlement assumptions can materially change prices.

Portfolio optimization
----------------------

Portfolio optimizers are sensitive to:

-  expected returns;
-  covariance estimates;
-  constraints and bounds;
-  missing data;
-  non-stationary correlations;
-  transaction costs;
-  turnover;
-  sampling frequency;
-  estimation window;
-  survivorship bias;
-  look-ahead bias.

Mean-variance optimization is especially sensitive to small changes in
expected returns.

Backtesting
-----------

Backtests are historical simulations. They do not prove that a strategy
will work out of sample.

Backtest failure modes include:

-  missing delisted assets;
-  stale prices;
-  unrealistic fills;
-  ignored taxes;
-  ignored borrow costs;
-  ignored capacity and market impact;
-  using revised data unavailable at the historical decision time;
-  optimizing after seeing the test period.

Credit proxy scoring
--------------------

Fundamentals-based credit proxy scoring is an accounting heuristic, not
a credit rating. It does not replace full credit analysis.

Missing dimensions include:

-  debt maturity ladder;
-  secured versus unsecured priority;
-  covenant package;
-  liquidity facilities;
-  off-balance-sheet obligations;
-  sector-specific adjustments;
-  macro regime;
-  issuer access to capital markets;
-  management quality and event risk.

Gaussian copula credit models
-----------------------------

Copula outputs depend heavily on default probabilities, recoveries,
exposures, and correlations. One-factor Gaussian copulas can understate
clustered tail dependence in stress regimes.

CDS and CDO analytics
---------------------

Credit derivative calculations depend on hazard-rate assumptions,
premium frequency, accrual conventions, discount curves, recovery
assumptions, counterparty risk, and legal definitions of credit events.

Rate curves
-----------

Manual and FRED-backed rate curves are convenient proxies. They are not
production-grade curve construction.

Limitations include:

-  no bootstrapped zero-coupon curve by default;
-  no collateral curve distinction;
-  no cross-currency basis;
-  no issuer-specific funding curve;
-  no liquidity adjustment;
-  no intraday curve dynamics.

Market data
-----------

Live provider data can be stale, delayed, missing, restated, adjusted,
subject to licensing restrictions, or inconsistent across providers.

Visualization and reports
-------------------------

Charts and reports summarize model outputs. They do not validate the
economic assumptions behind those outputs.
