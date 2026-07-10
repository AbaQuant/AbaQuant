# Contributing to AbaQuant

Thank you for helping improve AbaQuant. Contributions should preserve the
library-first architecture: numerical and actuarial routines belong under
`src/abaquant`, while network providers and visual backends remain optional.

## Development setup

Create or activate a Python 3.11–3.14 environment, then install all development
extras:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev,docs,market,visual]"
```

Repository maintainers working on the project’s Windows workstation use the
Conda environment named `quact`; that local convention is not required for
external contributors.

## Before opening a pull request

Run the same checks as CI:

```bash
python -m ruff format --check .
python -m ruff check .
python -m pytest
python scripts/check_documentation.py
python -m sphinx -W --keep-going -b html docs docs/_build/html
python -m build
python -m twine check dist/*
```

Format intentional Python changes with `python -m ruff format .`. Add focused,
deterministic tests for behavioral changes. Live Yahoo, SEC, and FRED requests
must not be required by CI; use injected providers or fixtures instead.

## Public API changes

Read `docs/reference/api_stability.rst` before changing imports, signatures, or
defaults. Public facade changes need documentation, tests, and an entry in
`CHANGELOG.md`. Regenerate API pages with:

```bash
python scripts/generate_api_docs.py
```

## Pull requests

Keep pull requests focused and explain the financial convention, numerical
method, and compatibility impact where relevant. Do not commit credentials,
provider caches, generated documentation builds, figures, or distribution
artifacts.
