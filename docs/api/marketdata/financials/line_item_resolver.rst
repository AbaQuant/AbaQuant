abaquant.marketdata.financials.line_item_resolver
=================================================

**Import path:** ``abaquant.marketdata.financials.line_item_resolver``

**Domain:** Provider-neutral market-data facades, normalized records, caching, and analytics.

Purpose
-------

Canonical financial-line-item resolution across provider-specific labels.

When to use it
--------------

This module participates in the financial-statement pipeline: provider response, normalization, cache/repository coordination, canonical line-item resolution, and analytical input construction.

Public objects
--------------

* **function:** ``find_label`` — Resolve a provider label by case-insensitive exact matching.
* **function:** ``latest_value`` — Return the first finite value from provider-order statement columns.
* **function:** ``resolve_line_items`` — Build canonical latest-value items with original-label provenance.
* **function:** ``history_for_item`` — Return finite values ordered oldest-to-newest where dates are parseable.

Detailed reference
------------------

.. automodule:: abaquant.marketdata.financials.line_item_resolver
   :members:
   :show-inheritance:
   :member-order: bysource
