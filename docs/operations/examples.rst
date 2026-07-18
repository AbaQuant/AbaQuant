Examples
========

The ``examples/`` directory is the executable tutorial layer. Its seven domain
packages mirror ``examples_notebooks/`` and the Examples menu in this
documentation.

Run the suites
--------------

Run commands from the repository root with AbaQuant installed:

.. code:: bash

   python -m examples.run_all_deterministic_examples
   python -m examples.run_all_visual_examples

Domain map
----------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Package
     - Coverage
   * - ``examples.foundations``
     - Public imports, root facades, and provenance.
   * - ``examples.financial_math_and_rates``
     - Time value, rates, annuities, bonds, corporate finance, and FRED curves.
   * - ``examples.derivatives``
     - Vanilla and advanced pricing, option-chain analytics, strategies, and calibration.
   * - ``examples.credit``
     - Credit proxies, transitions, CDS, CDO, copulas, and statement bridges.
   * - ``examples.portfolio_and_risk``
     - Optimization, scenario analysis, backtesting, and integrated dashboards.
   * - ``examples.market_data``
     - Offline and optional live ticker, financial-statement, SEC, and universe workflows.
   * - ``examples.visualization_and_reports``
     - Theme configuration, visualization galleries, and report export.

Run one example
---------------

Individual files are Python modules. For example:

.. code:: bash

   python -m examples.derivatives.01_derivatives
   python -m examples.market_data.06_marketdata_offline
   python -m examples.portfolio_and_risk.19_portfolio_backtesting

The live Yahoo example is optional and may make network requests:

.. code:: bash

   python -m examples.market_data.07_marketdata_live_cached_financials

Artifacts
---------

Figures and reports are written under ``examples/generated_figures/`` and
``examples/generated_reports/``. Examples return figures and do not call
``show()`` automatically.

Determinism policy
------------------

Examples should prefer deterministic fixtures over live providers. Any example
that can make a network request must say so and remain optional.
