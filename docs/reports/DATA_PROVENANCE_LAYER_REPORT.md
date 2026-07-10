# AbaQuant Data Provenance Layer

## Summary

This update adds a provider-neutral provenance layer across AbaQuant so derived and provider-backed objects can explain where their data came from, when it was retrieved or constructed, how cache was used, which source labels were transformed, and what reporting conventions apply.

## New public object

- `DataProvenance`
  - `provider`
  - `dataset`
  - `retrieved_at_utc`
  - `cache_status`
  - `source_labels`
  - `currency`
  - `reporting_date`
  - `transformation_steps`
  - `request`
  - `notes`
  - `as_dict()`
  - `from_dict(...)`
  - `with_step(...)`

## Objects now carrying `.provenance`

- `MarketTicker`
- `DerivativeDiagnosticsReport`
- `DerivativeScenarioGrid`
- `RateCurve`
- `SecCompanyFacts`
- `FinancialStatementSnapshot`
- `CreditAnalysisInputs`
- `CreditProxyAssessment`
- `CreditScenarioAnalysis`
- `OptionChainAnalytics`
- `PortfolioScenarioAnalysis`
- `PortfolioAllocator.context`
- `PortfolioBacktestResult`
- `CalibrationResult`
- `RiskDashboard`
- `ExportableReport`

## Tabular data provenance

For pandas DataFrames where wrapping the return value would break the public API, provenance is attached under `frame.attrs["provenance"]`:

- market price history
- listed option chains

## Cache and provider coverage

The layer includes provenance for:

- Yahoo-style market history and option-chain DataFrames through DataFrame attrs
- SEC Company Facts and SEC-backed financial-statement snapshots
- FRED/manual rate curves
- cached financial-statement snapshots
- option-chain analytics
- portfolio optimization inputs and backtests
- calibration outputs
- exportable reports
- integrated risk dashboards

## Example

```python
from abaquant.rates import RateCurve

curve = RateCurve.from_rates({0.5: 0.04, 1.0: 0.045})

curve.provenance.provider
curve.provenance.dataset
curve.provenance.as_dict()
```

## Validation

The update adds `tests/test_data_provenance.py` and `examples/23_data_provenance.py`.
