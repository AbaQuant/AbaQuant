Quickstart
==========

This page shows the shortest stable v1 workflows. All examples use
decimal annual rates and volatilities unless stated otherwise.

Price a European option
-----------------------

.. code:: python

   from abaquant.derivatives import black_scholes, calculate_greeks

   call = black_scholes(
       S=100.0,
       K=105.0,
       r=0.04,
       sigma=0.22,
       T=1.0,
       is_call=True,
   )
   greeks = calculate_greeks(100.0, 105.0, 0.04, 0.22, 1.0, is_call=True)

   print(call)
   print(greeks["delta"])

Use an object-oriented option model
-----------------------------------

.. code:: python

   from abaquant.derivatives import BlackScholesMertonModel

   model = BlackScholesMertonModel(
       spot_price=100.0,
       strike_price=105.0,
       maturity_years=1.0,
       risk_free_rate=0.04,
       volatility=0.22,
       dividend_yield=0.01,
   )

   price = model.price("call")
   greeks = model.greeks()
   report = model.report(option_type="call")

Build an option strategy
------------------------

.. code:: python

   from abaquant.derivatives import OptionStrategy

   strategy = OptionStrategy.bull_call_spread(
       lower_strike=100.0,
       upper_strike=115.0,
       lower_premium=6.0,
       upper_premium=2.0,
   )

   profile = strategy.profile(points=25)
   max_profit = strategy.max_profit()
   max_loss = strategy.max_loss()
   break_evens = strategy.break_even_points()

Discount with a manual rate curve
---------------------------------

.. code:: python

   from abaquant.rates import ManualRateProvider, get_rate_curve

   provider = ManualRateProvider({1.0: 0.045, 5.0: 0.047, 10.0: 0.049})
   curve = get_rate_curve(provider=provider)

   rate_5y = curve.zero_rate(5.0)
   df_5y = curve.discount_factor(5.0)

Run financial-math calculations
-------------------------------

.. code:: python

   from abaquant.financial_math import future_value, present_value, bond_price

   fv = future_value(1000.0, rate=0.05, periods=5)
   pv = present_value(1276.28, rate=0.05, periods=5)
   price, coupon_pv, redemption_pv, total_coupon = bond_price(
       face_value=1000.0,
       coupon_rate_per_period=0.05,
       redemption_value=1000.0,
       yield_per_period=0.045,
       periods=10,
   )

Build a portfolio allocator
---------------------------

.. code:: python

   import pandas as pd
   from abaquant.portfolio import PortfolioAllocator

   returns = pd.DataFrame(
       {
           "ALPHA": [0.01, -0.002, 0.006, 0.004],
           "BETA": [0.003, 0.005, -0.001, 0.002],
           "GAMMA": [-0.002, 0.007, 0.004, 0.006],
       }
   )

   allocator = PortfolioAllocator(returns, annual_risk_free_rate=0.02)
   max_sharpe = allocator.mean_variance.maximum_sharpe()
   risk_parity = allocator.risk_based.risk_parity()
   minimum_cvar = allocator.downside_risk.minimum_cvar(alpha=0.05)

Backtest a portfolio policy
---------------------------

.. code:: python

   backtest = allocator.backtest(
       weights="inverse_volatility",
       rebalance="monthly",
       transaction_cost_bps=5.0,
       slippage_bps=1.0,
       benchmark="equal_weight",
       lookback=10,
   )

   summary = backtest.summary()
   report = backtest.report()

Score fundamentals-based credit risk
------------------------------------

.. code:: python

   from abaquant.credit import (
       BalanceSheetInputs,
       IncomeStatementInputs,
       CashFlowInputs,
       CreditAnalysisInputs,
       calculate_credit_proxy_metrics,
   )

   inputs = CreditAnalysisInputs(
       balance_sheet=BalanceSheetInputs(
           total_debt=420.0,
           total_equity=700.0,
           current_assets=310.0,
           inventory=40.0,
           current_liabilities=180.0,
           cash_and_cash_equivalents=85.0,
           total_assets=1400.0,
           total_liabilities=620.0,
           retained_earnings=210.0,
           long_term_debt=350.0,
       ),
       income_statement=IncomeStatementInputs(
           revenue=950.0,
           gross_profit=390.0,
           ebit=120.0,
           ebitda=160.0,
           interest_expense=22.0,
           net_income=75.0,
       ),
       cash_flow_statement=CashFlowInputs(operating_cash_flow=115.0),
       reporting_currency="USD",
       reporting_period="FY2025",
   )

   assessment = calculate_credit_proxy_metrics(inputs)
   score = assessment.synthetic_credit_proxy_score
   band = assessment.synthetic_credit_proxy_band

Work with lazy market-data facades
----------------------------------

.. code:: python

   from abaquant.marketdata import get_ticker, get_tickers

   ticker = get_ticker("AAPL")
   # A retrieval method such as ticker.spot() may use the configured provider.

   universe = get_tickers(["AAPL", "MSFT", "NVDA"])

Export reports
--------------

.. code:: python

   from pathlib import Path

   output = Path("reports")
   written = model.report(option_type="call").save(
       output,
       "option_report",
       formats=("markdown", "html", "pdf"),
   )

Inspect provenance
------------------

.. code:: python

   from abaquant.core import DataProvenance

   provenance = DataProvenance(
       provider="manual",
       dataset="example_inputs",
       request={"symbols": ["ALPHA", "BETA"]},
       transformation_steps=("manual construction", "normalization"),
   )

   metadata = provenance.as_dict()
