# V1 Module Restructure Report

## Purpose

This pass reorganized AbaQuant around cleaner v1-style public namespaces before a stable release. The goal was to remove pre-v1 module names from the public source tree and make imports align with the library's current scope.

## Main source changes

- Moved `abaquant.advanced_derivatives` into `abaquant.derivatives`.
- Added `abaquant.derivatives.advanced` as a convenience namespace for advanced model aliases such as `HestonModel` and `SABRModel`.
- Moved advanced model classes into `abaquant.derivatives.models`.
- Moved calibration classes into `abaquant.derivatives.calibration`.
- Renamed `abaquant.portfolioopt` to `abaquant.portfolio`.
- Renamed `abaquant.creditrisk` to `abaquant.credit`.
- Moved provenance infrastructure into `abaquant.core`.
- Moved exportable report infrastructure into `abaquant.reports`.
- Moved the integrated dashboard into `abaquant.risk`.
- Converted `abaquant.rates` from a single module into a package while preserving the public `from abaquant.rates import get_rate_curve` import style.
- Removed the old derivative `engine.py` compatibility facade.

## Public v1 import examples

```python
from abaquant.core import DataProvenance
from abaquant.credit import CreditAnalysisInputs
from abaquant.derivatives import BlackScholesMertonModel, OptionStrategy
from abaquant.derivatives.advanced import HestonModel, SABRModel
from abaquant.derivatives.calibration import HestonCalibration
from abaquant.marketdata import get_ticker
from abaquant.portfolio import PortfolioAllocator
from abaquant.rates import get_rate_curve
from abaquant.reports import ExportableReport
from abaquant.risk import RiskDashboard
```

## Test and example updates

- Updated all source, test, and example imports to the new namespaces.
- Added `tests/test_v1_module_structure.py` to verify the new public imports and confirm removed pre-v1 module paths are no longer importable.
- Updated public module import coverage in `examples/00_import_all_public_modules.py`.
- Renamed the advanced-derivatives example to `examples/03_derivatives_advanced_models.py` to avoid old package-name wording.

## Validation

- `python -m compileall -q src examples tests scripts` passed.
- `PYTHONPATH=src python scripts/check_documentation.py` passed.
- `PYTHONPATH=src python -m pytest -q tests` passed.
- `PYTHONPATH=src python examples/00_import_all_public_modules.py` passed.
- `PYTHONPATH=src python examples/run_all_deterministic_examples.py` passed.
- `PYTHONPATH=src python examples/run_all_visual_examples.py` passed.
