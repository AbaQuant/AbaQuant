# Option Strategy Builder Report

## Summary

Added a composable static option-strategy layer to AbaQuant.

## Public API

- `OptionStrategy`
- `OptionStrategyLeg`
- `OptionStrategy.buy_call(...)`
- `OptionStrategy.sell_call(...)`
- `OptionStrategy.buy_put(...)`
- `OptionStrategy.sell_put(...)`
- `OptionStrategy.buy_underlying(...)`
- `OptionStrategy.sell_underlying(...)`
- `OptionStrategy.payoff(...)`
- `OptionStrategy.gross_payoff(...)`
- `OptionStrategy.profit(...)`
- `OptionStrategy.profile(...)`
- `OptionStrategy.max_profit()`
- `OptionStrategy.max_loss()`
- `OptionStrategy.break_even_points()`
- `OptionStrategy.visualize(...)`

## Predefined constructors

- `OptionStrategy.bull_call_spread(...)`
- `OptionStrategy.protective_put(...)`
- `OptionStrategy.straddle(...)`
- `OptionStrategy.strangle(...)`
- `OptionStrategy.iron_condor(...)`
- `OptionStrategy.butterfly(...)`

## Visualization charts

- `chart="payoff"`
- `chart="components"`

## Notes

The strategy layer is a static expiration analysis tool. It does not model early exercise, margin, assignment, funding, slippage, taxes, or dynamic hedging.

## Validation

- `python -m compileall -q src examples tests scripts`: passed
- `PYTHONPATH=src python scripts/check_documentation.py`: passed
- `PYTHONPATH=src python -m pytest -q tests`: passed, `236 passed`
- `PYTHONPATH=src python examples/00_import_all_public_modules.py`: passed
- `PYTHONPATH=src python examples/run_all_deterministic_examples.py`: passed
- `PYTHONPATH=src python examples/run_all_visual_examples.py`: passed
- `python -m ruff check .`: unavailable in this execution environment
