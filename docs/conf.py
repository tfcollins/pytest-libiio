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
html_logo = "_static/logo-pytest-libiio-banana.svg"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_theme_options = {
    "light_logo": "logo-pytest-libiio-banana.svg",
    "dark_logo": "logo-pytest-libiio-banana.svg",
}

myst_enable_extensions = ["colon_fence"]

source_suffix = {".rst": "restructuredtext", ".md": "markdown"}

master_doc = "index"

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
