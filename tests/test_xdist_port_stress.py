"""Stress tests for xdist port allocation in iio-emu emulation support."""

import os
import time
import types
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest

import pytest_libiio.plugin as plugin

PYADI_IIO_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "pyadi-iio")
PYADI_IIO_REPO = "https://github.com/analogdevicesinc/pyadi-iio.git"

# ---------------------------------------------------------------------------
# Helpers (duplicated from test_plugin_unit to avoid cross-test coupling)
# ---------------------------------------------------------------------------


class FakeConfig:
    def __init__(self, options=None):
        self.options = options or {}

    def getoption(self, name, default=None):
        return self.options.get(name, default)


def _calc_port(worker_id):
    """Replicate the port calculation from _iio_emu fixture (plugin.py:446-450)."""
    if worker_id == "master":
        return None
    num = int(worker_id.replace("gw", ""))
    return plugin.IIO_EMU_BASE_PORT + num


def _patch_emu_deps(monkeypatch):
    """Apply common monkeypatches for iio_emu_manager construction."""
    monkeypatch.setattr(plugin.iio_emu_manager, "__del__", lambda self: None)
    monkeypatch.setattr(plugin, "which", lambda name: "/usr/bin/iio-emu")
    monkeypatch.setattr(plugin.socket, "gethostname", lambda: "testhost")
    monkeypatch.setattr(plugin.socket, "gethostbyname", lambda h: "127.0.0.1")
    monkeypatch.delenv("IIO_EMU_URI", raising=False)


# ---------------------------------------------------------------------------
# Test 1: Port calculation correctness
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "wid, expected_port",
    [
        ("master", None),
        ("gw0", 30431),
        ("gw1", 30432),
        ("gw2", 30433),
        ("gw10", 30441),
        ("gw49", 30480),
        ("gw99", 30530),
    ],
)
def test_port_calculation_correctness(wid, expected_port):
    assert _calc_port(wid) == expected_port


# ---------------------------------------------------------------------------
# Test 2: Port uniqueness across many workers
# ---------------------------------------------------------------------------


def test_port_uniqueness_across_many_workers():
    ports = [_calc_port(f"gw{i}") for i in range(100)]
    assert len(set(ports)) == 100, "All 100 worker ports must be unique"
    # Master uses default port (None → base port implicitly), so no worker
    # port should equal the base port used when custom_port is None.
    # gw0 gets IIO_EMU_BASE_PORT + 0 == base port, which is actually the same
    # numeric value. That's by design — master uses custom_port=None (no -p flag)
    # while gw0 uses custom_port=30431 (explicit -p flag). Verify the distinction:
    assert _calc_port("master") is None
    assert _calc_port("gw0") == plugin.IIO_EMU_BASE_PORT


# ---------------------------------------------------------------------------
# Test 3: Master worker URI has no port suffix
# ---------------------------------------------------------------------------


def test_master_worker_uri_has_no_port_suffix(monkeypatch):
    _patch_emu_deps(monkeypatch)
    m = plugin.iio_emu_manager("x.xml", custom_port=None)
    assert m.uri == "ip:127.0.0.1"
    assert ":" not in m.uri.split("ip:")[1]


# ---------------------------------------------------------------------------
# Test 4: URI format with custom ports
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "port",
    [30431, 30432, 30450, 30480, 30530],
)
def test_uri_format_with_custom_ports(monkeypatch, port):
    _patch_emu_deps(monkeypatch)
    m = plugin.iio_emu_manager("x.xml", custom_port=port)
    assert m.uri == f"ip:127.0.0.1:{port}"


# ---------------------------------------------------------------------------
# Test 5: _iio_emu fixture port assignment
# ---------------------------------------------------------------------------


class FakeEmu:
    def __init__(self, xml_path, auto, custom_port=None):
        self.xml_path = xml_path
        self.auto = auto
        self.custom_port = custom_port
        self.started = 0
        self.stopped = 0

    def start(self):
        self.started += 1

    def stop(self):
        self.stopped += 1


@pytest.mark.parametrize(
    "wid, expected_port",
    [
        ("gw0", 30431),
        ("gw5", 30436),
        ("gw25", 30456),
        ("gw49", 30480),
    ],
)
def test_iio_emu_fixture_port_assignment(monkeypatch, tmp_path, wid, expected_port):
    monkeypatch.setattr(plugin, "iio_emu_manager", FakeEmu)
    xml = tmp_path / "ctx.xml"
    xml.write_text("<x/>")
    request = types.SimpleNamespace(
        config=FakeConfig(
            {
                "--emu": True,
                "--emu-xml": str(xml),
                "--adi-hw-map": False,
                "--custom-hw-map": None,
            }
        )
    )
    gen = plugin._iio_emu.__wrapped__(request, wid)
    emu = next(gen)
    assert emu.custom_port == expected_port
    assert emu.started == 1
    with pytest.raises(StopIteration):
        next(gen)
    assert emu.stopped == 1


