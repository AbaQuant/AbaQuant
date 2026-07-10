# Documentation overhaul

This source snapshot first received documentation improvements and then a
compatibility-preserving naming refactor. Numerical algorithms, public output
schemas, and provider boundaries remain unchanged. Where a public constructor
was renamed, the previous constructor form remains available through a wrapper
or alias.

## Included changes

- Every Python module opens with a substantive English-language docstring.
- Module docstrings state purpose, conventions, scope, limitations, and primary references.
- Every function, method, nested numerical objective, and class receives a NumPy-style docstring.
- Public arguments and return values are documented using finance-aware units and conventions.
- Spanish prose docstrings and explanatory comments were translated to English while legacy identifiers and public data labels were preserved.
- A portable bibliography and package landing pages were added under `docs/`.
- `tools/check_documentation.py` provides an AST-based regression check that does not import optional providers.

## Naming compatibility rule

Descriptive canonical classes and attributes are now preferred. Legacy class
names, constructor signatures, symbolic model attributes, DataFrame schemas,
result keys, and output labels remain available. See
``docs/NAMING_MIGRATION.md`` for the compatibility map.

## Phase 3 manual fundamental credit proxies

- Added provider-independent `FundamentalCreditInputs` and `CreditProxyAssessment`.
- Added transparent manual calculations for liquidity, leverage, coverage,
  cash-flow, Altman Z-score, Piotroski F-score, earnings volatility, leverage
  trend, and a clearly labeled coverage-normalized synthetic proxy score.
- Added `MarketTicker.credit.assess(...)`, `proxy_metrics(...)`,
  `synthetic_score(...)`, `altman_z_score(...)`, and `piotroski_f_score(...)`.
- Added Phase 3 documentation and canonical Altman/Piotroski bibliography entries.

## Phase 3.1: cached provider-fed financial statements

- Added `MarketTicker.financials`, which retrieves income, balance-sheet, and
  cash-flow tables together and exposes canonical line-item methods such as
  `total_debt()`, `ebitda()`, and `operating_cash_flow()`.
- Added memory and optional disk caches for normalized statement snapshots.
- Added explicit cache policies and cache-status/clear-cache methods.
- Added `credit_inputs()` and `credit.assess_from_financials()` while retaining
  the manual `FundamentalCreditInputs` path unchanged.
- Updated the Yahoo adapter to import `yfinance` only on its first data request.

## Examples coverage update

- Added an `examples/` suite with deterministic workflows for derivatives, financial mathematics, advanced derivatives, credit risk, portfolio optimization, root facades, and offline market-data usage.
- Added `00_import_all_public_modules.py` to import all public modules without network access.
- Added `07_marketdata_live_cached_financials.py` as an opt-in yfinance/disk-cache workflow.
- Added `MODULE_COVERAGE.md` mapping every public module to its example coverage.
- Added `run_all_deterministic_examples.py` for an end-to-end synthetic-data smoke run.

## Visualization API

- Added optional backend-neutral visualization package.
- Added domain-specific `visualize()` methods for option-pricing models, portfolio allocation, credit assessments, tickers, universes, financial statement façades, and financial snapshots.
- Added `examples/09_visualizations.py`, `docs/VISUALIZATION.md`, visualization smoke tests, and implementation report.

## Visualization themes and export policies

- Added reusable global `VisualizationTheme` configuration.
- Added global and scoped theme APIs, configurable backends, palettes, fonts,
  dimensions, resolutions, background/grid appearance, and export settings.
- Updated all supported visualizations to accept per-call theme and save
  overrides.
- Added theme documentation, deterministic tests, and a complete example.

- Expanded examples with direct visualization-method coverage and added the complete visualization gallery.
