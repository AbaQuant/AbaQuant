# Examples

The examples are executable tutorial modules grouped by the same analytical
domains as `examples_notebooks/`. Each module builds inputs, computes results,
creates visualizations where appropriate, and exposes a `run()` function.

```text
examples/
|-- foundations/
|-- financial_math_and_rates/
|-- derivatives/
|-- credit/
|-- portfolio_and_risk/
|-- market_data/
|-- visualization_and_reports/
|-- _shared/
|-- run_all_deterministic_examples.py
`-- run_all_visual_examples.py
```

No deterministic example requires Yahoo, yfinance, or network access.

## Install AbaQuant

The examples consume the published package through its public facade:

```python
import abaquant as aq
```

Install AbaQuant and the optional dependencies used by the complete suite:

```bash
python -m pip install "abaquant[market,visual]"
```

## Run the suites

Run commands from the repository root so Python can resolve the local
`examples` package:

```bash
python -m examples.run_all_deterministic_examples
python -m examples.run_all_visual_examples
```

## Run by domain

Individual examples use the same module-style command:

```bash
python -m examples.foundations.08_root_facades
python -m examples.financial_math_and_rates.02_financial_math
python -m examples.derivatives.01_derivatives
python -m examples.credit.04_credit_risk
python -m examples.portfolio_and_risk.05_portfolio_optimization
python -m examples.market_data.06_marketdata_offline
python -m examples.visualization_and_reports.09_visualizations
```

The optional live Yahoo/yfinance workflow may make network requests:

```bash
python -m examples.market_data.07_marketdata_live_cached_financials
```

## Generated artifacts

Examples save figures instead of calling `show()` automatically. Matplotlib
figures are committed as SVG files; dense surfaces and heatmaps are rasterized
inside the SVG so labels and axes remain vector sharp without oversized files.

```text
examples/generated_figures/
examples/generated_reports/
```

Most visualization examples use Matplotlib. The visualization-theme module
also demonstrates temporary Plotly themes and HTML export. Plotly HTML and
generated reports remain ignored.

## Import policy

The examples do not modify `sys.path` or import the library from `src`.
`abaquant` must be installed from PyPI or as an editable development package.
Only deterministic fixtures and presentation helpers are imported from
`examples._shared`.

All data are synthetic unless an example explicitly says it is live. These
examples are educational demonstrations, not investment, trading, or credit
rating advice.
