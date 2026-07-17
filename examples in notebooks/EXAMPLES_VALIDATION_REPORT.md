# Examples validation report

## Scope

The examples folder was refactored from long linear scripts into tutorial-style
modules with small functions and explicit `run()` entry points.

## Structural validation

- Every deterministic example compiles.
- The core deterministic runner executes in one Python process.
- The visualization runner executes in one Python process.
- Generated Matplotlib figures are closed between scripts to avoid resource warnings.
- Examples can run from the flat source snapshot using `_shared/package_bootstrap.py`.

## Commands run

```bash
python -m compileall -q .
python tools/check_documentation.py
PYTHONPATH=/mnt/data/test_alias python -m pytest -q tests
python examples/run_all_deterministic_examples.py
python examples/run_all_visual_examples.py
```

## Results

- Source compilation: passed.
- Documentation audit: passed.
- Tests: `11 passed` using a temporary `abaquant` package alias for the flat archive layout.
- Core deterministic examples: passed.
- Visualization examples: passed.

## Notes

`07_marketdata_live_cached_financials.py` remains intentionally outside the
deterministic runner because it can require `yfinance`, network access, and a
provider response from Yahoo Finance.
