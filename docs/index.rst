AbaQuant documentation
======================

AbaQuant **1.0.0rc1** is an applied actuarial and quantitative-finance
library for Python. It combines pricing models, financial mathematics,
market-data facades, credit analytics, portfolio construction, rate
curves, visualizations, exportable reports, and provenance-aware result
objects.

The documentation is now organized as Sphinx-native reStructuredText
rather than Markdown. Pages are grouped by task and domain so the tree can
scale without becoming a flat list.

.. important::

   AbaQuant outputs are model-derived estimates. They are not investment
   advice, credit ratings, trading signals, legal advice, accounting
   advice, or tax advice.

Documentation map
-----------------

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Section
     - Purpose
   * - :doc:`getting-started/index`
     - Installation, first workflows, conventions, units, rates, signs, and return assumptions.
   * - :doc:`reference/index`
     - Architecture, stable public imports, and provenance model.
   * - :doc:`api/index`
     - Function-level reference for every source module, including signatures, parameters, returns, methods, and properties.
   * - :doc:`domains/index`
     - Derivatives, financial math, portfolio, credit, market data, rates, visualization, reports, and assumptions.
   * - :doc:`operations/index`
     - Example gallery and workflow selection guide.
   * - :doc:`development/index`
     - Validation workflow, release checklist, and v1.0.0rc1 release notes.

Core workflow
-------------

::

   market data or manual inputs
           |
           v
   models, allocators, rate curves, credit inputs
           |
           v
   analytics, scenario grids, calibration, backtests
           |
           v
   visualizations, reports, dashboards
           |
           v
   provenance metadata for auditability

.. toctree::
   :maxdepth: 2
   :caption: Getting started

   getting-started/index

.. toctree::
   :maxdepth: 2
   :caption: Reference

   reference/index

.. toctree::
   :maxdepth: 3
   :caption: Complete API reference

   api/index

.. toctree::
   :maxdepth: 2
   :caption: Analytical domains

   domains/index

.. toctree::
   :maxdepth: 2
   :caption: Operations

   operations/index

.. toctree::
   :maxdepth: 3
   :caption: Examples

   notebooks/index

.. toctree::
   :maxdepth: 2
   :caption: Development

   development/index
