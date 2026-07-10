# Phase 3 implementation report: manual fundamental credit proxies

## Architecture

Phase 3 adds a pure, provider-independent layer in
`creditrisk/fundamentals.py`. The user creates a `FundamentalCreditInputs`
instance from manual financial-statement and market-value values. The pure
function `calculate_credit_proxy_metrics(...)` produces a
`CreditProxyAssessment`. `MarketTicker.credit` exposes a convenience façade but
makes no Yahoo or provider request for any Phase 3 calculation.

## Public API

```python
from abaquant.credit import (
    FundamentalCreditInputs,
    calculate_credit_proxy_metrics,
)
from abaquant.marketdata import get_ticker

inputs = FundamentalCreditInputs(...)
assessment = calculate_credit_proxy_metrics(inputs)
issuer = get_ticker("NVDA")
assessment = issuer.credit.assess(inputs)
metrics = issuer.credit.proxy_metrics(inputs)
```

## Metrics

- debt-to-equity;
- current and quick ratios;
- interest coverage;
- net debt and net debt / EBITDA;
- operating cash flow / total debt;
- traditional five-factor public-company Altman Z-score and component ratios;
- complete Piotroski F-score and nine binary signals only when all inputs exist;
- sample earnings standard deviation and coefficient of variation;
- leverage first-to-last relative trend;
- transparent coverage-normalized 0--100 synthetic credit-proxy score and band.

## Important boundaries

The score is not an agency rating, a probability of default, a CDS spread, a
regulatory model, or investment advice. No external statement, credit-rating,
CDS, SEC/XBRL, FRED, Treasury, or paid-data provider is used in Phase 3.
Missing values are not imputed.
