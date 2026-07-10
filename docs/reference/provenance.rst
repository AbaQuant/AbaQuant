Provenance
==========

Provenance is the metadata layer that explains where data came from,
when it was retrieved, how it was cached, and what transformations were
applied.

Core object
-----------

.. code:: python

   from abaquant.core import DataProvenance

   provenance = DataProvenance(
       provider="manual",
       dataset="portfolio_returns",
       request={"symbols": ["ALPHA", "BETA"]},
       transformation_steps=("manual construction", "return calculation"),
       currency="USD",
       reporting_date="2025-12-31",
   )

Typical fields:

+-----------------------------------+-----------------------------------+
| Field                             | Meaning                           |
+===================================+===================================+
| ``provider``                      | Data source or construction       |
|                                   | source, such as ``manual``,       |
|                                   | ``fred``, ``sec``, or ``yahoo``.  |
+-----------------------------------+-----------------------------------+
| ``dataset``                       | Logical dataset name.             |
+-----------------------------------+-----------------------------------+
| ``retrieved_at_utc``              | UTC retrieval or construction     |
|                                   | timestamp.                        |
+-----------------------------------+-----------------------------------+
| ``cache_status``                  | Cache behavior such as hit, miss, |
|                                   | refreshed, or manual.             |
+-----------------------------------+-----------------------------------+
| ``source_labels``                 | Provider series, symbols, forms,  |
|                                   | statements, or other source       |
|                                   | identifiers.                      |
+-----------------------------------+-----------------------------------+
| ``request``                       | Structured request metadata.      |
+-----------------------------------+-----------------------------------+
| ``transformation_steps``          | Ordered descriptions of           |
|                                   | transformations.                  |
+-----------------------------------+-----------------------------------+
| ``currency``                      | Reporting or valuation currency.  |
+-----------------------------------+-----------------------------------+
| ``reporting_date``                | Statement, curve, or observation  |
|                                   | date.                             |
+-----------------------------------+-----------------------------------+

Immutability
------------

``DataProvenance`` is designed to be immutable enough for safe
attachment to pandas metadata, report objects, and derived results.
Nested dictionaries are normalized into read-only mappings; nested
mutable sequences are normalized into immutable tuples.

.. code:: python

   metadata = provenance.as_dict()

Use ``as_dict()`` when serializing provenance to JSON-like output.

Merge provenance
----------------

.. code:: python

   from abaquant.core import merge_provenance

   combined = merge_provenance([curve.provenance, assessment.provenance])

Merging is useful when one derived object depends on multiple inputs,
such as:

-  an option report using a rate curve;
-  a portfolio dashboard using returns and credit assessments;
-  a credit report using cached SEC facts and normalized statement
   tables;
-  a backtest report using benchmark and transaction-cost assumptions.

DataFrame provenance
--------------------

.. code:: python

   from abaquant.core import provenance_from_dataframe

   prov = provenance_from_dataframe(
       returns,
       provider="manual",
       dataset="returns",
       request={"frequency": "daily"},
   )

This records table shape and supplied metadata without requiring a
provider request.

Audit pattern
-------------

For reproducible research, store four objects together:

.. code:: text

   result object
   input parameters
   provenance metadata
   package version

This makes it easier to answer:

-  which provider supplied the data;
-  whether the result came from cache;
-  what date or reporting period was used;
-  which transformations occurred;
-  which AbaQuant version generated the result.

Limitations
-----------

Provenance records explain computational lineage. They do not guarantee
provider correctness, data licensing compliance, economic validity, or
absence of look-ahead bias.
