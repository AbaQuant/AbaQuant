Release notes
=============

1.0.0rc1
--------

AbaQuant 1.0.0rc1 stabilizes the public namespace and package metadata,
adds root documentation, clarifies the ``parametric_var()`` return
contract, corrects the financial-math example labeling, and hardens
provenance metadata immutability.

Highlights
~~~~~~~~~~

-  Stable v1 imports across derivatives, financial math, market data,
   credit, portfolio, rates, visualization, reports, risk dashboards,
   and core provenance.
-  ``abaquant.derivatives.advanced`` provides the supported
   advanced-model import path.
-  Root package exports now include market-data, visualization, and
   financial-math facades consistently.
-  ``README.md``, ``CHANGELOG.md``, and expanded Sphinx/reStructuredText
   documentation are included in the source snapshot.
-  CI validates Python 3.10 through 3.13, the tested minimum dependency set,
   both standard distribution formats, and the PyPI long description.
-  A generated, hierarchical API reference covers every source module and
   documents public functions, classes, methods, properties, parameters, return
   values, exceptions, and type hints from the canonical docstrings.
-  Deterministic examples cover derivatives, financial math, credit,
   portfolio optimization, market-data facades, FRED-style rate curves,
   option-chain analytics, option strategies, backtesting, dashboards,
   reports, calibration, and provenance.

Compatibility notes
~~~~~~~~~~~~~~~~~~~

-  The old top-level advanced derivatives namespace is not part of the
   v1 API.
-  Live provider workflows remain optional and may require optional
   dependencies, credentials, contact metadata, and network
   availability.
-  Generated figures and reports are presentation artifacts; numerical
   objects remain the source of truth.

Validation commands
~~~~~~~~~~~~~~~~~~~

.. code:: bash

   python scripts/generate_api_docs.py
   python -m compileall -q src tests examples docs scripts
   python -m ruff format --check .
   python -m ruff check .
   python -m pytest
   python scripts/check_documentation.py
   python -m sphinx -W --keep-going -b html docs docs/_build/html
   python -m examples.run_all_deterministic_examples
   python -m examples.run_all_visual_examples
   python -m build
   python -m twine check dist/*
