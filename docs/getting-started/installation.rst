Installation
============

AbaQuant requires Python **3.11 or newer**.

Standard installation
---------------------

.. code-block:: bash

   pip install abaquant

For a local source checkout:

.. code-block:: bash

   python -m pip install -e .

Optional extras
---------------

AbaQuant keeps provider and visualization dependencies optional so the
core numerical package remains lightweight.

.. list-table:: Optional dependency groups
   :header-rows: 1
   :widths: 18 42 40

   * - Extra
     - Command
     - Adds
   * - Market data
     - ``python -m pip install -e .[market]``
     - ``yfinance`` for optional Yahoo-backed workflows.
   * - Visualization
     - ``python -m pip install -e .[visual]``
     - Matplotlib and Plotly chart backends.
   * - Development
     - ``python -m pip install -e .[dev]``
     - Pytest and Ruff.
   * - Documentation
     - ``python -m pip install -e .[docs]``
     - Sphinx, Furo, copy buttons, and autobuild tooling.

Install multiple extras by separating them with commas:

.. code-block:: bash

   python -m pip install -e .[market,visual,dev,docs]

Verify the installation
-----------------------

.. code-block:: bash

   python - <<'PY'
   import abaquant
   print(abaquant.__version__)
   from abaquant.derivatives import black_scholes
   print(round(black_scholes(100, 100, 0.05, 0.20, 1.0), 6))
   PY

Expected version:

.. code-block:: text

   1.0.0rc1

Build documentation locally
---------------------------

Documentation is written as Sphinx-native reStructuredText and organized
into topic subfolders.

.. code-block:: bash

   python -m pip install -e .[docs]
   sphinx-build -b html docs docs/_build/html

Open the generated site:

.. code-block:: bash

   python -m webbrowser docs/_build/html/index.html

Provider credentials and contact metadata
-----------------------------------------

Live data workflows can require provider-specific credentials or contact
metadata.

For SEC EDGAR/XBRL usage, set a project-specific contact user agent:

.. code-block:: bash

   export ABAQUANT_SEC_USER_AGENT="your-app/1.0 your.email@example.com"

For FRED usage, pass an API key to the FRED provider or configure the
environment according to your deployment pattern.

.. warning::

   Provider responses can be delayed, adjusted, restated, rate-limited,
   incomplete, or unavailable. Cache live data deliberately and record
   provenance for reproducibility.
