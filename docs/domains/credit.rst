Credit analytics
================

The ``abaquant.credit`` namespace provides transition-matrix
construction, bond-value distributions, CDS/CDO helpers, Gaussian-copula
simulation, credit VaR/CVaR, and fundamentals-based proxy scoring.

Transition matrices
-------------------

.. code:: python

   from abaquant.credit import build_transition_matrix, DEFAULT_TM

   transition_matrix = build_transition_matrix(DEFAULT_TM)

A transition matrix stores conditional probabilities:

.. math::


   P_{ij}=\Pr(R_{t+1}=j\mid R_t=i).

Rows are starting rating states. Columns are destination states,
including default where represented.

Bond values by rating
---------------------

.. code:: python

   import numpy as np
   from abaquant.credit import bond_values_per_rating

   spreads = np.tile(np.linspace(0.01, 0.08, 5), (17, 1))
   values = bond_values_per_rating(
       face_value=100.0,
       coupon_rate=0.05,
       T=5,
       payments_per_year=1,
       recovery_pct=0.40,
       spreads=spreads,
   )

The valuation layer maps possible destination ratings to spread-adjusted
bond values.

Portfolio distribution
----------------------

.. code:: python

   from abaquant.credit import independent_distribution, expected_value_and_sigma

   bonds_data = [
       {"name": "Bond A", "rating_idx": 0, "values": values},
       {"name": "Bond B", "rating_idx": 2, "values": values * 0.95},
   ]
   distribution = independent_distribution(bonds_data, transition_matrix)
   expected_values, moments = expected_value_and_sigma(bonds_data, transition_matrix)

Independent portfolio distributions are tractable for compact examples.
They should not be treated as full credit portfolio models when defaults
are materially correlated.

Gaussian copula simulation
--------------------------

.. code:: python

   import numpy as np
   from abaquant.credit import gaussian_copula_simulation

   corr = np.array([[1.0, 0.25], [0.25, 1.0]])
   simulation = gaussian_copula_simulation(
       bonds_data,
       transition_matrix,
       corr,
       n_sims=10000,
       seed=42,
   )

The one-factor latent-variable frame is:

.. math::


   X_i=\sqrt{\rho}Z+\sqrt{1-\rho}\epsilon_i.

Default occurs when :math:`X_i` falls below the threshold implied by the
default probability.

CDS valuation
-------------

.. code:: python

   from abaquant.credit import value_cds

   cds = value_cds(
       hazard_rate=0.02,
       discount_rate=0.04,
       maturity=5,
       recovery_rate=0.40,
   )
   fair_spread = cds["spread"]

CDS valuation decomposes the contract into premium-leg and
contingent-leg components.

CDO tranche valuation
---------------------

.. code:: python

   import numpy as np
   from abaquant.credit import gauss_hermite_normal, value_tranche

   nodes, weights = gauss_hermite_normal(10)
   tranche_value = value_tranche(
       hazard_rate=0.03,
       rho=0.25,
       n=20,
       recovery_rate=0.40,
       attachment=0.03,
       detachment=0.07,
       risk_free_rate=0.04,
       periods=np.arange(1.0, 6.0),
       factor_nodes=nodes,
       weights=weights,
   )

Tranche valuation is very sensitive to correlation, recovery, default
probability, and model form.

Fundamentals-based credit proxy scoring
---------------------------------------

.. code:: python

   from abaquant.credit import CreditAnalysisInputs, calculate_credit_proxy_metrics

   assessment = calculate_credit_proxy_metrics(inputs)
   score = assessment.synthetic_credit_proxy_score
   band = assessment.synthetic_credit_proxy_band

Credit proxy scoring combines accounting, market-equity, and historical
series inputs when available.

Common metrics include:

+-----------------------------------+-----------------------------------+
| Metric                            | Meaning                           |
+===================================+===================================+
| Debt-to-equity                    | leverage relative to book equity. |
+-----------------------------------+-----------------------------------+
| Net debt to EBITDA                | debt burden relative to operating |
|                                   | earnings proxy.                   |
+-----------------------------------+-----------------------------------+
| Interest coverage                 | operating profit relative to      |
|                                   | interest expense.                 |
+-----------------------------------+-----------------------------------+
| Current ratio                     | short-term liquidity ratio.       |
+-----------------------------------+-----------------------------------+
| Quick ratio                       | liquidity excluding inventory.    |
+-----------------------------------+-----------------------------------+
| Altman-style Z score              | blended accounting distress       |
|                                   | heuristic.                        |
+-----------------------------------+-----------------------------------+
| Piotroski-style F score           | accounting quality and trend      |
|                                   | heuristic where enough data       |
|                                   | exist.                            |
+-----------------------------------+-----------------------------------+
| Synthetic proxy band              | AbaQuant’s internal qualitative   |
|                                   | band from normalized metrics.     |
+-----------------------------------+-----------------------------------+

Scenario analysis
-----------------

Credit proxy assessments can be stressed by changing debt, EBITDA,
revenue, margins, cash, or market value assumptions. Use scenario
analysis to identify which inputs dominate the synthetic score.

Interpretation limits
---------------------

Credit proxy scoring is not an agency rating. It does not include
covenant analysis, debt maturity schedules, collateral, legal seniority,
sector-specific adjustments, liquidity backstops, qualitative management
assessment, or forward-looking analyst judgment.
