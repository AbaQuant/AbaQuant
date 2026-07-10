abaquant.core.provenance
========================

**Import path:** ``abaquant.core.provenance``

**Domain:** Auditability and metadata primitives.

Purpose
-------

Provider-neutral data provenance metadata for AbaQuant objects.

When to use it
--------------

Use these objects when results must retain provider, cache, request, currency, reporting-date, and transformation information.

Public objects
--------------

* **class:** ``DataProvenance`` — Immutable metadata describing how a dataset or result was produced.
  * ``DataProvenance.as_dict`` — Return a JSON-serializable provenance dictionary.
  * ``DataProvenance.with_step`` — Return a copy with one additional transformation step appended.
  * ``DataProvenance.from_dict`` — Build a provenance object from a saved dictionary payload.
* **class:** ``ProvenanceMixin`` — Mixin for objects that expose a ''provenance'' metadata attribute.
  * ``ProvenanceMixin.provenance_dict`` — Return this object's provenance as a plain dictionary.
* **function:** ``utc_now_iso`` — Return the current UTC timestamp in second precision.
* **function:** ``provenance_from_dataframe`` — Build provenance with shape metadata for a tabular object.
* **function:** ``merge_provenance`` — Combine several provenance records into one derived record.

Detailed reference
------------------

.. automodule:: abaquant.core.provenance
   :members:
   :show-inheritance:
   :member-order: bysource
