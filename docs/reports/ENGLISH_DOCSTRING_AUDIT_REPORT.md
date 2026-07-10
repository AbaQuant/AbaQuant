# English and Docstring Audit Report

This update audits the AbaQuant source snapshot for English-language consistency and documentation coverage.

## Changes

- Translated remaining Spanish user-facing labels to English in financial-math, portfolio-risk, credit-risk, and fixture outputs.
- Replaced Spanish parameter names in exotic-option public signatures with English names, including `option_type`, `position`, and `premium`.
- Replaced Spanish local variable names in bond, cash-flow, and credit-valuation helpers with English names.
- Updated DCF output tables to use English column labels: `Projected FCF`, `Discount Factor`, and `Present Value`.
- Updated beta/regression output tables to use English labels: `Asset`, `Market`, `Asset Excess Return`, and `Market Excess Return`.
- Updated VaR/CVaR summary labels from daily Spanish labels to `daily` English labels.
- Improved selected placeholder-style docstrings in validation and cash-flow helpers.
- Extended the documentation checker with an English-language guard for targeted non-English terms.
- Regenerated deterministic result fixtures after user-facing output labels changed.

## Compatibility note

Most changes are label/docstring/identifier cleanups. The notable public API cleanup is in `abaquant.derivatives.exotics`, where formerly Spanish parameter names were changed to English names. Positional calls remain numerically unchanged.

## Validation

- Compileall passed.
- Documentation and English-language audit passed.
- Full test suite passed.
- Deterministic examples passed.
- Visual examples passed.
