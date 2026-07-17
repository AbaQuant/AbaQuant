"""Examples for root-level convenience facades."""

from __future__ import annotations

from _shared.output import print_mapping
from _shared.package_bootstrap import ensure_package_importable

ensure_package_importable()

from abaquant import black_scholes, forward_price, portfolio_sharpe
from abaquant.credit import build_transition_matrix, value_cds
from abaquant.rates import future_value, nominal_to_effective_rate, present_value


def demonstrate_root_facade() -> dict[str, float]:
    """Use the root namespace for common pricing and portfolio utilities."""
    return {
        "black_scholes_call": black_scholes(100.0, 100.0, 0.05, 0.20, 1.0),
        "forward_price": forward_price(100.0, 0.05, 1.0),
        "portfolio_sharpe": portfolio_sharpe(0.10, 0.18, 0.03),
    }


def demonstrate_credit_and_rates_facades() -> dict[str, object]:
    """Use dedicated credit and rates facade modules."""
    cds = value_cds(0.03, 0.04, 5, 0.40)
    return {
        "future_value": future_value(1_000.0, 0.05, 5),
        "present_value": present_value(1_500.0, 0.05, 5),
        "effective_rate": nominal_to_effective_rate(0.06, 12),
        "transition_shape": build_transition_matrix().shape,
        "cds_fair_spread": cds["spread"],
    }


def run() -> None:
    """Run root-facade demonstrations."""
    print_mapping("Root abaquant namespace", demonstrate_root_facade())
    print_mapping("Credit and rates facades", demonstrate_credit_and_rates_facades())


if __name__ == "__main__":
    run()
