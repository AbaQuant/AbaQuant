# SEC/XBRL Fundamentals Provider Report

## Summary

This update adds an SEC EDGAR/XBRL fundamentals provider for AbaQuant. The
provider retrieves SEC Company Facts JSON, converts selected US-GAAP and DEI
facts into AbaQuant's canonical financial-statement tables, and feeds the
existing grouped credit-input and credit-proxy pipeline.

## Public API

```python
from abaquant.marketdata import get_ticker

nvda = get_ticker(
    "NVDA",
    fundamentals_provider="sec",
    sec_user_agent="AbaQuant Research contact@example.com",
)

facts = nvda.financials.sec_facts()
balance_sheet = nvda.financials.balance_sheet(source="sec")
inputs = nvda.financials.credit_inputs(source="sec")
assessment = nvda.credit.assess_from_financials(source="sec")
```

## Files changed

- `src/abaquant/marketdata/providers/sec.py`
- `src/abaquant/marketdata/providers/__init__.py`
- `src/abaquant/marketdata/providers/financial_statements.py`
- `src/abaquant/marketdata/ticker.py`
- `src/abaquant/marketdata/financials/facade.py`
- `src/abaquant/marketdata/financials/repository.py`
- `src/abaquant/marketdata/financials/cache.py`
- `tests/test_sec_xbrl_provider.py`
- `examples/15_sec_xbrl_fundamentals.py`
- `examples/00_import_all_public_modules.py`
- `examples/run_all_deterministic_examples.py`
- `examples/README.md`
- `examples/MODULE_COVERAGE.md`

## Design notes

- Yahoo remains the default provider for quotes, prices, and options.
- SEC can be selected as the fundamentals-only provider.
- The SEC provider uses the Company Facts endpoint and CIK/ticker mapping.
- Disk cache paths now include the provider namespace so Yahoo and SEC financial
  snapshots cannot collide.
- SEC-derived frames use AbaQuant's existing canonical line-item labels so the
  existing credit input builder works unchanged.
- Missing facts stay missing; EBITDA is not inferred from partial tags.

## Validation

- `python -m compileall -q src examples tests scripts` passed.
- `python scripts/check_documentation.py` passed.
- `python -m pytest -q tests` passed: 220 passed.
- `python examples/00_import_all_public_modules.py` passed.
- `python examples/15_sec_xbrl_fundamentals.py` passed.
- `python examples/run_all_deterministic_examples.py` passed.
- `python examples/run_all_visual_examples.py` passed.
- ZIP integrity was verified after packaging.
