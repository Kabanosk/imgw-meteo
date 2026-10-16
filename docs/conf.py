"""Sphinx configuration for imgw-meteo documentation."""

from importlib.metadata import version as _version

project = "imgw-meteo"
author = "Wojciech Fiołka"
copyright = "2026, Wojciech Fiołka"
try:
    release = _version("imgw-meteo")
except Exception:  # pragma: no cover - docs may build without install
    release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "myst_parser",
    "sphinx_copybutton",
]

autodoc_typehints = "description"
autodoc_member_order = "bysource"
autodoc_mock_imports = ["torch", "tensorflow", "typer", "rich"]

napoleon_google_docstring = False
napoleon_numpy_docstring = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pandas": ("https://pandas.pydata.org/docs", None),
}

myst_enable_extensions = ["colon_fence", "deflist"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "furo"
html_title = f"imgw-meteo {release}"

source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
