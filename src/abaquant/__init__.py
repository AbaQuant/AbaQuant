"""Stable public AbaQuant API.

AbaQuant is an applied quantitative-finance research library that combines
financial mathematics, derivatives, market data, credit analytics, rates,
portfolio construction, backtesting, reports, dashboards, and provenance-aware
workflows under stable v1 namespaces.
"""

from .core import DataProvenance as DataProvenance
from .core import ProvenanceMixin as ProvenanceMixin
from .credit import *  # noqa: F403
from .credit import __all__ as _credit_all
from .derivatives import *  # noqa: F403
from .derivatives import __all__ as _derivatives_all
from .financial_math import *  # noqa: F403
from .financial_math import __all__ as _financial_math_all
from .marketdata import *  # noqa: F403
from .marketdata import __all__ as _marketdata_all
from .portfolio import *  # noqa: F403
from .portfolio import __all__ as _portfolio_all
from .rates import *  # noqa: F403
from .rates import __all__ as _rates_all
from .reports import *  # noqa: F403
from .reports import __all__ as _reports_all
from .risk import *  # noqa: F403
from .risk import __all__ as _risk_all
from .visualization import *  # noqa: F403
from .visualization import __all__ as _visualization_all

__version__ = "1.0.0rc1"

__all__ = sorted(
    set(_credit_all)
    | set(_derivatives_all)
    | set(_financial_math_all)
    | set(_marketdata_all)
    | set(_portfolio_all)
    | set(_rates_all)
    | set(_reports_all)
    | set(_risk_all)
    | set(_visualization_all)
    | {
        "DataProvenance",
        "ProvenanceMixin",
        "__version__",
    }
)
