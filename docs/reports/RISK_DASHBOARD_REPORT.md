# AbaQuant Risk Dashboard Report

## Implemented API

The risk dashboard layer adds a cohesive object that combines portfolio/backtest diagnostics, volatility risk contribution, drawdown, asset correlation, and synthetic credit proxy scores.

```python
from abaquant import RiskDashboard

dashboard = RiskDashboard(
    portfolio=allocator,
    credit_assessments={"NVDA": nvda_credit, "MSFT": msft_credit},
)

summary = dashboard.summary()
risk_table = dashboard.risk_contribution()
credit_table = dashboard.credit_scores()
correlation = dashboard.correlation()
```

## Visualization API

```python
dashboard.visualize(chart="risk_contribution")
dashboard.visualize(chart="drawdown")
dashboard.visualize(chart="credit_scores")
dashboard.visualize(chart="correlation")
```

The object also exposes `visual_report()` for creating a bundle of the main figures.

## Main files changed

- `src/abaquant/risk/dashboard.py`
- `src/abaquant/visualization/dashboard.py`
- `src/abaquant/visualization/__init__.py`
- `src/abaquant/__init__.py`
- `examples/20_risk_dashboard.py`
- `examples/00_import_all_public_modules.py`
- `examples/run_all_deterministic_examples.py`
- `examples/run_all_visual_examples.py`
- `examples/README.md`
- `examples/MODULE_COVERAGE.md`
- `tests/test_risk_dashboard.py`

## Validation

- `python -m compileall -q src examples tests scripts` passed.
- `PYTHONPATH=src python scripts/check_documentation.py` passed.
- `PYTHONPATH=src python -m pytest -q tests` passed: `249 passed`.
- `PYTHONPATH=src python examples/00_import_all_public_modules.py` passed.
- `PYTHONPATH=src python examples/20_risk_dashboard.py` passed.
- `PYTHONPATH=src python examples/run_all_deterministic_examples.py` passed.
- `PYTHONPATH=src python examples/run_all_visual_examples.py` passed.
- `python -m ruff check .` could not run because Ruff is not installed in this environment.
