Development and release checks
==============================

This page documents the local checks maintainers should run before
publishing a source snapshot or wheel.

Core checks
-----------

.. code:: bash

   python scripts/generate_api_docs.py
   python -m compileall -q src tests examples docs scripts
   python -m ruff format --check .
   python -m ruff check .
   python -m pytest
   python scripts/check_documentation.py
   python -m sphinx -W --keep-going -b html docs docs/_build/html
   PYTHONPATH=src python examples/run_all_deterministic_examples.py
   PYTHONPATH=src python examples/run_all_visual_examples.py
   python -m build
   python -m twine check dist/*

Supported Python versions
-------------------------

CI runs the complete release checks on Python 3.11, 3.12, 3.13, and
3.14. A separate Python 3.11 job constrains NumPy, pandas, and SciPy to the
versions in ``requirements/minimum.txt``. A version classifier or dependency
floor is changed only after that environment passes.

Python 3.14 is part of the supported matrix and must pass the complete
release suite before publication.

Type checking is being introduced incrementally after v1. It is not a release
gate until the complete package passes without broad error suppressions.

Documentation audit
-------------------

``scripts/generate_api_docs.py`` mirrors the Python package tree under
``docs/api/`` and creates one RST page for every module or package. Each
implementation page includes a public-symbol inventory plus an ``automodule``
directive.

``scripts/check_documentation.py`` performs an AST-based docstring audit,
rejects known placeholder forms, requires documentation for public properties,
and verifies that every source module has a matching API page with the correct
``automodule`` directive. It is a regression guard, not a complete
natural-language quality evaluator.

Example policy
--------------

Examples should:

1. run from an installed package or source checkout;
2. prefer deterministic data;
3. avoid network access unless explicitly documented;
4. expose a ``run()`` function;
5. print compact summaries instead of huge tables;
6. save figures rather than calling ``show()`` automatically;
7. be suitable for smoke tests.

Release artifact checklist
--------------------------

Before publishing:

-  verify ``pyproject.toml`` version;
-  verify ``abaquant.__version__``;
-  verify root ``README.md`` renders as package long description;
-  verify ``CHANGELOG.md`` contains the release entry and release date;
-  verify the old top-level advanced derivatives path is not
   accidentally restored;
-  verify stable namespace imports;
-  verify both the standard source distribution and wheel;
-  run ``python -m twine check dist/*``;
-  install the built wheel into a clean target directory and import it.

Versioning policy
-----------------

AbaQuant follows semantic-versioning intent:

+-----------------------------------+-----------------------------------+
| Change                            | Version impact                    |
+===================================+===================================+
| Backward-compatible bug fix       | patch release.                    |
+-----------------------------------+-----------------------------------+
| Backward-compatible new feature   | minor release.                    |
+-----------------------------------+-----------------------------------+
| Public API break                  | major release.                    |
+-----------------------------------+-----------------------------------+
| Internal refactor preserving      | patch or minor release depending  |
| documented imports                | on risk.                          |
+-----------------------------------+-----------------------------------+

API stability guidelines
------------------------

-  See :doc:`../reference/api_stability` for the complete policy.
-  Public facade namespaces should preserve documented imports.
-  Private helper names beginning with ``_`` are not stable.
-  Provider cache internals are not stable.
-  Chart aesthetics can change between minor versions.
-  Numerical default tolerances should be changed carefully and
   documented when they affect outputs.
