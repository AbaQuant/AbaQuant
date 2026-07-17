# Examples

The examples are written as small tutorial modules rather than long one-block
scripts. Each file follows the same pattern:

1. build deterministic inputs;
2. compute one family of results;
3. create visualizations when the domain exposes `visualize()`;
4. print a compact summary from `run()`.

No deterministic example requires Yahoo, yfinance, or network access.

## Run everything deterministic

```bash
python examples/run_all_deterministic_examples.py
python examples/run_all_visual_examples.py
```

## Run by topic

```bash
python examples/01_derivatives.py
python examples/02_financial_math.py
python examples/03_derivatives_advanced_models.py
python examples/04_credit_risk.py
python examples/05_portfolio_optimization.py
python examples/06_marketdata_offline.py
python examples/09_visualizations.py
python examples/10_visualization_theme.py
python examples/11_visualize_method_gallery.py
python examples/12_option_model_visual_report.py
python examples/13_portfolio_credit_visual_dashboard.py
python examples/14_scenario_analysis.py
python examples/15_sec_xbrl_fundamentals.py
python examples/16_fred_rate_curve.py
python examples/17_option_chain_analytics.py
python examples/18_option_strategy_builder.py
python examples/19_portfolio_backtesting.py
python examples/20_risk_dashboard.py
python examples/21_exportable_reports.py
python examples/22_derivative_calibration.py
```

## Optional live Yahoo/yfinance example

```bash
python examples/07_marketdata_live_cached_financials.py
```

This example may make a network request and requires the optional market-data
provider dependency.

## SEC EDGAR/XBRL fundamentals example

```bash
python examples/15_sec_xbrl_fundamentals.py
python examples/16_fred_rate_curve.py
python examples/17_option_chain_analytics.py
python examples/18_option_strategy_builder.py
python examples/19_portfolio_backtesting.py
python examples/20_risk_dashboard.py
python examples/21_exportable_reports.py
python examples/22_derivative_calibration.py
```

The SEC example is deterministic and offline. It uses a fixture shaped like the
official SEC Company Facts JSON to demonstrate the full provider path from
Company Facts to canonical statement tables and credit proxy inputs. It also
shows disk-cache reuse for both raw SEC Company Facts and normalized financial
statement snapshots. For live SEC access, construct a ticker with
`fundamentals_provider="sec"`, set a clear User-Agent through `sec_user_agent`
or `ABAQUANT_SEC_USER_AGENT`, and use `financial_cache="disk"` with an explicit
`cache_directory` when you want repeated Python sessions to reuse cached SEC
fundamentals.

## Visualization examples

The examples save figures instead of calling `show()` automatically. This makes
them suitable for scripts, notebooks, and CI-style smoke tests.

Generated files are saved under:

```text
examples/generated_figures/
```

Most visualization examples use Matplotlib by default. Run all visual examples with `python examples/run_all_visual_examples.py`. `10_visualization_theme.py`
also demonstrates temporary Plotly themes and HTML export. The option visual
examples include intrinsic/extrinsic decomposition, standardized Greek curves,
price, delta, gamma, vega, and extrinsic-value surfaces, option-chain IV smile/surface/term-structure/rich-cheap/open-interest charts, plus derivative,
portfolio, credit scenario-analysis visual reports, and integrated risk-dashboard charts, and derivative calibration model-versus-market/residual diagnostics.

## Local source snapshots

The helper `examples/_shared/package_bootstrap.py` lets examples run either from
an installed package or from a flat unpacked source snapshot.

## Scope warning

All data are synthetic unless an example explicitly says it is live. The examples
are educational demonstrations of APIs, not investment, trading, or credit-rating
advice.

## Documentation companions

Release documentation is available under `docs/`. The examples remain the
canonical executable tutorial layer; documentation pages summarize public
namespaces, assumptions, and release notes.

- `16_fred_rate_curve.py` — Builds a deterministic risk-free-rate curve, shows `zero_rate()` and `discount_factor()`, uses the one-year curve rate inside a Black--Scholes--Merton example, and documents the optional live FRED branch with disk caching.


- `17_option_chain_analytics.py` — Demonstrates IV smiles, IV surfaces, skew, term structure, rich/cheap tables, and open-interest heatmaps from a deterministic listed option chain.

- `18_option_strategy_builder.py` — Builds composable option strategies, prints payoff diagnostics, and saves strategy payoff/component visualizations.

- `19_portfolio_backtesting.py` - Demonstrates deterministic portfolio backtesting with equal-weight, buy-and-hold, and inverse-volatility policies; benchmark comparison; rolling metrics; calendar return tables; drawdown events; contribution and trade summaries; transaction-cost and slippage modeling; and extended backtest visualizations.


- `20_risk_dashboard.py` - Builds an integrated dashboard that combines portfolio backtesting, volatility risk contributions, drawdowns, asset correlation, and synthetic credit proxy scores.

- `21_exportable_reports.py` - Exports option, portfolio, backtest, credit, and risk-dashboard reports as Markdown, HTML, and PDF files.


- `22_derivative_calibration.py` - Calibrates BSM flat volatility, SABR smile parameters, and a compact Heston fit to deterministic option-chain observations, then saves calibration diagnostic charts.

- `23_data_provenance.py` demonstrates the provider-neutral `.provenance` metadata layer across derivatives, rates, portfolios, credit, dashboards, and reports.
