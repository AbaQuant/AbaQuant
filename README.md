# AbaQuant

[![Tests](https://github.com/AbaQuant/AbaQuant/actions/workflows/tests.yml/badge.svg)](https://github.com/AbaQuant/AbaQuant/actions/workflows/tests.yml)
[![Documentation](https://github.com/AbaQuant/AbaQuant/actions/workflows/docs.yml/badge.svg)](https://abaquant.github.io/AbaQuant/)
[![PyPI](https://img.shields.io/pypi/v/abaquant.svg)](https://pypi.org/project/abaquant/)
[![Python](https://img.shields.io/pypi/pyversions/abaquant.svg)](https://pypi.org/project/abaquant/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

AbaQuant is an applied actuarial and quantitative-finance library for Python. Version **1.0.0rc1** stabilizes the public namespace around derivatives, financial mathematics, market data, credit analytics, portfolio construction, risk dashboards, visualization, reports, rate curves, and provenance-aware workflows.

## Installation

```bash
pip install abaquant
```

For a local source checkout:

```bash
python -m pip install -e .
```

Optional extras are grouped by workflow:

```bash
python -m pip install -e .[market]
python -m pip install -e .[visual]
python -m pip install -e .[dev]
python -m pip install -e .[docs]
```

AbaQuant targets Python 3.11 through 3.14; the release workflow validates each
version before publication. Live market-data workflows and visualization
backends are optional; the mathematical core depends only on NumPy, pandas,
and SciPy.

## Minimal examples

### Derivatives

```python
from abaquant.derivatives import BlackScholesMertonModel

model = BlackScholesMertonModel(
    spot_price=100.0,
    strike_price=105.0,
    maturity_years=1.0,
    risk_free_rate=0.04,
    volatility=0.20,
)

price = model.price("call")
greeks = model.greeks("call")
```

### Market data and option-chain analytics

```python
from abaquant.marketdata import get_ticker

ticker = get_ticker("AAPL")
spot = ticker.spot()
# Live data requires an installed provider extra and provider availability.
```

### Portfolio construction

```python
from abaquant.portfolio import PortfolioAllocator

allocator = PortfolioAllocator.from_returns(returns)
weights = allocator.max_sharpe()
report = allocator.report()
```

### Rates

```python
from abaquant.rates import ManualRateProvider, get_rate_curve

curve = get_rate_curve(
    provider=ManualRateProvider({1.0: 0.045, 5.0: 0.047, 10.0: 0.049})
)
discount = curve.discount_factor(5.0)
```

### Provenance

```python
from abaquant.core import DataProvenance

provenance = DataProvenance(
    provider="manual",
    dataset="example",
    request={"symbol": "AAPL"},
)
metadata = provenance.as_dict()
```

## Stable v1 namespace map

| Namespace | Purpose |
|---|---|
| `abaquant.derivatives` | Vanilla, exotic, tree, simulation, strategy, calibration, and advanced option models. |
| `abaquant.financial_math` | Time value of money, rates, annuities, bonds, loans, corporate finance, equity, portfolio math, and VaR helpers. |
| `abaquant.marketdata` | Lazy ticker and universe facades, optional provider adapters, option-chain analytics, and financial statements. |
| `abaquant.credit` | Credit transition matrices, CDS/CDO helpers, Gaussian copula simulation, credit proxy scoring, and credit VaR/CVaR. |
| `abaquant.portfolio` | Allocation engines, downside-risk optimizers, backtesting, rolling metrics, and scenario analysis. |
| `abaquant.rates` | Manual and FRED-backed rate curves, interpolation, discount factors, and interest-rate utilities. |
| `abaquant.visualization` | Matplotlib and Plotly chart helpers with configurable themes. |
| `abaquant.reports` | Markdown, HTML, and lightweight PDF report exports. |
| `abaquant.risk` | Integrated risk dashboard workflows. |
| `abaquant.core` | Shared provenance objects and provenance merging helpers. |

The root `abaquant` namespace re-exports the documented public facades and defines `abaquant.__version__`.

## Live-data warnings

Market-data providers are optional and lazy. Object construction should not make network requests unless a retrieval method explicitly asks for provider data. Provider data can be unavailable, incomplete, stale, adjusted, restated, or subject to provider-specific terms and rate limits.

For SEC EDGAR requests, set a project-specific contact user agent when using live data:

```bash
export ABAQUANT_SEC_USER_AGENT="your-app/1.0 your.email@example.com"
```

For FRED requests, provide a FRED API key through the provider constructor or environment where supported.

## Model assumptions

AbaQuant implements educational and research-grade quantitative routines. Major assumptions include:

- Black-Scholes-Merton assumes lognormal dynamics, constant volatility, frictionless markets, and continuous trading.
- Black-76 uses forward pricing conventions and constant lognormal forward volatility.
- Bachelier uses normal price dynamics and can accommodate negative underlyings or rates.
- Heston, SABR, Merton jump diffusion, NIG, and Variance-Gamma models rely on numerical approximations and calibration quality.
- Portfolio optimizers are sensitive to estimated returns, covariance matrices, constraints, sampling frequency, and transaction-cost assumptions.
- Credit proxy metrics are accounting-derived heuristics, not agency ratings.
- Gaussian copula credit simulation depends materially on default probabilities, recoveries, and correlation assumptions.
- Backtests are historical simulations; they are not forecasts.

## Not investment advice

AbaQuant is not an investment adviser, broker, credit-rating agency, or risk-management system. Outputs are model-derived estimates for research and education, not trading, lending, investment, tax, accounting, or legal advice.

## Development checks

```bash
python -m pip install -e ".[dev,docs,market,visual]"
python -m ruff format --check .
python -m ruff check .
python -m pytest
python scripts/check_documentation.py
python -m sphinx -W --keep-going -b html docs docs/_build/html
python -m build
python -m twine check dist/*
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the complete contributor workflow
and [the hosted documentation](https://abaquant.github.io/AbaQuant/) for API
contracts, model assumptions, and examples.

## Documentation source layout

The Sphinx documentation source is written in native reStructuredText under `docs/` and organized into topic subfolders: `getting-started/`, `reference/`, `domains/`, `operations/`, `development/`, and `api/`. The `api/` tree is generated from the source package by `python scripts/generate_api_docs.py`; it mirrors all 109 Python modules/packages and renders detailed autodoc entries for the public callable surface.
