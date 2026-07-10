# Breaking architecture refactor

This release intentionally removes all prior compatibility aliases and legacy
constructor forms.

## Removed names

- `*Engine` pricing class names and abbreviated model aliases
- `AppliedTicker` and `AppliedUniverse`
- `StaticPortfolioOptimizer` and `PortfolioOptimizer`
- `FundamentalCreditInputs`
- dynamic symbolic model attributes such as `S`, `K`, `T`, `r`, `q`, and
  `sigma`

## New canonical structure

- `MarketTicker` uses `TickerIdentity`, `TickerConfiguration`, and
  `TickerSession`.
- `MarketUniverse` uses `UniverseSession`.
- `FinancialStatements` delegates to `FinancialStatementRepository`,
  `FinancialStatementCacheStore`, normalizers, and a line-item resolver.
- `CreditAnalysisInputs` contains grouped statement inputs and optional
  prior-period, market-equity, and historical-series groups.
- `PortfolioAllocator` exposes `mean_variance`, `risk_based`, and
  `downside_risk` allocation families.
- Pricing classes use names ending in `Model`; scalar parameter containers are
  provided for Black--Scholes--Merton and lattice workflows.

## Cache safety

Financial statement cache files use schema versioning, checksums, and atomic
replacement. Invalid cache files are treated as misses.
