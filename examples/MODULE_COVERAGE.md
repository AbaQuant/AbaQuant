# Example Module Coverage

The Python examples mirror the domain structure under `examples_notebooks/`.

## Foundations

| Example | Main coverage |
|---|---|
| `foundations/00_import_all_public_modules.py` | Import smoke test for public modules. |
| `foundations/08_root_facades.py` | Root namespace and facade imports. |
| `foundations/23_data_provenance.py` | Provenance across rates, derivatives, portfolios, credit, dashboards, and reports. |

## Financial Math and Rates

| Example | Main coverage |
|---|---|
| `financial_math_and_rates/02_financial_math.py` | TVM, rates, annuities, bonds, cash flows, corporate finance, loans, and risk. |
| `financial_math_and_rates/16_fred_rate_curve.py` | Deterministic and optional live FRED rate curves. |

## Derivatives

| Example | Main coverage |
|---|---|
| `derivatives/01_derivatives.py` | Vanilla options, Greeks, trees, forwards, strategies, and exotics. |
| `derivatives/03_derivatives_advanced_models.py` | Advanced models, diagnostics, simulations, and surfaces. |
| `derivatives/12_option_model_visual_report.py` | Option-model diagnostics and visual reports. |
| `derivatives/17_option_chain_analytics.py` | IV smiles, surfaces, skew, term structure, and open interest. |
| `derivatives/18_option_strategy_builder.py` | Composable option strategies and payoff diagnostics. |
| `derivatives/22_derivative_calibration.py` | BSM, SABR, and Heston calibration diagnostics. |

## Credit

| Example | Main coverage |
|---|---|
| `credit/04_credit_risk.py` | Credit proxies, transitions, CDS, CDO, copula, and credit VaR. |
| `credit/manual_credit_proxy_example.py` | Minimal manual grouped credit inputs. |
| `credit/cached_financials_credit_example.py` | Cached statement bridge to credit proxies. |

## Portfolio and Risk

| Example | Main coverage |
|---|---|
| `portfolio_and_risk/05_portfolio_optimization.py` | Allocation, frontier, downside risk, backtests, and stress tests. |
| `portfolio_and_risk/13_portfolio_credit_visual_dashboard.py` | Portfolio-credit visual dashboard. |
| `portfolio_and_risk/14_scenario_analysis.py` | Derivative, portfolio, and credit scenarios. |
| `portfolio_and_risk/19_portfolio_backtesting.py` | Rebalancing, benchmarks, costs, drawdowns, and contributions. |
| `portfolio_and_risk/20_risk_dashboard.py` | Integrated portfolio and credit risk dashboard. |

## Market Data

| Example | Main coverage |
|---|---|
| `market_data/06_marketdata_offline.py` | Offline ticker, options, financials, and universe workflows. |
| `market_data/07_marketdata_live_cached_financials.py` | Optional live Yahoo cached-financial workflow. |
| `market_data/15_sec_xbrl_fundamentals.py` | SEC Company Facts, statements, and credit inputs. |
| `market_data/applied_marketdata_ticker_options.py` | Applied single-ticker option workflow. |
| `market_data/applied_marketdata_universe_portfolio.py` | Applied multi-ticker portfolio workflow. |

## Visualization and Reports

| Example | Main coverage |
|---|---|
| `visualization_and_reports/09_visualizations.py` | Visualization-family overview. |
| `visualization_and_reports/10_visualization_theme.py` | Matplotlib and Plotly theme configuration. |
| `visualization_and_reports/11_visualize_method_gallery.py` | Complete public `visualize()` gallery. |
| `visualization_and_reports/21_exportable_reports.py` | Markdown, HTML, and PDF report export. |

Generated figures are written under `examples/generated_figures/`. SVG files
are committed, while non-SVG generated artifacts are excluded from version
control.
