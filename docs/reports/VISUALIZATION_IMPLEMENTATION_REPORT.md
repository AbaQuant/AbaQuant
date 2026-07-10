# Visualization Implementation Report

## Added design

The visualization API is optional and backend-neutral. Analytical façade objects return figures without invoking `show()`. Matplotlib and Plotly are imported lazily, so core imports and nonvisual calculations retain no visualization dependency.

## Public entry points

- Option-pricing model objects: `visualize(option_type=..., chart=..., backend=...)`.
- `PortfolioAllocator.visualize(weights=..., chart=..., backend=...)`.
- `CreditProxyAssessment.visualize(chart=..., backend=...)`.
- `MarketTicker.visualize(...)` and `MarketUniverse.visualize(...)`.
- `FinancialStatements.visualize(...)` and `FinancialStatementSnapshot.visualize(...)`.

## Chart families

- Options: payoff, price profile, implied-volatility smile, and CRR tree nodes.
- Portfolio: weights, cumulative return, and correlation heatmap.
- Credit: available metrics and synthetic proxy score.
- Market data: price history and latest statement-column bars.

## Scope boundary

Exceptions, provider protocols, scalar input dataclasses, cache stores, and other structural objects do not expose arbitrary charts. They have no natural numerical visual semantics.
