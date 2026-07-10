API reference guide
===================

AbaQuant has two complementary documentation layers.

* The :doc:`../domains/index` pages explain financial meaning, model choice,
  assumptions, and workflow design.
* The :doc:`../api/index` pages document the callable surface module by module,
  including signatures, parameters, return values, exceptions, methods,
  properties, inheritance, and source-derived notes.

Choosing an import path
-----------------------

Use domain facades for ordinary application code::

   from abaquant.derivatives import black_scholes, OptionStrategy
   from abaquant.financial_math import present_value, bond_price
   from abaquant.portfolio import PortfolioAllocator

Use implementation modules when you need a narrowly scoped dependency or want
to inspect the canonical definition::

   from abaquant.derivatives.vanilla import black_scholes
   from abaquant.portfolio.optimization import PortfolioAllocator

The root ``abaquant`` facade is convenient for exploration, but explicit domain
imports are easier to audit and less likely to create accidental coupling.

How to read function documentation
----------------------------------

For each callable, verify these items before use:

#. **Units:** decimal rates versus percentages, years versus periods, currency
   values versus normalized returns.
#. **Compounding:** simple, periodic, or continuous conventions.
#. **Sign convention:** cash inflow/outflow and long/short position semantics.
#. **Shape:** scalar, one-dimensional array, table, or path matrix.
#. **Annualization:** observations per year and whether input returns are already
   annualized.
#. **Failure behavior:** validation errors, infeasible optimization, missing data,
   optional dependencies, and numerical non-convergence.

API stability
-------------

The documented domain namespaces are the supported v1 import surface. Internal
helpers whose names begin with an underscore are excluded from the generated
public inventory and may change without a compatibility guarantee.

.. seealso::

   Open the :doc:`../api/index` for the complete generated reference.
