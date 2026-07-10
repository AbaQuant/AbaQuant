# Examples Validation Report

## Added coverage

The `examples/` directory contains:

- `00_import_all_public_modules.py`: imports all 75 public module paths without requesting provider data.
- `01_derivatives.py`: vanilla, tree, forward, strategy, and exotic derivative workflows.
- `02_financial_math.py`: time-value, annuities, bonds, cash flows, corporate finance, equity valuation, loans, rates, risk, and portfolio primitives.
- `03_advanced_derivatives.py`: analytical engines, numerical implied volatility, simulation, Monte Carlo, and analytics. Calibration modules are imported and shown as explicit opt-in because they are materially more expensive.
- `04_credit_risk.py`: transition matrices, copula thresholds, distributions, valuation, CDS, CDO, risk metrics, and fundamental credit proxies.
- `05_portfolio_optimization.py`: return preparation, optimization, efficient frontier, risk metrics, HRP, solver, stress tests, and backtest.
- `06_marketdata_offline.py`: fake-provider ticker/options/financial cache/credit assessment and multi-ticker universe workflow without yfinance or network access.
- `07_marketdata_live_cached_financials.py`: opt-in Yahoo/yfinance cached statement retrieval.
- `08_root_facades.py`: legacy root `credit` and `rates` façade modules.
- `run_all_deterministic_examples.py`: executes all deterministic examples.

## Validation performed

- `python -m compileall -q .`: passed.
- `00_import_all_public_modules.py`: passed; imported 75 public modules with no live data request.
- `run_all_deterministic_examples.py`: passed.
- The live Yahoo/yfinance example was intentionally not executed because it requires optional dependencies and network access.

## Constraints

Examples use synthetic data by default. They are demonstrations of API usage, not financial, trading, or credit advice.
