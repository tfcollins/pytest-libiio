project = "pytest-libiio"
author = "Travis F. Collins"
copyright = "2024, Travis F. Collins"

extensions = [
    "myst_parser",
    "sphinx_click",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

html_theme = "furo"

html_static_path = ["_static"]
html_favicon = "_static/favicon-pytest-libiio.svg"
html_theme_options = {
    "light_logo": "logo-pytest-libiio.svg",
    "dark_logo": "logo-pytest-libiio.svg",
}

myst_enable_extensions = ["colon_fence"]

source_suffix = {".rst": "restructuredtext", ".md": "markdown"}

master_doc = "index"

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "logo-design-notes.md"]
