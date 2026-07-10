abaquant.marketdata.financials.normalizer
=========================================

**Import path:** ``abaquant.marketdata.financials.normalizer``

**Domain:** Provider-neutral market-data facades, normalized records, caching, and analytics.

Purpose
-------

Provider-statement table normalization and JSON-safe serialization.

When to use it
--------------

This module participates in the financial-statement pipeline: provider response, normalization, cache/repository coordination, canonical line-item resolution, and analytical input construction.

Public objects
--------------

* **function:** ``normalize_statement_frame`` — Normalize statement axes and numeric values without changing line labels.
* **function:** ``json_value`` — Convert pandas and NumPy scalars into JSON-safe values.
* **function:** ``frame_to_payload`` — Serialize a normalized statement frame to a portable JSON payload.
* **function:** ``frame_from_payload`` — Deserialize one normalized statement frame from a JSON payload.

Detailed reference
------------------

.. automodule:: abaquant.marketdata.financials.normalizer
   :members:
   :show-inheritance:
   :member-order: bysource
