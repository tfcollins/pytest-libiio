import nox

nox.options.default_venv_backend = "uv"

PYTHON_VERSIONS = ["3.9", "3.10", "3.11", "3.12"]

TEST_DEPS = [
    "pytest>=3.0",
    "pylibiio==0.23.1",
    "pyyaml",
    "pytest-mock",
    "pytest-cov",
    "pytest-xdist",
    "paramiko",
]


@nox.session(python=PYTHON_VERSIONS)
def tests(session):
    """Run the test suite."""
    session.install(*TEST_DEPS)
    session.install("-e", ".")
    session.run(
        "pytest",
        "tests",
        "--cov=pytest_libiio",
        "--cov-append",
        "--cov-report=term-missing",
        "--resource-dir=tests/resources",
        *session.posargs,
    )


@nox.session(python="3.9")
def lint(session):
    """Lint with ruff."""
    session.install("ruff")
    session.run("ruff", "check", "pytest_libiio", "tests")


@nox.session(python="3.9")
def format_check(session):
    """Check formatting with ruff format."""
    session.install("ruff")
    session.run("ruff", "format", "--check", "pytest_libiio", "tests")


@nox.session(python="3.9")
def mypy(session):
    """Type-check with mypy."""
    session.install(
        "mypy", "pytest", "pylibiio==0.23.1", "pyyaml", "paramiko", "lxml", "click"
    )
    session.install("-e", ".")
    session.run("mypy", "pytest_libiio")


@nox.session(python="3.9")
def clean(session):
    """Erase coverage data."""
    session.install("coverage")
    session.run("coverage", "erase")


@nox.session(python="3.9")
def docs(session):
    """Build Sphinx documentation."""
    session.install(
        "sphinx", "furo", "myst-parser", "sphinx-click",
        "jinja2", "pyyaml", "pylibiio", "paramiko",
    )
    session.install("-e", ".")
    session.run("sphinx-build", "-b", "html", "docs", "docs/_build/html")
