# Descriptive naming refactor report

## Scope

This refactor improves naming in the high-impact public object model and in
core option-pricing, simulation, comparison, market-data, and portfolio
workflows. Numerical algorithms and public output schemas were preserved.

## Canonical API additions

- Model engines now use descriptive canonical names, including
  `BlackScholesMertonModel`, `CoxRossRubinsteinModel`,
  `HestonStochasticVolatilityModel`, and `MertonJumpDiffusionModel`.
- Applied market-data objects now use `MarketTicker`, `MarketUniverse`,
  `TickerHistory`, `TickerOptionAnalytics`, `UniverseHistory`,
  `UniverseStatistics`, and `UniversePortfolioAnalytics`.
- The static allocation class is now `PortfolioAllocator`.

## Internal naming improvements

Representative replacements include:

- `S`, `K`, `T`, `r`, `q`, and `sigma` state replaced with `spot_price`,
  `strike_price`, `maturity_years`, `risk_free_rate`, `dividend_yield`, and
  `volatility`.
- Binomial-tree internals now use names such as `up_factor`,
  `risk_neutral_up_probability`, `terminal_underlying_prices`, and
  `option_value_tree`.
- Monte Carlo internals now use `standard_normal_draws`,
  `terminal_underlying_prices`, `discounted_option_payoffs`, and
  `estimated_standard_error`.
- Portfolio workflows now use `annualized_expected_returns`,
  `annualized_covariance_matrix`, `optimized_weight_vector`, and
  `return_observation_count`.

## Compatibility

Legacy class names, legacy model constructors, and legacy symbolic model
attributes are preserved through aliases and wrappers. See
`docs/NAMING_MIGRATION.md` for the full map.

## Intentional boundary

Short names in stable formula-oriented public functions are retained where
those symbols are conventional and widely used in quantitative finance. Their
implementations convert them into descriptive local names immediately after
argument validation.
