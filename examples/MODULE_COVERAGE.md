# Example module coverage

The examples are organized as tutorial-style scripts. Each file is built from
small functions: one section builds inputs, one computes results, one creates
visualizations where supported, and `run()` wires the workflow together.

| Example | Main coverage |
|---|---|
| `00_import_all_public_modules.py` | Import smoke test for public modules. |
| `01_derivatives.py` | Vanilla options, Greeks, binomial trees, forwards, strategies, exotics. |
| `02_financial_math.py` | TVM, rates, annuities, bonds, cash flows, corporate finance, portfolio primitives, loans, VaR/CVaR. |
| `03_derivatives_advanced_models.py` | Advanced option models, diagnostics, extrinsic value, Greek curves, surfaces, simulations, analytics, and option-model visualizations. |
| `04_credit_risk.py` | Fundamental credit proxies, transitions, CDS, CDO, copula, VaR/CVaR, and credit visualizations. |
| `05_portfolio_optimization.py` | Mean-variance, risk-based, downside-risk allocators, frontier, backtest, stress tests, and portfolio visualizations. |
| `06_marketdata_offline.py` | Offline ticker, option chain, cached financials, credit bridge, universe, and market-data visualizations. |
| `07_marketdata_live_cached_financials.py` | Optional Yahoo/yfinance cached-statement workflow. Not deterministic. |
| `08_root_facades.py` | Root namespace, credit facade, and rates facade. |
| `09_visualizations.py` | One compact overview of all supported `visualize()` families, including option extrinsic value, Greek curves, and surfaces. |
| `10_visualization_theme.py` | Global visualization theme and temporary theme context manager. |
| `11_visualize_method_gallery.py` | Complete `visualize()` gallery for supported model families, including derivative Greek and surface plots. |
| `12_option_model_visual_report.py` | Saved option-model visual report with diagnostics, extrinsic value, Greek curves, and option surfaces. |
| `13_portfolio_credit_visual_dashboard.py` | Saved portfolio-credit dashboard. |
| `14_scenario_analysis.py` | Derivative spot-volatility scenario grids, portfolio shock analysis, credit multiplier scenarios, and scenario visual reports. |
| `15_sec_xbrl_fundamentals.py` | SEC EDGAR/XBRL Company Facts provider workflow, canonical statements, and credit-proxy bridge. |
| `16_fred_rate_curve.py` | Deterministic and optional live FRED risk-free-rate curve workflow. |
| `17_option_chain_analytics.py` | Listed option-chain analytics: IV smile, IV surface, skew, term structure, rich/cheap, and open-interest heatmaps. |
| `18_option_strategy_builder.py` | Composable option strategy builder, named strategy constructors, payoff diagnostics, break-even points, and payoff/component visualizations. |
| `19_portfolio_backtesting.py` | Deterministic portfolio backtesting with rebalancing policies, benchmark comparison, rolling metrics, return tables, drawdown events, contribution/trade summaries, transaction-cost/slippage modeling, and extended visualizations. |
| `20_risk_dashboard.py` | Integrated risk dashboard combining backtest summary, volatility risk contribution, drawdown, correlation, and credit proxy score visualizations. |
| `21_exportable_reports.py` | Exportable Markdown, HTML, and PDF reports for option models, portfolio allocators, backtests, credit assessments, and risk dashboards. |
| `22_derivative_calibration.py` | BSM flat-vol, SABR smile, and compact Heston calibration with model-versus-market and residual visualizations. |
| `manual_credit_proxy_example.py` | Minimal manual grouped credit inputs. |
| `cached_financials_credit_example.py` | Offline cached statement bridge to credit proxies. |
| `applied_marketdata_ticker_options.py` | Single-ticker applied options workflow. |
| `applied_marketdata_universe_portfolio.py` | Multi-ticker applied universe workflow. |

Generated figures are written under `examples/generated_figures/`. SVG files are
committed, while non-SVG generated artifacts are excluded from version control.


- `16_fred_rate_curve.py` — Builds a deterministic risk-free-rate curve, shows `zero_rate()` and `discount_factor()`, uses the one-year curve rate inside a Black--Scholes--Merton example, and documents the optional live FRED branch with disk caching.

| Data provenance | `23_data_provenance.py` | Shows `.provenance` metadata for derived, manual, cached, and report objects. |
