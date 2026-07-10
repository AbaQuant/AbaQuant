abaquant.credit.cds
===================

**Import path:** ``abaquant.credit.cds``

**Domain:** Credit-risk analytics and fundamentals-derived credit proxies.

Purpose
-------

Credit-default-swap valuation primitives.

When to use it
--------------

Use this package for transition matrices, spread-based valuation, CDS/CDO building blocks, copula simulation, tail risk, and accounting-based credit diagnostics.

Public objects
--------------

* **function:** ``cds_probability_table`` — Build the default and survival probability table used for CDS valuation.
* **function:** ``cds_premium_leg_table`` — Build the discounted premium-leg cash-flow table for a CDS.
* **function:** ``cds_contingent_leg_table`` — Build the discounted contingent-protection-leg cash-flow table for a CDS.
* **function:** ``cds_accrued_premium_table`` — Build the accrued-premium approximation table for a CDS.
* **function:** ``cds_fair_spread`` — Compute the fair annual CDS premium rate from leg present values.
* **function:** ``value_cds`` — Value the CDS premium and protection legs and compute the fair spread.

Detailed reference
------------------

.. automodule:: abaquant.credit.cds
   :members:
   :show-inheritance:
   :member-order: bysource
