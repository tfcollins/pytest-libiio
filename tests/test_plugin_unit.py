import types

import pytest

import pytest_libiio.plugin as plugin


class FakeConfig:
    def __init__(self, options=None):
        self.options = options or {}
        self.pytest_libiio = None

    def getoption(self, name, default=None):
        return self.options.get(name, default)

    def addinivalue_line(self, *args, **kwargs):
        self._added_marker = (args, kwargs)

    def getini(self, name):
        return "%(message)s"


class FakeRequest:
    def __init__(self, options=None, marker=None, test_name="test_fn"):
        self.config = FakeConfig(options)
        self.node = types.SimpleNamespace(
            name=test_name, get_closest_marker=lambda name: marker
        )


class FakeItem:
    def __init__(self, marker):
        self._marker = marker
        self.added = []

    def get_closest_marker(self, name):
        return self._marker

    def add_marker(self, mark):
        self.added.append(mark)


def test_iio_emu_manager_init_uri_and_missing_binary(monkeypatch):
    monkeypatch.setattr(plugin.iio_emu_manager, "__del__", lambda self: None)
    monkeypatch.setattr(plugin, "which", lambda name: None)
    with pytest.raises(Exception, match="iio-emu not found"):
        plugin.iio_emu_manager("x.xml")

    monkeypatch.setattr(plugin, "which", lambda name: "/usr/bin/iio-emu")
    monkeypatch.setattr(plugin.socket, "gethostname", lambda: "host")
    monkeypatch.setattr(plugin.socket, "gethostbyname", lambda hostname: "127.0.0.2")

    monkeypatch.delenv("IIO_EMU_URI", raising=False)
    m = plugin.iio_emu_manager("x.xml", custom_port=5555)
    assert m.uri == "ip:127.0.0.2:5555"

    monkeypatch.setenv("IIO_EMU_URI", "ip:9.9.9.9:30431")
    m2 = plugin.iio_emu_manager("x.xml")
    assert m2.uri == "ip:9.9.9.9:30431"


