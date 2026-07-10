# Option-chain analytics implementation report

## Summary

AbaQuant now includes provider-independent listed-option-chain analytics that connect raw option-chain data to implied-volatility, liquidity, and model-comparison diagnostics.

## Public API

```python
chain = nvda.options.chain(expiry="2027-01-15")
chain_analytics = nvda.options.analytics(expiry="2027-01-15")

smile = chain_analytics.iv_smile(option_type="call")
surface = chain_analytics.iv_surface(option_type="call")
skew = chain_analytics.skew(option_type="put")
term = chain_analytics.term_structure(strike=100.0, option_type="call")
rich_cheap = chain_analytics.rich_cheap_table(model="bsm", risk_free_rate=0.04)
open_interest = chain_analytics.open_interest_grid(option_type="put")
```

Visualizations:

```python
chain_analytics.visualize(chart="iv_smile", option_type="call")
chain_analytics.visualize(chart="iv_surface", option_type="call")
chain_analytics.visualize(chart="term_structure", option_type="call", strike=100.0)
chain_analytics.visualize(chart="rich_cheap", option_type="call", risk_free_rate=0.04)
chain_analytics.visualize(chart="open_interest_heatmap", option_type="put")
```

## Added objects

- `OptionChainAnalytics`
- `OptionSkewSummary`
- `visualize_option_chain_analytics`

## Analytics added

- Implied-volatility smile by strike and moneyness.
- Long-form implied-volatility surface across expirations.
- Linear implied-volatility skew against log-moneyness.
- Implied-volatility term structure at a target strike.
- Black--Scholes--Merton rich/cheap comparison against listed market premiums.
- Open-interest grid for heatmap visualization.

## Examples updated

- `examples/06_marketdata_offline.py`
- `examples/09_visualizations.py`
- `examples/11_visualize_method_gallery.py`
- `examples/17_option_chain_analytics.py`
- `examples/README.md`
- `examples/MODULE_COVERAGE.md`

## Validation

- `python -m compileall -q src examples tests scripts` passed.
- `python scripts/check_documentation.py` passed.
- `python -m pytest -q tests` passed: 230 tests.
- `python examples/00_import_all_public_modules.py` passed.
- `python examples/17_option_chain_analytics.py` passed.
- `python examples/run_all_deterministic_examples.py` passed.
- `python examples/run_all_visual_examples.py` passed.
- `python -m ruff check .` could not run because Ruff was unavailable in the execution environment.