# ---------------------------------------------------------------------------
# Test 6: Concurrent iio_emu_manager construction (stress)
# ---------------------------------------------------------------------------


def test_concurrent_emu_manager_construction(monkeypatch):
    _patch_emu_deps(monkeypatch)
    num_workers = 50
    results = [None] * num_workers

    def build(i):
        port = plugin.IIO_EMU_BASE_PORT + i
        m = plugin.iio_emu_manager("x.xml", custom_port=port)
        return m.uri

    with ThreadPoolExecutor(max_workers=num_workers) as pool:
        futures = {pool.submit(build, i): i for i in range(num_workers)}
        for fut in as_completed(futures):
            idx = futures[fut]
            results[idx] = fut.result()

    # All URIs must be present and unique
    assert None not in results
    assert len(set(results)) == num_workers
    for i, uri in enumerate(results):
        assert uri == f"ip:127.0.0.1:{plugin.IIO_EMU_BASE_PORT + i}"


# ---------------------------------------------------------------------------
# Test 7: Concurrent start/stop lifecycle (stress)
# ---------------------------------------------------------------------------


class FakeProc:
    def __init__(self):
        self.signals = []

    def poll(self):
        return 0  # success

    def send_signal(self, sig):
        self.signals.append(sig)


def test_concurrent_start_stop_lifecycle(monkeypatch, tmp_path):
    _patch_emu_deps(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(plugin.time, "sleep", lambda _: None)

    num_workers = 20
    commands = []

    def fake_popen(cmd):
        commands.append(cmd)
        return FakeProc()

    monkeypatch.setattr(plugin.subprocess, "Popen", fake_popen)

    results = [None] * num_workers

    def run_lifecycle(i):
        port = plugin.IIO_EMU_BASE_PORT + i
        m = plugin.iio_emu_manager("ctx.xml", custom_port=port)
        m.start()
        m.stop()
        return port

    with ThreadPoolExecutor(max_workers=num_workers) as pool:
        futures = {pool.submit(run_lifecycle, i): i for i in range(num_workers)}
        for fut in as_completed(futures):
            idx = futures[fut]
            results[idx] = fut.result()

    # Every worker ran without error
    assert None not in results
    assert len(set(results)) == num_workers

    # Each command included -p with the correct port
    assert len(commands) == num_workers
    for cmd in commands:
        assert "-p" in cmd
        port_idx = cmd.index("-p") + 1
        port_val = int(cmd[port_idx])
        assert (
            plugin.IIO_EMU_BASE_PORT
            <= port_val
            < plugin.IIO_EMU_BASE_PORT + num_workers
        )


# ---------------------------------------------------------------------------
# Test 8: Port range bounds
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("num_workers", [100, 500])
def test_port_range_bounds(num_workers):
    for i in range(num_workers):
        port = _calc_port(f"gw{i}")
        assert port > 1024, f"Worker gw{i} port {port} is in privileged range"
        assert port <= 65535, f"Worker gw{i} port {port} exceeds valid port range"
    # Verify expected boundaries
    assert _calc_port("gw0") == plugin.IIO_EMU_BASE_PORT
    assert (
        _calc_port(f"gw{num_workers - 1}") == plugin.IIO_EMU_BASE_PORT + num_workers - 1
    )


# ---------------------------------------------------------------------------
# Integration: pytester + real iio-emu + xdist
# ---------------------------------------------------------------------------


_LOCALHOST_CONFTEST = """
import pytest_libiio.plugin as _plugin
import socket as _socket

# Force iio-emu to bind to localhost so tests work in CI where
# socket.gethostbyname(socket.gethostname()) may return an unreachable IP.
_orig_gethostbyname = _socket.gethostbyname
_plugin.socket.gethostbyname = lambda h: "127.0.0.1"
"""


@pytest.mark.parametrize("num_workers", [2, 4])
def test_xdist_emulation_with_multiple_workers(testdir, num_workers):
    """Run multiple emulated device tests in parallel via xdist.

    Each worker gets its own iio-emu instance on a unique port. This verifies
    the full integration: port allocation, iio-emu lifecycle, and parallel
    test execution with real IIO contexts.
    """
    testdir.makeconftest(_LOCALHOST_CONFTEST)
    testdir.makepyfile(
        """
        import pytest
        import iio

        @pytest.mark.iio_hardware("pluto")
        def test_pluto_context(iio_uri):
            ctx = iio.Context(iio_uri)
            assert ctx.devices

        @pytest.mark.iio_hardware("ad9081")
        def test_ad9081_context(iio_uri):
            ctx = iio.Context(iio_uri)
            assert ctx.devices

        @pytest.mark.iio_hardware("fmcomms2")
        def test_fmcomms2_context(iio_uri):
            ctx = iio.Context(iio_uri)
            assert ctx.devices

        @pytest.mark.iio_hardware("daq2")
        def test_daq2_context(iio_uri):
            ctx = iio.Context(iio_uri)
            assert ctx.devices
    """
    )
    result = testdir.runpytest(
        "--adi-hw-map",
        "--emu",
        "--skip-scan",
        "-v",
        f"-n={num_workers}",
    )
    result.stdout.fnmatch_lines(["*passed*"])
    assert result.ret == 0


@pytest.mark.parametrize("num_workers", [2, 4])
def test_xdist_emulation_repeated_device(testdir, num_workers):
    """Stress the same emulated device across multiple xdist workers.

    All tests target the same hardware type. Each worker manages its own
    iio-emu instance on a separate port, testing that multiple identical
    emulations can run concurrently.
    """
    testdir.makeconftest(_LOCALHOST_CONFTEST)
    testdir.makepyfile(
        """
        import pytest
        import iio

        @pytest.mark.iio_hardware("pluto")
        def test_pluto_ctx_a(iio_uri):
            ctx = iio.Context(iio_uri)
            devs = [d.name for d in ctx.devices]
            assert "ad9361-phy" in devs

        @pytest.mark.iio_hardware("pluto")
        def test_pluto_ctx_b(iio_uri):
            ctx = iio.Context(iio_uri)
            devs = [d.name for d in ctx.devices]
            assert "cf-ad9361-lpc" in devs

        @pytest.mark.iio_hardware("pluto")
        def test_pluto_ctx_c(iio_uri):
            ctx = iio.Context(iio_uri)
            devs = [d.name for d in ctx.devices]
            assert "cf-ad9361-dds-core-lpc" in devs

        @pytest.mark.iio_hardware("pluto")
        def test_pluto_ctx_d(iio_uri):
            ctx = iio.Context(iio_uri)
            assert len(ctx.devices) > 0
    """
    )
    result = testdir.runpytest(
        "--adi-hw-map",
        "--emu",
        "--skip-scan",
        "-v",
        f"-n={num_workers}",
    )
    result.stdout.fnmatch_lines(["*4 passed*"])
    assert result.ret == 0


# ---------------------------------------------------------------------------
# Integration: pyadi-iio emulation test suite with xdist
# ---------------------------------------------------------------------------


def _ensure_pyadi_iio():
    """Clone pyadi-iio at the latest release tag if not already present."""
    import subprocess

    repo_dir = os.path.abspath(PYADI_IIO_DIR)
    if os.path.isdir(os.path.join(repo_dir, "test")):
        return repo_dir

    print(f"Cloning pyadi-iio into {repo_dir} ...")
    subprocess.check_call(
        ["git", "clone", "--depth=1", PYADI_IIO_REPO, repo_dir],
    )
    # Fetch tags and check out the latest release
    subprocess.check_call(
        ["git", "-C", repo_dir, "fetch", "--tags", "--depth=1"],
    )
    latest_tag = (
        subprocess.check_output(
            ["git", "-C", repo_dir, "tag", "--sort=-v:refname"],
        )
        .decode()
        .split("\n")[0]
        .strip()
    )
    if latest_tag:
        print(f"Checking out latest release: {latest_tag}")
        subprocess.check_call(
            ["git", "-C", repo_dir, "checkout", latest_tag],
        )
    return repo_dir


@pytest.mark.skipif(
    not os.environ.get("PYADI_IIO_STRESS"),
    reason="Set PYADI_IIO_STRESS=1 to run (requires numpy, scipy, pyadi-iio)",
)
@pytest.mark.parametrize("num_workers", [2, 4])
def test_xdist_pyadi_iio_emulation(num_workers):
    """Run pyadi-iio emulation tests with xdist parallel workers.

    This is the most rigorous stress test: it exercises the full pytest-libiio
    plugin with real pyadi-iio device driver tests, real iio-emu instances,
    and xdist parallelism across multiple workers.

    Automatically clones pyadi-iio at the latest release tag if not found
    at ../pyadi-iio.
    """
    import subprocess
    import sys

    repo_dir = _ensure_pyadi_iio()

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "test/test_pluto_p.py",
            "test/test_ad9081.py",
            "test/test_daq2_p.py",
            "test/test_ad9361_p.py",
            "test/test_daq3_p.py",
            "--emu",
            "--skip-scan",
            "-k",
            "not prod and not stress and not tx_data and not cyclic"
            " and not sfdr and not cw and not iq and not dds"
            " and not loopback and not gain_check and not dc",
            "-p",
            "no:labgrid",
            "-q",
            "--tb=short",
            f"-n={num_workers}",
        ],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=300,
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    assert result.returncode == 0, f"pyadi-iio tests failed:\n{result.stdout}"
    assert "passed" in result.stdout