def test_iio_emu_manager_start_stop_and_failure(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(plugin, "which", lambda name: "/usr/bin/iio-emu")
    monkeypatch.setattr(plugin.socket, "gethostname", lambda: "host")
    monkeypatch.setattr(plugin.socket, "gethostbyname", lambda hostname: "127.0.0.2")
    monkeypatch.setattr(plugin.time, "sleep", lambda _: None)

    called = {}

    class Proc:
        def __init__(self, fail=False):
            self.fail = fail
            self.signals = []

        def poll(self):
            return 1 if self.fail else 0

        def send_signal(self, sig):
            self.signals.append(sig)

    good_proc = Proc(fail=False)

    def fake_popen(cmd):
        called["cmd"] = cmd
        return good_proc

    monkeypatch.setattr(plugin.subprocess, "Popen", fake_popen)

    m = plugin.iio_emu_manager("ctx.xml", custom_port=30499)
    m.data_devices = ["iio:device1", "iio:device2"]
    m.start()
    assert (tmp_path / "data.bin").exists()
    assert "iio:device1@data.bin" in called["cmd"]
    assert "-p" in called["cmd"]
    m.stop()
    assert good_proc.signals

    bad_proc = Proc(fail=True)
    monkeypatch.setattr(plugin.subprocess, "Popen", lambda cmd: bad_proc)

    m = plugin.iio_emu_manager("ctx.xml")
    with pytest.raises(Exception, match="failed to start"):
        m.start()
    assert bad_proc.signals


def test_gen_markdown_table_and_filename_helpers(tmp_path):
    data = {
        "pluto": {"device_coverage": 0.5, "total_coverage": 0.75, "foo": 1},
        "ad9081": {"channel_coverage": 0.2},
    }
    report = tmp_path / "cov" / "report.md"
    plugin.gen_markdown_table(data, str(report))

    text = report.read_text()
    assert "IIO Coverage Report" in text
    assert "device_coverage" in text
    assert "total_coverage" in text
    assert "foo" not in text

    hw_map = {
        "pluto": [{"emulate": [{"filename": "pluto.xml"}, {"data_devices": ["d0"]}]}]
    }
    assert plugin.get_filename(hw_map, "pluto") == ("pluto.xml", ["d0"])


def test_get_hw_map_variants(monkeypatch, tmp_path):
    path = tmp_path / "map.yml"
    path.write_text("pluto:\n  - ad9361-phy\n")

    called = {}

    def fake_import(filename):
        called["filename"] = filename
        return {"ok": True}

    monkeypatch.setattr(plugin, "import_hw_map", fake_import)

    req = types.SimpleNamespace(config=FakeConfig({"--adi-hw-map": True}))
    assert plugin.get_hw_map(req) == {"ok": True}
    assert called["filename"].endswith("adi_hardware_map.yml")

    req = types.SimpleNamespace(
        config=FakeConfig({"--adi-hw-map": False, "--custom-hw-map": str(path)})
    )
    assert plugin.get_hw_map(req) == {"ok": True}
    assert called["filename"] == str(path)

    req = types.SimpleNamespace(
        config=FakeConfig({"--adi-hw-map": False, "--custom-hw-map": None})
    )
    assert plugin.get_hw_map(req) is None


def test_handle_iio_emu_restart_and_skip(monkeypatch, tmp_path):
    ctx = {"hw": "pluto", "uri": "ip:1.2.3.4"}

    class Emu:
        auto = True
        current_device = None
        p = None
        xml_path = None
        data_devices = None

        def __init__(self):
            self.started = 0
            self.stopped = 0

        def start(self):
            self.started += 1

        def stop(self):
            self.stopped += 1

    emu = Emu()
    req = types.SimpleNamespace(config=FakeConfig({"--emu-xml-dir": str(tmp_path)}))

    monkeypatch.setattr(
        plugin,
        "get_hw_map",
        lambda request: {"pluto": [{"emulate": [{"filename": "p.xml"}]}]},
    )

    # file missing => skip
    with pytest.raises(pytest.skip.Exception):
        plugin.handle_iio_emu(ctx, req, emu)

    (tmp_path / "p.xml").write_text("<x/>")
    out = plugin.handle_iio_emu(ctx, req, emu)
    assert out is ctx
    assert emu.started == 1
    assert emu.xml_path == str(tmp_path / "p.xml")

    emu.p = object()
    ctx2 = {"hw": "ad9081", "uri": "ip:1.2.3.4"}
    monkeypatch.setattr(
        plugin,
        "get_hw_map",
        lambda request: {"ad9081": [{"emulate": [{"filename": "p.xml"}]}]},
    )
    plugin.handle_iio_emu(ctx2, req, emu)
    assert emu.stopped == 1

    # no filename path returns untouched context
    monkeypatch.setattr(plugin, "get_filename", lambda m, hw: (None, None))
    assert plugin.handle_iio_emu(ctx2, req, emu) is ctx2


def test_pytest_configure_and_collection(monkeypatch):
    config = FakeConfig()
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw1")

    called = {}

    def fake_basicConfig(**kwargs):
        called.update(kwargs)

    monkeypatch.setattr(plugin.logging, "basicConfig", fake_basicConfig)
    plugin.pytest_configure(config)
    assert "filename" in called and called["filename"] == "tests_gw1.log"

    monkeypatch.setattr(
        plugin,
        "find_contexts",
        lambda config, hw_map, request: [{"uri": "u", "hw": "pluto"}],
    )
    monkeypatch.setattr(plugin, "get_hw_map", lambda request: {"pluto": []})

    marker = types.SimpleNamespace(name="iio_hardware", args=("pluto",))
    item = FakeItem(marker)
    plugin.pytest_collection_modifyitems(config, [item])
    assert item.added


def test_sessionstart_and_sessionfinish(monkeypatch, tmp_path, capsys):
    class FakeTracker:
        def __init__(self):
            self.trackers = {
                "pluto": types.SimpleNamespace(
                    results_folder=None,
                    print_context_map=lambda: None,
                    export_to_file=lambda: None,
                    calculate_coverage=lambda: {"total_coverage": 1.0},
                )
            }
            self.track_debug_props = False

        def do_monkey_patch(self):
            self.patched = True

    monkeypatch.setattr(plugin, "MultiContextTracker", FakeTracker)

    session = types.SimpleNamespace(
        config=FakeConfig(
            {
                "--iio-coverage": True,
                "--iio-coverage-debug-props": True,
                "--iio-coverage-print-results": True,
                "--iio-coverage-folder": str(tmp_path / "iio_cov"),
            }
        )
    )

    plugin.pytest_sessionstart(session)
    assert session.config.pytest_libiio.coverage_tracker.track_debug_props is True

    called = {}

    def fake_md(data, filename):
        called["filename"] = filename

    monkeypatch.setattr(plugin, "gen_markdown_table", fake_md)
    plugin.pytest_sessionfinish(session, 0)
    assert called["filename"].endswith("iio_coverage_report.md")

    session2 = types.SimpleNamespace(
        config=FakeConfig({"--iio-coverage": True, "--iio-coverage-folder": "x"})
    )
    session2.config.pytest_libiio = types.SimpleNamespace(coverage_tracker=None)
    plugin.pytest_sessionfinish(session2, 0)
    assert "No IIO coverage tracking was set up" in capsys.readouterr().out


def test_iio_uri_single_context_and_context_desc(monkeypatch):
    marker = types.SimpleNamespace(name="iio_hardware", args=("pluto",))
    request = FakeRequest(
        {
            "--iio-coverage": True,
            "--telm": False,
        },
        marker,
    )

    tracker = types.SimpleNamespace(
        trackers={},
        add_instance=lambda n, u: (
            request.config.pytest_libiio.coverage_tracker.trackers.setdefault(
                n, object()
            )
        ),
        set_tracker=lambda n: None,
    )
    request.config.pytest_libiio = types.SimpleNamespace(coverage_tracker=tracker)

    monkeypatch.setattr(plugin, "get_telemetry_data", lambda *args, **kwargs: None)

    fixture_fn = plugin.iio_uri.__wrapped__
    gen = fixture_fn(request, {"hw": "pluto", "uri": "ip:1.2.3.4"})
    assert next(gen) == "ip:1.2.3.4"
    with pytest.raises(StopIteration):
        next(gen)

    gen = plugin.iio_uri.__wrapped__(request, None)
    with pytest.raises(StopIteration) as stop:
        next(gen)
    assert stop.value.value is False

    contexts = [{"hw": "pluto", "uri": "u1"}, {"hw": "ad9081", "uri": "u2"}]
    assert plugin.single_ctx_desc.__wrapped__(request, contexts)["hw"] == "pluto"
    assert plugin.context_desc.__wrapped__(request, contexts) == [
        {"hw": "pluto", "uri": "u1"}
    ]


def test_iio_emu_func_and_emu_fixture(monkeypatch, tmp_path):
    marker_skip = types.SimpleNamespace(name="iio_hardware", args=("pluto", True))
    request = FakeRequest({"--emu": True}, marker_skip)
    with pytest.raises(pytest.skip.Exception):
        plugin._iio_emu_func.__wrapped__(
            request, [{"hw": "pluto", "uri": "u"}], object()
        )

    marker = types.SimpleNamespace(name="iio_hardware", args=("pluto",))
    request = FakeRequest({"--emu": False}, marker)
    monkeypatch.setattr(
        plugin, "handle_iio_emu", lambda dec, request, emu: {**dec, "handled": True}
    )
    out = plugin._iio_emu_func.__wrapped__(
        request, [{"hw": "pluto", "uri": "u"}], object()
    )
    assert out["handled"]

    # _iio_emu fixture: no emu
    request = types.SimpleNamespace(config=FakeConfig({"--emu": False}))
    gen = plugin._iio_emu.__wrapped__(request, "master")
    assert next(gen) is None
    with pytest.raises(StopIteration):
        next(gen)

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
    gen = plugin._iio_emu.__wrapped__(request, "gw2")
    emu = next(gen)
    assert emu.started == 1
    with pytest.raises(StopIteration):
        next(gen)
    assert emu.stopped == 1


def test_contexts_fixture_cleanup_and_telemetry(tmp_path, monkeypatch):
    # _contexts with auto emu
    req = types.SimpleNamespace(
        config=FakeConfig({"--uri": None, "--scan-verbose": False, "--hw": None})
    )
    emu = types.SimpleNamespace(
        auto=True, uri="ip:emu", hw={"pluto": {"devices": ["d0"]}}
    )
    rows = plugin._contexts.__wrapped__(req, emu)
    assert rows[0]["type"] == "emu"

    # _contexts with URI and context attrs
    class Ctx:
        attrs = {"uri": "ip:1.1.1.1"}
        devices = [types.SimpleNamespace(name="dev0")]

    monkeypatch.setattr(plugin.iio, "Context", lambda uri: Ctx())
    monkeypatch.setattr(plugin, "lookup_hw_from_map", lambda ctx, m: "pluto")

    req = types.SimpleNamespace(
        config=FakeConfig({"--uri": "ip:1.1.1.1", "--hw": None, "--scan-verbose": True})
    )
    out = plugin._contexts.__wrapped__(req, None)
    assert out[0]["hw"] == "pluto"

    # timeout path
    def timeout_ctx(uri):
        raise TimeoutError()

    monkeypatch.setattr(plugin.iio, "Context", timeout_ctx)
    with pytest.raises(Exception, match="no reachable context"):
        plugin._contexts.__wrapped__(req, None)

    # cleanup_ssh_sessions fixture
    close_called = {"count": 0}

    class SSH:
        def close(self):
            close_called["count"] += 1

    plugin.pytest.hw_telemetry_ssh_sessions = {"u": SSH(), "n": None}
    gen = plugin.cleanup_ssh_sessions.__wrapped__()
    next(gen)
    with pytest.raises(StopIteration):
        next(gen)
    assert close_called["count"] == 1

    # save telemetry logs fixture
    plugin.pytest.hw_telemetry = {"u": {"test_a": {"k": 1}}}
    req = types.SimpleNamespace(
        config=FakeConfig({"--telm-data-folder": str(tmp_path / "telm")})
    )
    gen = plugin.save_telemtry_logs_to_files.__wrapped__(req)
    next(gen)
    with pytest.raises(StopIteration):
        next(gen)
    assert (tmp_path / "telm" / "test_a.pkl").exists()

    # get_telemetry_data disabled
    request = FakeRequest({"--telm": False})
    assert plugin.get_telemetry_data(request, {"uri": "ip:1.1.1.1"}) is None

    # get_telemetry_data enabled for emu path and before/after writes
    monkeypatch.setattr(plugin.iio, "Context", lambda uri: object())
    monkeypatch.setattr(plugin.meta, "get_hardware_info", lambda ctx, ssh: {"ok": True})

    request = FakeRequest({"--telm": True, "--emu": True}, test_name="test_telem")
    plugin.get_telemetry_data(request, {"uri": "ip:1.1.1.1"}, before_test=True)
    plugin.get_telemetry_data(request, {"uri": "ip:1.1.1.1"}, before_test=False)
    assert plugin.pytest.hw_telemetry["ip:1.1.1.1"]["test_telem"]["before_test"] == {
        "ok": True
    }
    assert plugin.pytest.hw_telemetry["ip:1.1.1.1"]["test_telem"]["after_test"] == {
        "ok": True
    }


def test_import_lookup_and_find_contexts(tmp_path, monkeypatch, capsys):
    hw_map_file = tmp_path / "hw.yml"
    hw_map_file.write_text(
        "pluto:\n  - ad9361-phy,1\n  - ctx_attr:\n    - hw_model: Demo\n"
    )

    data = plugin.import_hw_map(str(hw_map_file))
    assert "pluto" in data

    with pytest.raises(Exception, match="Hardware map file not found"):
        plugin.import_hw_map(str(tmp_path / "missing.yml"))

    dev = types.SimpleNamespace(
        name="ad9361-phy",
        channels=[types.SimpleNamespace(scan_element=True)],
    )
    ctx = types.SimpleNamespace(attrs={"hw_model": "Demo"}, devices=[dev])
    assert plugin.lookup_hw_from_map(ctx, data) == "pluto"
    assert plugin.lookup_hw_from_map(ctx, None) == "Unknown"

    config = FakeConfig({"--scan-verbose": True})
    request = types.SimpleNamespace(config=FakeConfig({"--skip-scan": True}))
    assert plugin.find_contexts(config, data, request) is False

    request = types.SimpleNamespace(config=FakeConfig({"--skip-scan": False}))
    monkeypatch.setattr(
        plugin.iio, "scan_contexts", lambda: {"ip:1.1.1.1": "demo(ad9361-phy)"}
    )

    class Ctx:
        attrs = {"uri": "ip:1.1.1.1"}
        devices = [types.SimpleNamespace(name=None, id="id0", channels=[])]

    monkeypatch.setattr(plugin.iio, "Context", lambda uri: Ctx())
    rows = plugin.find_contexts(config, data, request)
    assert rows[0]["uri"] == "ip:1.1.1.1"

    class BusyError(Exception):
        errno = 16

    monkeypatch.setattr(
        plugin.iio, "Context", lambda uri: (_ for _ in ()).throw(BusyError("busy"))
    )
    rows = plugin.find_contexts(config, data, request)
    assert rows == []
    assert "not reachable" in capsys.readouterr().out

    class FatalError(Exception):
        errno = 1

    monkeypatch.setattr(
        plugin.iio, "Context", lambda uri: (_ for _ in ()).throw(FatalError("fatal"))
    )
    with pytest.raises(FatalError):
        plugin.find_contexts(config, data, request)
