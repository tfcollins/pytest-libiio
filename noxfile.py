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


VERSION_FILE = HERE / "pytest_libiio" / "__init__.py"


@nox.session(python="3.12", name="release")
def release(session):
    """Bump version, commit, tag, and optionally push.

    Usage:
        nox -s release -- patch          # 0.0.27 -> 0.0.28 (default)
        nox -s release -- minor          # 0.0.27 -> 0.1.0
        nox -s release -- major          # 0.0.27 -> 1.0.0
        nox -s release -- 0.1.0          # explicit version
        nox -s release -- patch --push   # bump + push to remote
    """
    import re
    import subprocess

    args = list(session.posargs)
    push = "--push" in args
    if push:
        args.remove("--push")

    bump = args[0] if args else "patch"

    # Read current version
    text = VERSION_FILE.read_text()
    match = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    if not match:
        session.error("Could not find __version__ in " + str(VERSION_FILE))
    current = match.group(1)
    parts = [int(x) for x in current.split(".")]

    # Calculate new version
    if bump == "major":
        parts = [parts[0] + 1, 0, 0]
    elif bump == "minor":
        parts = [parts[0], parts[1] + 1, 0]
    elif bump == "patch":
        parts = [parts[0], parts[1], parts[2] + 1]
    elif re.match(r"^\d+\.\d+\.\d+$", bump):
        parts = [int(x) for x in bump.split(".")]
    else:
        session.error(f"Invalid bump: {bump!r}  (use major/minor/patch or X.Y.Z)")

    new_version = ".".join(str(p) for p in parts)
    tag = f"v{new_version}"
    session.log(f"Bumping version: {current} -> {new_version}")

    # Update __init__.py
    new_text = text.replace(
        f'__version__ = "{current}"', f'__version__ = "{new_version}"'
    )
    VERSION_FILE.write_text(new_text)

    # Verify the build works
    session.install("build", "hatchling")
    session.run("python", "-m", "build", "--sdist", "--wheel")

    # Commit and tag
    subprocess.check_call(["git", "add", str(VERSION_FILE)])
    subprocess.check_call(["git", "commit", "-m", f"Release {tag}"])
    subprocess.check_call(["git", "tag", "-a", tag, "-m", f"Release {tag}"])
    session.log(f"Created commit and tag: {tag}")

    if push:
        subprocess.check_call(["git", "push"])
        subprocess.check_call(["git", "push", "origin", tag])
        session.log(f"Pushed {tag} to origin — CI will publish to PyPI")
    else:
        session.log(f"Run 'git push && git push origin {tag}' to trigger PyPI publish")


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
