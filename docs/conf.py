"""Sphinx configuration for the AbaQuant documentation."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

project = "AbaQuant"
author = "AbaQuant contributors"
release = "1.0.0rc1"
version = "1.0.0rc1"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.mathjax",
    "sphinx_copybutton",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

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

nitpicky = False
