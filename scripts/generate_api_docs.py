"""Generate the Sphinx API tree from AbaQuant source modules.

The generator is intentionally AST-based. It does not import AbaQuant, call
network providers, or require optional dependencies. Each Python package gets
an ``index.rst`` page and each implementation module gets an individual RST
page containing a source-derived symbol inventory and Sphinx ``automodule``
documentation.
"""

from __future__ import annotations

import ast
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src" / "abaquant"
OUTPUT_ROOT = ROOT / "docs" / "api"

AREA_GUIDANCE = {
    "core": (
        "Auditability and metadata primitives.",
        "Use these objects when results must retain provider, cache, request, currency, "
        "reporting-date, and transformation information.",
    ),
    "credit": (
        "Credit-risk analytics and fundamentals-derived credit proxies.",
        "Use this package for transition matrices, spread-based valuation, CDS/CDO "
        "building blocks, copula simulation, tail risk, and accounting-based credit diagnostics.",
    ),
    "derivatives": (
        "Derivative pricing, simulation, calibration, diagnostics, and strategy analysis.",
        "Use this package when valuing contingent claims, calculating Greeks, building option "
        "strategies, simulating stochastic processes, or fitting models to market observations.",
    ),
    "financial_math": (
        "Time-value, actuarial, fixed-income, corporate-finance, and portfolio mathematics.",
        "Use these functions for deterministic calculations where explicit cash-flow, rate, "
        "compounding, sign, and annualization conventions matter.",
    ),
    "marketdata": (
        "Provider-neutral market-data facades, normalized records, caching, and analytics.",
        "Use this package to retrieve or inject quotes, price history, option chains, and "
        "financial statements while preserving a stable analytical interface.",
    ),
    "portfolio": (
        "Portfolio construction, optimization, backtesting, risk metrics, and stress testing.",
        "Use this package to transform return histories and covariance estimates into weights, "
        "then evaluate those weights out of sample and under explicit scenarios.",
    ),
    "rates": (
        "Interest-rate curves, interpolation, discounting, and FRED/manual providers.",
        "Use this package when a workflow needs tenor-dependent rates or discount factors "
        "rather than one scalar risk-free-rate assumption.",
    ),
    "reports": (
        "Structured analytical reports and Markdown, HTML, or lightweight PDF export.",
        "Use these objects after calculations are complete and results must be packaged for "
        "review, storage, or distribution.",
    ),
    "risk": (
        "Integrated portfolio and credit-risk dashboards.",
        "Use this package to combine backtest, drawdown, contribution, correlation, and credit "
        "information into one review surface.",
    ),
    "visualization": (
        "Matplotlib and Plotly visualization helpers with shared themes.",
        "Use these functions to inspect model behavior, portfolio allocations, market surfaces, "
        "credit assessments, calibrations, and dashboard outputs.",
    ),
}

MODULE_GUIDANCE = {
    "types": "Defines shared enums, aliases, and result containers used by neighboring modules.",
    "data": "Provides reference data or normalized data containers; inspect units and labels before reuse.",
    "validation": "Centralizes input validation and error messages used by public calculations.",
    "errors": "Defines domain-specific exceptions that callers may catch explicitly.",
    "models": "Defines structured inputs or model-facing data containers.",
    "parameters": "Defines validated parameter objects and admissibility constraints.",
    "sessions": "Controls provider/session construction and dependency injection.",
    "base": "Defines provider protocols or abstract interfaces for custom implementations.",
    "__init__": "Defines the package facade and supported import surface.",
}


@dataclass
class Symbol:
    """One public top-level symbol extracted from a module AST."""

    kind: str
    name: str
    summary: str
    methods: list[Symbol] = field(default_factory=list)


@dataclass
class ModuleInfo:
    """AST-derived information for one Python module or package."""

    module: str
    path: Path
    is_package: bool
    docstring: str
    symbols: list[Symbol]

    @property
    def relative_parts(self) -> tuple[str, ...]:
        """Return module components below ``abaquant``."""
        parts = self.module.split(".")
        return tuple(parts[1:])

    @property
    def public_definition_count(self) -> int:
        """Return the number of public top-level definitions in this source file."""
        return len(self.symbols)


