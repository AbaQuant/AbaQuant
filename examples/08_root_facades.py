"""Examples for root-level convenience facades."""

from __future__ import annotations

import abaquant as aq
from _shared.output import print_mapping


def demonstrate_root_facade() -> dict[str, float]:
    """Use the root namespace for common pricing and portfolio utilities."""
    return {
        "black_scholes_call": aq.black_scholes(100.0, 100.0, 0.05, 0.20, 1.0),
        "forward_price": aq.forward_price(100.0, 0.05, 1.0),
        "portfolio_sharpe": aq.portfolio_sharpe(0.10, 0.18, 0.03),
    }


def demonstrate_credit_and_rates_facades() -> dict[str, object]:
    """Use dedicated credit and rates facade modules."""
    cds = aq.value_cds(0.03, 0.04, 5, 0.40)
    return {
        "future_value": aq.future_value(1_000.0, 0.05, 5),
        "present_value": aq.present_value(1_500.0, 0.05, 5),
        "effective_rate": aq.nominal_to_effective_rate(0.06, 12),
        "transition_shape": aq.build_transition_matrix().shape,
        "cds_fair_spread": cds["spread"],
    }


def run() -> None:
    """Run root-facade demonstrations."""
    print_mapping("Root abaquant namespace", demonstrate_root_facade())
    print_mapping("Credit and rates facades", demonstrate_credit_and_rates_facades())


if __name__ == "__main__":
    run()
