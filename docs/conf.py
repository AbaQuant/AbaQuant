"""Sphinx configuration for the AbaQuant documentation."""

from __future__ import annotations

import sys
from pathlib import Path
from shutil import copy2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


# Copy example notebooks into the Sphinx source tree without rewriting unchanged files.
NOTEBOOKS_SRC = ROOT / "examples_notebooks"
NOTEBOOKS_DST = Path(__file__).resolve().parent / "notebooks"
NOTEBOOK_SECTION_TITLES = {
    "foundations": "Foundations",
    "financial_math_and_rates": "Financial Math and Rates",
    "derivatives": "Derivatives",
    "credit": "Credit",
    "portfolio_and_risk": "Portfolio and Risk",
    "market_data": "Market Data",
    "visualization_and_reports": "Visualization and Reports",
}


def write_generated_page(path: Path, content: str) -> None:
    """Write a generated documentation page only when its content changed."""
    if not path.exists() or path.read_text(encoding="utf-8") != content:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def create_notebook_indexes(source_notebooks: dict[Path, Path]) -> None:
    """Generate nested Sphinx indexes from the notebook directory structure."""
    notebooks_by_section: dict[str, list[Path]] = {}
    for relative_path in source_notebooks:
        if len(relative_path.parts) != 2:
            raise RuntimeError(
                "Example notebooks must live in one category directory under examples_notebooks/."
            )
        notebooks_by_section.setdefault(relative_path.parts[0], []).append(relative_path)

    configured_sections = [
        section for section in NOTEBOOK_SECTION_TITLES if section in notebooks_by_section
    ]
    extra_sections = sorted(set(notebooks_by_section) - set(NOTEBOOK_SECTION_TITLES))
    ordered_sections = configured_sections + extra_sections

    expected_indexes = {Path("index.rst")}
    for section in ordered_sections:
        expected_indexes.add(Path(section) / "index.rst")
    for index_path in NOTEBOOKS_DST.rglob("index.rst"):
        if index_path.relative_to(NOTEBOOKS_DST) not in expected_indexes:
            index_path.unlink()

    root_entries = "\n".join(f"   {section}/index" for section in ordered_sections)
    write_generated_page(
        NOTEBOOKS_DST / "index.rst",
        "Examples\n========\n\n"
        "Executable notebooks organized by analytical domain. The documentation build "
        "renders saved notebook content without executing live data requests.\n\n"
        ".. toctree::\n"
        "   :maxdepth: 2\n\n"
        f"{root_entries}\n",
    )

    for section in ordered_sections:
        title = NOTEBOOK_SECTION_TITLES.get(section, section.replace("_", " ").title())
        notebook_entries = "\n".join(
            f"   {relative_path.stem}" for relative_path in sorted(notebooks_by_section[section])
        )
        write_generated_page(
            NOTEBOOKS_DST / section / "index.rst",
            f"{title}\n{'=' * len(title)}\n\n.. toctree::\n   :maxdepth: 1\n\n{notebook_entries}\n",
        )


def sync_example_notebooks() -> None:
    """Mirror notebook sources into the generated documentation directory."""
    if not NOTEBOOKS_SRC.exists():
        return

    source_notebooks = {
        source.relative_to(NOTEBOOKS_SRC): source for source in NOTEBOOKS_SRC.rglob("*.ipynb")
    }
    NOTEBOOKS_DST.mkdir(parents=True, exist_ok=True)

    for destination in NOTEBOOKS_DST.rglob("*.ipynb"):
        if destination.relative_to(NOTEBOOKS_DST) not in source_notebooks:
            destination.unlink()

    for relative_path, source in source_notebooks.items():
        destination = NOTEBOOKS_DST / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists() or destination.read_bytes() != source.read_bytes():
            copy2(source, destination)

    create_notebook_indexes(source_notebooks)


sync_example_notebooks()


# -- Project information -----------------------------------------------------
project = "AbaQuant"
author = "AbaQuant contributors"
release = "1.0.0rc1"
version = "1.0.0rc1"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.mathjax",
    "sphinx_copybutton",
    "myst_nb",
]

nb_execution_mode = "off"

templates_path = ["_templates"]
exclude_patterns = ["_build", "reports/**", "Thumbs.db", ".DS_Store"]

autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_preserve_defaults = True
autoclass_content = "both"
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False
napoleon_use_param = True
napoleon_use_rtype = True

html_theme = "furo"
html_title = "AbaQuant 1.0.0rc1 documentation"
html_baseurl = "https://abaquant.github.io/AbaQuant/"
html_show_sourcelink = False
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_theme_options = {
    "source_repository": "https://github.com/AbaQuant/AbaQuant/",
    "source_branch": "main",
    "source_directory": "docs/",
}
html_logo = "_static/abaquant-logo.svg"

nitpicky = False
