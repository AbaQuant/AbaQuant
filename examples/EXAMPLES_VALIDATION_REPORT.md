# Examples validation report

## Scope

The examples folder was refactored from long linear scripts into tutorial-style
modules with small functions and explicit `run()` entry points.

## Structural validation

- Every deterministic example compiles.
- The core deterministic runner executes in one Python process.
- The visualization runner executes in one Python process.
- Generated Matplotlib figures are closed between scripts to avoid resource warnings.
- Matplotlib figures export as SVG, with dense surface and heatmap artists rasterized.
- Every example accesses the installed library through `import abaquant as aq`.
- No example modifies `sys.path` or injects the repository's `src` directory.

## Commands run

```bash
python -m compileall -q examples
python -m pytest
python -m examples.run_all_deterministic_examples
python -m examples.run_all_visual_examples
```

## Results

- Example compilation: passed.
- Test suite: passed.
- Core deterministic examples: passed.
- Visualization examples: passed.

## Notes

`market_data/07_marketdata_live_cached_financials.py` remains intentionally outside the
deterministic runner because it can require `yfinance`, network access, and a
provider response from Yahoo Finance.