def module_name(path: Path) -> str:
    """Convert one source path into its importable module name."""
    relative = path.relative_to(ROOT / "src").with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def first_paragraph(docstring: str) -> str:
    """Return the first prose paragraph from a docstring."""
    if not docstring:
        return "Public API for this module."
    lines = []
    for raw in docstring.strip().splitlines():
        line = raw.strip()
        if not line and lines:
            break
        if line:
            lines.append(line)
    return " ".join(lines)


def first_sentence(docstring: str) -> str:
    """Return a compact, RST-safe first sentence for a symbol inventory."""
    paragraph = first_paragraph(docstring)
    match = re.search(r"(?<=[.!?])\s+", paragraph)
    text = paragraph[: match.start()] if match else paragraph
    text = re.sub(r"\s+", " ", text).strip()
    # Inline inventories should remain plain prose rather than carrying directives/roles.
    text = text.replace("`", "'").replace("|", "/")
    return text or "Public callable documented below."


def parse_module(path: Path) -> ModuleInfo:
    """Parse one source module without importing it."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    symbols: list[Symbol] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith(
            "_"
        ):
            symbols.append(
                Symbol("function", node.name, first_sentence(ast.get_docstring(node) or ""))
            )
        elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            methods: list[Symbol] = []
            for child in node.body:
                if (
                    isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and not child.name.startswith("_")
                    and child.name != "__init__"
                ):
                    methods.append(
                        Symbol("method", child.name, first_sentence(ast.get_docstring(child) or ""))
                    )
            symbols.append(
                Symbol("class", node.name, first_sentence(ast.get_docstring(node) or ""), methods)
            )
    return ModuleInfo(
        module=module_name(path),
        path=path,
        is_package=path.name == "__init__.py",
        docstring=ast.get_docstring(tree) or "",
        symbols=symbols,
    )


def normalize_directive_spacing(text: str) -> str:
    """Remove blank lines that would detach RST directive options."""
    text = re.sub(
        r"(\.\. (?:automodule|toctree)::[^\n]*\n)\n+(?=   :)",
        r"\1",
        text,
    )
    text = re.sub(r"(   :[^\n]*\n)\n+(?=   :)", r"\1", text)
    return text


def title(text: str, marker: str = "=") -> str:
    """Return an RST title block."""
    return f"{text}\n{marker * len(text)}\n"


def area_for(module: str) -> str:
    """Return the top-level AbaQuant area for a module."""
    parts = module.split(".")
    return parts[1] if len(parts) > 1 else "core"


def usage_guidance(info: ModuleInfo) -> str:
    """Build source-aware usage guidance for one module page."""
    basename = info.path.stem
    area = area_for(info.module)
    base = AREA_GUIDANCE.get(area, ("AbaQuant public API.", "Use the documented contracts below."))[
        1
    ]
    specific = MODULE_GUIDANCE.get(basename)
    if specific:
        return f"{specific} {base}"
    if ".providers." in info.module:
        return (
            "This module belongs to the provider layer. Most users reach it through the market-data "
            "facades; custom integrations can implement or instantiate the documented contracts directly."
        )
    if ".financials." in info.module:
        return (
            "This module participates in the financial-statement pipeline: provider response, normalization, "
            "cache/repository coordination, canonical line-item resolution, and analytical input construction."
        )
    if ".models." in info.module:
        return (
            "This module implements or supports one derivative model. Read the parameter constraints, pricing "
            "measure, numerical method, and limiting cases before comparing outputs across models."
        )
    if ".calibration." in info.module:
        return (
            "This module fits model parameters to observations. Inspect convergence status, residual scale, "
            "bounds, weighting, and data provenance before treating fitted parameters as stable estimates."
        )
    if ".simulation." in info.module:
        return (
            "This module generates stochastic paths or returns. Reproducible analysis should set the random "
            "seed and record time-step, horizon, drift, and volatility conventions."
        )
    if ".analytics." in info.module:
        return (
            "This module computes derived diagnostics from prices, returns, or model outputs. Ensure inputs use "
            "the frequency and units stated by each function."
        )
    return base


def inventory_lines(info: ModuleInfo) -> list[str]:
    """Create an explanatory inventory for public definitions in one source file."""
    if not info.symbols:
        return [
            "This source file primarily re-exports symbols or defines package metadata. Detailed definitions ",
            "are documented in the implementation-module pages listed below.",
            "",
        ]
    lines = []
    for symbol in info.symbols:
        role = "class" if symbol.kind == "class" else "function"
        lines.append(f"* **{role}:** ``{symbol.name}`` — {symbol.summary}")
        if symbol.methods:
            for method in symbol.methods:
                lines.append(f"  * ``{symbol.name}.{method.name}`` — {method.summary}")
    lines.append("")
    return lines


def source_children(
    infos: list[ModuleInfo], package: str
) -> tuple[list[ModuleInfo], list[ModuleInfo]]:
    """Return immediate child packages and modules for one package."""
    prefix = package + "."
    packages = []
    modules = []
    for info in infos:
        if not info.module.startswith(prefix):
            continue
        remainder = info.module[len(prefix) :]
        if "." in remainder:
            continue
        if info.is_package:
            packages.append(info)
        else:
            modules.append(info)
    return sorted(packages, key=lambda item: item.module), sorted(
        modules, key=lambda item: item.module
    )


def output_path(info: ModuleInfo) -> Path:
    """Return the RST destination for one module or package."""
    parts = info.relative_parts
    if info.module == "abaquant":
        return OUTPUT_ROOT / "root.rst"
    if info.is_package:
        return OUTPUT_ROOT.joinpath(*parts, "index.rst")
    return OUTPUT_ROOT.joinpath(*parts).with_suffix(".rst")


def write_module_page(info: ModuleInfo) -> None:
    """Write one implementation-module page."""
    path = output_path(info)
    path.parent.mkdir(parents=True, exist_ok=True)
    area = area_for(info.module)
    area_label = AREA_GUIDANCE.get(area, (area, ""))[0]
    lines = [
        title(info.module),
        f"**Import path:** ``{info.module}``\n",
        f"**Domain:** {area_label}\n",
        "Purpose\n-------\n",
        first_paragraph(info.docstring) + "\n",
        "When to use it\n--------------\n",
        usage_guidance(info) + "\n",
        "Public objects\n--------------\n",
        *inventory_lines(info),
        "Detailed reference\n------------------\n",
        f".. automodule:: {info.module}\n",
        "   :members:\n",
        "   :show-inheritance:\n",
        "   :member-order: bysource\n",
    ]
    # Pure re-export/facade modules can duplicate canonical implementation objects.
    if info.public_definition_count == 0:
        lines.append("   :no-index:\n")
    path.write_text(normalize_directive_spacing("\n".join(lines).rstrip() + "\n"), encoding="utf-8")


def write_package_page(info: ModuleInfo, infos: list[ModuleInfo]) -> None:
    """Write one package index with immediate child navigation."""
    path = output_path(info)
    path.parent.mkdir(parents=True, exist_ok=True)
    packages, modules = source_children(infos, info.module)
    area = area_for(info.module)
    area_label = AREA_GUIDANCE.get(area, (area, ""))[0]
    lines = [
        title(info.module),
        f"**Import path:** ``{info.module}``\n",
        f"**Domain:** {area_label}\n",
        "Package purpose\n---------------\n",
        first_paragraph(info.docstring) + "\n",
        "How to use this package\n-----------------------\n",
        usage_guidance(info) + "\n",
    ]
    if info.symbols:
        lines.extend(["Facade objects\n--------------\n", *inventory_lines(info)])
    leaf_package = not packages and not modules
    lines.extend(
        [
            "Package reference\n-----------------\n",
            f".. automodule:: {info.module}\n",
        ]
    )
    if leaf_package:
        lines.extend(
            [
                "   :members:\n",
                "   :show-inheritance:\n",
                "   :member-order: bysource\n",
            ]
        )
    else:
        lines.append("   :no-index:\n")
    children = packages + modules
    if children:
        lines.extend(["Modules\n-------\n", ".. toctree::\n", "   :maxdepth: 2\n", ""])
        for child in children:
            if child.is_package:
                rel = child.module.split(".")[-1] + "/index"
            else:
                rel = child.module.split(".")[-1]
            lines.append(f"   {rel}\n")
    path.write_text(normalize_directive_spacing("\n".join(lines).rstrip() + "\n"), encoding="utf-8")


def write_api_index(infos: list[ModuleInfo]) -> None:
    """Write the top-level API landing page and generated coverage report."""
    root_info = next(info for info in infos if info.module == "abaquant")
    top_packages = sorted(
        [info for info in infos if info.is_package and len(info.module.split(".")) == 2],
        key=lambda item: item.module,
    )
    functions = sum(1 for info in infos for symbol in info.symbols if symbol.kind == "function")
    classes = sum(1 for info in infos for symbol in info.symbols if symbol.kind == "class")
    methods = sum(len(symbol.methods) for info in infos for symbol in info.symbols)
    documented = 0
    total = 0
    for info in infos:
        tree = ast.parse(info.path.read_text(encoding="utf-8"), filename=str(info.path))
        for node in tree.body:
            if isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef)
            ) and not node.name.startswith("_"):
                total += 1
                documented += bool(ast.get_docstring(node))
            elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                total += 1
                documented += bool(ast.get_docstring(node))
                for method in node.body:
                    if (
                        isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and not method.name.startswith("_")
                        and method.name != "__init__"
                    ):
                        total += 1
                        documented += bool(ast.get_docstring(method))

    index = [
        title("Complete API reference"),
        "This section is generated from the AbaQuant source tree and then rendered by",
        "Sphinx autodoc. It complements the conceptual domain guides: the guides explain",
        "model choice and workflow design, while these pages document callable contracts.\n",
        "What each entry contains\n------------------------\n",
        "Each module page provides:\n",
        "* the canonical import path;",
        "* a purpose and usage explanation;",
        "* an inventory of public functions, classes, methods, and properties;",
        "* callable signatures and type hints;",
        "* parameter, return-value, exception, and notes sections from source docstrings; and",
        "* inheritance information for classes.\n",
        "Coverage\n--------\n",
        f"The generated tree covers **{len(infos)} Python modules/packages**,",
        f"**{functions} public functions**, **{classes} public classes**, and",
        f"**{methods} public methods or properties** discovered by the AST inventory.",
        f"The documentation guard reports docstrings for **{documented}/{total} public definitions**.\n",
        ".. note::\n",
        "   “Public” means a source definition whose name does not begin with an underscore.",
        "   Package facades may also re-export canonical definitions documented on their",
        "   implementation-module pages.\n",
        "Navigation\n----------\n",
        ".. toctree::\n",
        "   :maxdepth: 3\n",
        "",
        "   root\n",
    ]
    for package in top_packages:
        index.append(f"   {package.module.split('.')[-1]}/index\n")
    (OUTPUT_ROOT / "index.rst").write_text(
        normalize_directive_spacing("\n".join(index).rstrip() + "\n"), encoding="utf-8"
    )

    root_lines = [
        title("abaquant root facade"),
        "The root namespace provides version metadata and convenience re-exports. For ",
        "long-lived production code, prefer the domain namespaces shown below because they ",
        "make dependencies and ownership clearer.\n",
        ".. code-block:: python\n",
        "   :caption: Prefer explicit domain imports\n",
        "",
        "   import abaquant",
        "   from abaquant.derivatives import black_scholes",
        "   from abaquant.portfolio import PortfolioAllocator\n",
        "Root package documentation\n--------------------------\n",
        ".. automodule:: abaquant\n",
        "   :no-index:\n",
        "",
        "Domain packages\n---------------\n",
    ]
    for package in top_packages:
        name = package.module.split(".")[-1]
        summary = AREA_GUIDANCE.get(name, (first_paragraph(package.docstring), ""))[0]
        root_lines.append(f"* :doc:`{name}/index` — {summary}")
    root_lines.append("")
    output_path(root_info).write_text(
        normalize_directive_spacing("\n".join(root_lines)), encoding="utf-8"
    )


def main() -> int:
    """Regenerate the complete API documentation tree."""
    infos = [parse_module(path) for path in sorted(SOURCE_ROOT.rglob("*.py"))]
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True)
    for info in infos:
        if info.module == "abaquant":
            continue
        if info.is_package:
            write_package_page(info, infos)
        else:
            write_module_page(info)
    write_api_index(infos)
    print(f"Generated API documentation for {len(infos)} modules/packages in {OUTPUT_ROOT}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
