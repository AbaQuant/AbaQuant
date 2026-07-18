# AbaQuant Example Notebooks

These are the canonical notebook sources rendered in the AbaQuant Sphinx
documentation. They are grouped by analytical domain so the source tree and
the documentation sidebar share the same structure.

```text
examples_notebooks/
|-- foundations/
|-- financial_math_and_rates/
|-- derivatives/
|-- credit/
|-- portfolio_and_risk/
|-- market_data/
`-- visualization_and_reports/
```

To add an example, place its `.ipynb` file in the appropriate category. During
the Sphinx build, `docs/conf.py` copies the notebooks into the ignored
`docs/notebooks/` directory and generates the category index pages. Do not edit
the generated copies directly.

Notebook execution is disabled during documentation builds. Store outputs in a
notebook when they should appear in the published documentation, and keep live
network calls optional.
