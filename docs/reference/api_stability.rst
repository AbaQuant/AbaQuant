API stability
=============

AbaQuant uses semantic versioning for its supported public facades. Version
1.x compatibility applies to names exported by ``__all__`` from the following
modules:

* ``abaquant``
* ``abaquant.core``
* ``abaquant.credit``
* ``abaquant.derivatives``
* ``abaquant.financial_math``
* ``abaquant.marketdata``
* ``abaquant.portfolio``
* ``abaquant.rates``
* ``abaquant.reports``
* ``abaquant.risk``
* ``abaquant.visualization``

For these facades, incompatible removals, import moves, signature changes, or
meaningful default changes require a major release. Deprecations should remain
available for at least one minor release when practical.

Provisional implementation modules
----------------------------------

The complete API reference documents lower-level implementation modules so
users can inspect behavior and type contracts. A documented implementation
detail is not automatically a stable import path. Names outside the facade
``__all__`` lists, private names beginning with an underscore, provider cache
formats, and numerical helper modules may change in a minor release.

Numerical compatibility
-----------------------

Floating-point results may vary slightly across supported NumPy, pandas,
SciPy, operating-system, and BLAS combinations. AbaQuant treats documented
formulas, units, conventions, and tolerances as the compatibility contract;
bit-for-bit equality across platforms is not guaranteed.

Provider and visualization behavior
-----------------------------------

External providers may change fields, availability, or rate limits outside
AbaQuant's release cycle. Chart aesthetics and backend-native figure types may
evolve in minor releases, while the documented data returned by analytical
methods remains the primary contract.
