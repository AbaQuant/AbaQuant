# Scenario analysis implementation report

## Summary

This phase makes scenario analysis a first-class AbaQuant workflow across three
families:

1. derivative spot--volatility grids;
2. portfolio one-period asset shock analysis;
3. fundamental credit proxy multiplier grids.

The implementation follows the common pattern:

```text
base case -> scenario grid -> visual report
```

## Public API

### Derivatives

```python
scenario = option_model.scenario_grid(
    spot_prices=[80, 90, 100, 110, 120],
    volatilities=[0.15, 0.20, 0.25, 0.30],
    option_type="call",
)

scenario.data
scenario.pivot("price")
scenario.visualize(metric="delta", chart="heatmap")
scenario.visualize(metric="price", chart="surface")
```

### Portfolios

```python
scenario = allocator.scenario_analysis(
    shocks={"NVDA": -0.20, "MSFT": -0.10, "AAPL": -0.15},
    weights={"NVDA": 0.50, "MSFT": 0.30, "AAPL": 0.20},
    base_value=1_000_000,
)

scenario.as_frame()
scenario.portfolio_return
scenario.ending_value
scenario.visualize(chart="contributions")
```

### Credit proxies

```python
scenario = assessment.scenario_analysis(
    debt_multiplier=[1.0, 1.25, 1.50],
    ebitda_multiplier=[1.0, 0.75, 0.50],
)

scenario.data
scenario.visualize(metric="synthetic_credit_proxy_score", chart="heatmap")
```

## Files changed

- `src/abaquant/advanced_derivatives/models/diagnostics.py`
- `src/abaquant/advanced_derivatives/models/__init__.py`
- `src/abaquant/portfolioopt/optimization.py`
- `src/abaquant/portfolioopt/__init__.py`
- `src/abaquant/creditrisk/fundamentals.py`
- `src/abaquant/creditrisk/__init__.py`
- `src/abaquant/marketdata/universe_portfolio.py`
- `src/abaquant/visualization/options.py`
- `src/abaquant/visualization/portfolio.py`
- `src/abaquant/visualization/credit.py`
- `src/abaquant/visualization/__init__.py`
- `examples/14_scenario_analysis.py`
- `examples/run_all_deterministic_examples.py`
- `examples/run_all_visual_examples.py`
- `examples/README.md`
- `examples/MODULE_COVERAGE.md`
- `tests/test_scenario_analysis.py`
- `scripts/check_documentation.py`

## Validation

The following checks were run from the package snapshot with `PYTHONPATH=src`:

```bash
python -m compileall -q src examples tests scripts
python scripts/check_documentation.py
python -m pytest -q tests
python examples/00_import_all_public_modules.py
python examples/14_scenario_analysis.py
python examples/run_all_deterministic_examples.py
python examples/run_all_visual_examples.py
```

Results:

- `pytest`: 217 passed.
- Documentation audit: passed.
- Deterministic and visual example runners: passed.
- ZIP integrity: checked after packaging.
