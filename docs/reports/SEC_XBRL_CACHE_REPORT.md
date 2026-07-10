# SEC/XBRL cache implementation report

## Summary

AbaQuant now caches SEC raw JSON payloads in addition to the normalized financial-statement snapshots. The SEC provider can reuse the ticker-to-CIK mapping and Company Facts JSON across Python sessions when `financial_cache="disk"` is used.

## User-facing behavior

```python
from abaquant.marketdata import get_ticker

nvda = get_ticker(
    "NVDA",
    fundamentals_provider="sec",
    sec_user_agent="AbaQuant Research your-email@example.com",
    financial_cache="disk",
    cache_directory="~/.cache/abaquant",
)

# First call can request SEC data and then save both raw and normalized cache.
inputs = nvda.financials.credit_inputs(source="sec")

# Later sessions can force cache-only behavior.
facts = nvda.financials.sec_facts(refresh_policy="cache_only")
balance = nvda.financials.balance_sheet(source="sec", refresh_policy="cache_only")

status = nvda.financials.sec_cache_status()
```

## Cache layers

- Raw SEC ticker-to-CIK mapping cache.
- Raw SEC Company Facts JSON cache.
- Existing normalized financial-statement snapshot cache.

## Refresh policies

- `cache_only`: never requests SEC; fails if no cache exists.
- `if_missing`: requests only when no cache exists.
- `if_stale`: requests when cache age exceeds the TTL.
- `refresh`: requests a new SEC payload.

## Validation

- `python -m compileall -q src examples tests scripts` passed.
- `python scripts/check_documentation.py` passed.
- `python -m pytest -q tests` passed: 222 passed.
- `python examples/15_sec_xbrl_fundamentals.py` passed.
- `python examples/00_import_all_public_modules.py` passed.
- `python examples/run_all_deterministic_examples.py` passed.
- `python examples/run_all_visual_examples.py` passed.

The deterministic cache tests verify that a second provider instance can read raw SEC Company Facts and normalized SEC statements from disk with zero request attempts.
