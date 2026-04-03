import pathlib

import nox

nox.options.default_venv_backend = "uv"

HERE = pathlib.Path(__file__).parent

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
        f"--resource-dir={HERE / 'tests' / 'resources'}",
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
        "sphinx",
        "furo",
        "myst-parser",
        "sphinx-click",
        "jinja2",
        "pyyaml",
        "pylibiio",
        "paramiko",
    )
    session.install("-e", ".")
    session.run("sphinx-build", "-b", "html", "docs", "docs/_build/html")


PYADI_IIO_DIR = HERE.parent / "pyadi-iio"
PYADI_IIO_REPO = "https://github.com/analogdevicesinc/pyadi-iio.git"

PYADI_IIO_DEPS = [
    "pyadi-iio",
    "numpy",
    "scipy",
    "plotly",
    "pytest-html",
]


def _ensure_pyadi_iio(session):
    """Clone pyadi-iio at the latest release tag if not already present."""
    import subprocess

    if PYADI_IIO_DIR.is_dir():
        session.log(f"Using existing pyadi-iio at {PYADI_IIO_DIR}")
        return
    session.log(f"Cloning pyadi-iio into {PYADI_IIO_DIR} ...")
    subprocess.check_call(
        ["git", "clone", "--depth=1", PYADI_IIO_REPO, str(PYADI_IIO_DIR)],
    )
    # Fetch tags and check out the latest release
    subprocess.check_call(
        ["git", "-C", str(PYADI_IIO_DIR), "fetch", "--tags", "--depth=1"],
    )
    latest_tag = (
        subprocess.check_output(
            ["git", "-C", str(PYADI_IIO_DIR), "tag", "--sort=-v:refname"],
        )
        .decode()
        .split("\n")[0]
        .strip()
    )
    if latest_tag:
        session.log(f"Checking out latest release: {latest_tag}")
        subprocess.check_call(
            ["git", "-C", str(PYADI_IIO_DIR), "checkout", latest_tag],
        )


@nox.session(python="3.12", name="stress")
def stress(session):
    """Stress-test xdist port allocation with pyadi-iio emulation tests.

    Clones pyadi-iio at the latest release if not found at ../pyadi-iio.
    Pass the number of xdist workers as a positional arg (default: 4):

        nox -s stress -- 8
    """
    _ensure_pyadi_iio(session)
    session.install(*TEST_DEPS, *PYADI_IIO_DEPS)
    session.install("-e", ".")
    num_workers = session.posargs[0] if session.posargs else "4"
    test_files = [
        "test/test_pluto_p.py",
        "test/test_ad9081.py",
        "test/test_daq2_p.py",
        "test/test_ad9361_p.py",
        "test/test_daq3_p.py",
        "test/test_fmcomms5_p.py",
        "test/test_adrv9009_p.py",
    ]
    session.run(
        "pytest",
        *test_files,
        "--emu",
        "--skip-scan",
        "-k",
        "not prod and not stress and not tx_data and not cyclic"
        " and not sfdr and not cw and not iq and not dds"
        " and not loopback and not gain_check and not dc",
        "-p",
        "no:labgrid",
        "-v",
        f"-n={num_workers}",
        env={"PYTHONPATH": str(PYADI_IIO_DIR)},
    )


@nox.session(python=False, name="act")
def act_session(session):
    """Install act (if needed) and run the CI test workflow locally."""
    import shutil

    if not shutil.which("act"):
        session.log("act not found — installing to ~/.local/bin")
        session.run(
            "bash",
            "-c",
            "curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh"
            " | bash -s -- -b ~/.local/bin",
            external=True,
        )

    # Run each Python version separately: Docker containers share network="host",
    # so parallel matrix jobs would conflict on iio-emu's port 30431.
    for python_version in PYTHON_VERSIONS:
        session.run(
            "act",
            "push",
            "--job",
            "Test",
            "--workflows",
            ".github/workflows/test.yml",
            "--matrix",
            f"python-version:{python_version}",
            *session.posargs,
            external=True,
        )
