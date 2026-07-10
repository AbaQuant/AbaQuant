abaquant.derivatives.strategies
===============================

**Import path:** ``abaquant.derivatives.strategies``

**Domain:** Derivative pricing, simulation, calibration, diagnostics, and strategy analysis.

Purpose
-------

Composable option-strategy objects and expiration payoff profiles.

When to use it
--------------

Use this package when valuing contingent claims, calculating Greeks, building option strategies, simulating stochastic processes, or fitting models to market observations.

Public objects
--------------

* **function:** ``option_payoff_leg`` — Evaluate one legacy option leg's net expiration profit.
* **class:** ``OptionStrategyLeg`` — One line item in a static option strategy.
  * ``OptionStrategyLeg.option`` — Create one call or put leg.
  * ``OptionStrategyLeg.underlying`` — Create one underlying asset leg.
  * ``OptionStrategyLeg.display_label`` — Return the label used in strategy profiles and charts.
  * ``OptionStrategyLeg.gross_payoff`` — Evaluate the terminal payoff before inception cash flows.
  * ``OptionStrategyLeg.net_inception_cost`` — Return the initial net cash cost of the leg.
  * ``OptionStrategyLeg.profit`` — Evaluate terminal net profit after inception cash flows.
  * ``OptionStrategyLeg.terminal_slope`` — Return the profit slope as the terminal price tends to infinity.
* **class:** ``OptionStrategy`` — Composable static option strategy with payoff and risk diagnostics.
  * ``OptionStrategy.legs`` — Return the strategy legs as an immutable tuple.
  * ``OptionStrategy.add_leg`` — Append a validated leg and return ''self'' for chaining.
  * ``OptionStrategy.buy_call`` — Add a long call leg and return the strategy.
  * ``OptionStrategy.sell_call`` — Add a short call leg and return the strategy.
  * ``OptionStrategy.buy_put`` — Add a long put leg and return the strategy.
  * ``OptionStrategy.sell_put`` — Add a short put leg and return the strategy.
  * ``OptionStrategy.buy_underlying`` — Add a long underlying leg and return the strategy.
  * ``OptionStrategy.sell_underlying`` — Add a short underlying leg and return the strategy.
  * ``OptionStrategy.bull_call_spread`` — Create a long bull call spread.
  * ``OptionStrategy.protective_put`` — Create a protective put from a long underlying and long put.
  * ``OptionStrategy.straddle`` — Create a long straddle using one call and one put at one strike.
  * ``OptionStrategy.strangle`` — Create a long strangle using an out-of-the-money put and call.
  * ``OptionStrategy.iron_condor`` — Create a long-wing iron condor with four option legs.
  * ``OptionStrategy.butterfly`` — Create a symmetric or asymmetric long butterfly.
  * ``OptionStrategy.net_inception_cost`` — Return total net cash paid at inception.
  * ``OptionStrategy.gross_payoff`` — Evaluate strategy payoff before premiums and entry costs.
  * ``OptionStrategy.profit`` — Evaluate terminal net profit after inception cash flows.
  * ``OptionStrategy.payoff`` — Evaluate the strategy expiration payoff or profit.
  * ``OptionStrategy.profile`` — Return a payoff table over terminal underlying prices.
  * ``OptionStrategy.max_profit`` — Return maximum expiration profit, or ''np.inf'' if unbounded above.
  * ``OptionStrategy.max_loss`` — Return minimum expiration profit, or ''-np.inf'' if unbounded below.
  * ``OptionStrategy.break_even_points`` — Return terminal prices where net profit is approximately zero.
  * ``OptionStrategy.as_dict`` — Return a plain-Python summary of the strategy and diagnostics.
  * ``OptionStrategy.visualize`` — Visualize the strategy payoff or component profile.
* **function:** ``strategy_profile`` — Evaluate a legacy dictionary-based static strategy profile.

Detailed reference
------------------

.. automodule:: abaquant.derivatives.strategies
   :members:
   :show-inheritance:
   :member-order: bysource
