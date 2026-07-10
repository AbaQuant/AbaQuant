abaquant.credit.cdo
===================

**Import path:** ``abaquant.credit.cdo``

**Domain:** Credit-risk analytics and fundamentals-derived credit proxies.

Purpose
-------

One-factor Gaussian-copula CDO tranche valuation.

When to use it
--------------

Use this package for transition matrices, spread-based valuation, CDS/CDO building blocks, copula simulation, tail risk, and accounting-based credit diagnostics.

Public objects
--------------

* **function:** ``gauss_hermite_normal`` — Transform Gauss--Hermite nodes to standard-normal factor nodes.
* **function:** ``log_binomial_coefficient`` — Compute the logarithm of a binomial coefficient.
* **function:** ``conditional_default_probability`` — Compute conditional default probability given the common Gaussian factor.
* **function:** ``binomial_probabilities_log`` — Compute binomial probabilities in log-stable form.
* **function:** ``expected_tranche_survival_given_factor`` — Compute conditional expected tranche survival for one factor realization.
* **function:** ``value_tranche`` — Value the tranche cash-flow structure under the one-factor Gaussian-copula model.

Detailed reference
------------------

.. automodule:: abaquant.credit.cdo
   :members:
   :show-inheritance:
   :member-order: bysource
