Rates
=====

The ``abaquant.rates`` namespace provides provider-neutral rate curves,
manual curves, optional FRED-backed curves, interpolation, discount
factors, and interest-rate helper re-exports.

Manual curves
-------------

.. code:: python

   from abaquant.rates import ManualRateProvider, get_rate_curve

   provider = ManualRateProvider({
       1.0 / 12.0: 0.043,
       1.0: 0.045,
       5.0: 0.047,
       10.0: 0.049,
   })
   curve = get_rate_curve(provider=provider)

Query rates and discount factors
--------------------------------

.. code:: python

   one_year_rate = curve.zero_rate(1.0)
   five_year_rate = curve.zero_rate(5.0)
   five_year_df = curve.discount_factor(5.0)

Continuous discounting:

.. math::


   D(T)=e^{-r(T)T}.

Annual compounding:

.. math::


   D(T)=(1+r(T))^{-T}.

Simple discounting:

.. math::


   D(T)=\frac{1}{1+r(T)T}.

Interpolation and extrapolation
-------------------------------

Rate curves sort observations by maturity and linearly interpolate by
default. Extrapolation can be flat or can raise an error depending on
the request.

.. code:: python

   rate = curve.zero_rate(3.0, interpolation="linear", extrapolation="flat")

FRED-backed curves
------------------

FRED Treasury constant-maturity series are reported as annual percentage
yields. AbaQuant converts values into annual decimal rates.

.. code:: python

   from abaquant.rates import FredRateProvider, get_rate_curve

   provider = FredRateProvider(api_key="...")
   curve = get_rate_curve(provider=provider, curve_date="latest")

FRED-backed workflows can use memory or disk caching depending on
provider configuration.

Provenance
----------

Rate curves carry provenance with provider name, dataset, requested
curve date, source labels, transformation steps, and cache status when
applicable.

.. code:: python

   metadata = curve.provenance.as_dict()

Limitations
-----------

Treasury constant-maturity rates are pragmatic yield proxies. They are
not fully bootstrapped collateralized zero-coupon curves. They do not
model OIS discounting, issuer curves, liquidity premiums, cross-currency
basis, funding valuation adjustments, or intraday curve dynamics.
