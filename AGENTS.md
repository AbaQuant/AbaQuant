# AGENTS.md

Repository guide for Codex and other coding agents working on AbaQuant.

## Environment

This repository is worked on locally on Windows at:

```text
C:\git\AbaQuant
```

Always use the Conda environment named `quact` for Python commands. Preferred
direct interpreter path:

```powershell
C:\Users\herie\.conda\envs\quact\python.exe
```

Common validation commands:

```powershell
C:\Users\herie\.conda\envs\quact\python.exe -m pytest -q tests
C:\Users\herie\.conda\envs\quact\python.exe -m ruff check .
C:\Users\herie\.conda\envs\quact\python.exe -m ruff format --check .
C:\Users\herie\.conda\envs\quact\python.exe -m compileall -q src examples tests scripts
C:\Users\herie\.conda\envs\quact\python.exe scripts\check_documentation.py
C:\Users\herie\.conda\envs\quact\python.exe -m sphinx -W --keep-going -b html docs docs\_build\html
C:\Users\herie\.conda\envs\quact\python.exe -m build
C:\Users\herie\.conda\envs\quact\python.exe -m twine check dist\*
```

Use `conda run -n quact ...` only when the direct interpreter is unavailable.

## Architecture

AbaQuant is a library-first repository:

```text
src/abaquant/ = distributable Python library
docs/         = Sphinx reStructuredText documentation
examples/     = runnable Python examples
notebooks/    = runnable Jupyter notebooks
tests/        = pytest suite and saved regression results
scripts/      = repository checks and maintenance scripts
```

There is no Streamlit app layer in this repository. Do not reintroduce UI
framework imports, widgets, session-state logic, or page files.

Core library rules:

- Keep mathematical code pure, typed, and presentation-agnostic.
- Market-data providers may perform IO only when retrieval methods are called.
- Visualization code must stay optional and lazy-load Matplotlib or Plotly.
- Public routines should accept Python, NumPy, or pandas data and return primitives, arrays, dictionaries, Series, or DataFrames.
- Avoid global engines, hidden singletons, and UI-coupled algorithms.
- Keep public names English-only.

## Package Areas

```text
src/abaquant/
├── financial_math/
├── derivatives/
├── credit/
├── portfolio/
├── marketdata/
├── rates/
├── reports/
├── risk/
└── visualization/
```

Pre-v1 module families such as ``advanced_derivatives``, ``creditrisk``, and
``portfolioopt`` were removed. Do not restore those compatibility paths.

The root `abaquant` namespace exposes the main mathematical API. Some applied
helpers such as market-data and visualization functions may also be reachable
from `abaquant`, but do not add non-deterministic helper functions to
`abaquant.__all__` if that would force saved-result fixtures for IO or plotting
behavior.

## Market Data And SEC

`abaquant.marketdata` supports optional applied workflows. Keep live providers
lazy and optional.

SEC/XBRL fundamentals use:

```python
from abaquant.marketdata import get_ticker

nvda = get_ticker(
    "NVDA",
    fundamentals_provider="sec",
    sec_user_agent="AbaQuant Research your-email@example.com",
    financial_cache="disk",
    cache_directory="~/.cache/abaquant",
)
```

SEC rules for agents:

- Use a clear SEC User-Agent for live requests.
- Prefer fixture-backed tests for CI; do not require live SEC/network access in pytest.
- Test live SEC manually only as a smoke test, and keep it out of CI.
- SEC cache behavior must support `cache_only`, `if_missing`, `if_stale`, and `refresh`.
- Disk cache should remain versioned, checksum-validated, and atomically written.
- SEC may return gzip or deflate responses; provider code must decode compressed payloads.

Useful SEC checks:

```powershell
C:\Users\herie\.conda\envs\quact\python.exe -m pytest -q tests\test_sec_xbrl_provider.py -vv
C:\Users\herie\.conda\envs\quact\python.exe -m examples.market_data.15_sec_xbrl_fundamentals
```

## Examples And Notebooks

Examples are plain Python scripts under `examples/`.

Notebooks should be clean for readers:

- The first code cell should be just `import abaquant`.
- Prefer `abaquant.function_name(...)` in notebook cells instead of repeated
  `from abaquant... import ...` blocks.
- Do not add repeated `**Result interpretation.**` cells.
- Offline notebooks should be deterministic and avoid live network calls.

Common example commands:

```powershell
C:\Users\herie\.conda\envs\quact\python.exe -m examples.foundations.00_import_all_public_modules
C:\Users\herie\.conda\envs\quact\python.exe -m examples.run_all_deterministic_examples
C:\Users\herie\.conda\envs\quact\python.exe -m examples.run_all_visual_examples
```

Generated outputs such as `examples/generated_figures/`,
`notebooks/generated_figures/`, and `notebook_outputs/` should not be committed.

## Tests

Tests use pytest and live in `tests/`.

The saved regression file is:

```text
tests/fixtures/results.json
```

The naming convention is `results`, not `golden_results`.

Regenerate `results.json` only when a deliberate public API or mathematical
behavior change requires it, and explain the reason. For optimizer outputs,
prefer narrow case-specific tolerances over loosening every saved-result
comparison.

## Dependencies

Core dependencies:

- NumPy 1.23.5 or newer
- pandas 1.5.3 or newer
- SciPy 1.10.1 or newer

Optional extras:

- `market`: yfinance and applied market-data dependencies
- `visual`: Matplotlib and Plotly
- `dev`: pytest and Ruff
- `docs`: Sphinx documentation tooling

CI validates Python 3.11 through 3.14. It also runs a Python 3.11 job with the
exact floors in `requirements/minimum.txt`. Do not lower a dependency floor or
add a Python classifier without a passing compatibility job.

Do not add optional market-data or plotting packages to required dependencies
unless explicitly approved.

## Documentation

Sphinx docs are built from `docs/`.

Do not hand-edit generated HTML in `docs/_build`.

When adding public modules, update the relevant API reference or reStructuredText guides.
Run:

```powershell
C:\Users\herie\.conda\envs\quact\python.exe scripts\check_documentation.py
```

Before a release, build both standard distributions and validate the PyPI long
description with `python -m build` followed by `python -m twine check dist\*`.
Repository metadata and public links target `https://github.com/AbaQuant/AbaQuant`.

## Git Notes

The worktree may already contain modified or untracked files. Do not revert user
changes. Do not run destructive Git commands such as `git reset --hard` or
`git checkout --` unless explicitly asked.

Use `git status --short` before summarizing work, and mention unrelated dirty
files only when they affect the task.

## Coding Style

- Prefer small, stateless functions and focused model classes.
- Add docstrings for public mathematical functions/classes.
- Use existing local patterns before creating new abstractions.
- Catch expected exceptions in library code; avoid broad `except Exception`.
- Keep changes scoped to the request.
- Use `apply_patch` for manual edits.

Above all: keep AbaQuant a clean, distributable Python library.
