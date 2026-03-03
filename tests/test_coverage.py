import importlib
import json
import sys
import types

import pytest


@pytest.fixture
def fake_iio(monkeypatch):
    class FakeAttr:
        def __init__(self, value):
            self.value = value

    class FakeChannel:
        def __init__(self, channel_id, output, attrs):
            self.id = channel_id
            self.output = output
            self.attrs = {k: FakeAttr(v) for k, v in attrs.items()}

    class FakeDevice:
        def __init__(self, name, attrs, channels, debug_attrs):
            self.name = name
            self.attrs = {k: FakeAttr(v) for k, v in attrs.items()}
            self.channels = channels
            self.debug_attrs = {k: FakeAttr(v) for k, v in debug_attrs.items()}

    class FakeContext:
        def __init__(self, uri):
            self.uri = uri
            self.attrs = {"uri": FakeAttr(uri), "hw": FakeAttr("mock")}
            self.devices = [
                FakeDevice(
                    name="dev0",
                    attrs={"dev_attr": "1"},
                    channels=[
                        FakeChannel("ch_in", False, {"in_attr": "2"}),
                        FakeChannel("ch_out", True, {"out_attr": "3"}),
                    ],
                    debug_attrs={"dbg_attr": "4"},
                )
            ]

    module = types.ModuleType("iio")
    module.Context = FakeContext
    monkeypatch.setitem(sys.modules, "iio", module)
    return module


def import_coverage_module(monkeypatch, fake_iio):
    monkeypatch.setitem(sys.modules, "iio", fake_iio)
    sys.modules.pop("pytest_libiio.coverage", None)
    return importlib.import_module("pytest_libiio.coverage")


def test_multicontext_add_instance_set_tracker_and_duplicate(monkeypatch, mocker, fake_iio):
    fake_mkpatch = types.ModuleType("pytest_libiio.mkpatch")
    fake_mkpatch.reset_coverage_tracker = lambda: None
    fake_mkpatch.set_coverage_tracker = lambda tracker=None: None
    monkeypatch.setitem(sys.modules, "pytest_libiio.mkpatch", fake_mkpatch)

    coverage = import_coverage_module(monkeypatch, fake_iio)
    mkpatch = sys.modules["pytest_libiio.mkpatch"]

    reset_mock = mocker.patch.object(mkpatch, "reset_coverage_tracker")
    set_mock = mocker.patch.object(mkpatch, "set_coverage_tracker")

    tracker = coverage.MultiContextTracker()
    tracker.track_context_props = True
    tracker.track_debug_props = True

    tracker.do_monkey_patch()
    reset_mock.assert_called_once_with()

    tracker.add_instance("ctx0", "ip:1.2.3.4")
    assert "ctx0" in tracker.trackers

    with pytest.raises(Exception, match="already in tracker list"):
        tracker.add_instance("ctx0", "ip:1.2.3.4")

    tracker.set_tracker("ctx0")
    set_mock.assert_called_once()

    with pytest.raises(ValueError, match="not tracked"):
        tracker.set_tracker("missing")


def test_coverage_tracker_build_reset_export(monkeypatch, fake_iio):
    coverage = import_coverage_module(monkeypatch, fake_iio)

    tracker = coverage.CoverageTracker(
        "ctx0", "ip:1.2.3.4", track_context_props=True, track_debug_props=True
    )

    assert set(tracker.context_attr_reads_writes) == {"uri", "hw"}
    assert tracker.device_attr_reads_writes["dev0"] == {"dev_attr": 0}
    assert tracker.channel_attr_reads_writes["dev0"]["input"]["ch_in"] == {"in_attr": 0}
    assert tracker.channel_attr_reads_writes["dev0"]["output"]["ch_out"] == {
        "out_attr": 0
    }
    assert tracker.debug_attr_reads_writes["dev0"] == {"dbg_attr": 0}

    exported = tracker.export()
    assert "context_attr_reads_writes" in exported
    assert "debug_attr_reads_writes" in exported

    tracker.reset()
    assert tracker.context_attr_reads_writes == {}
    assert tracker.device_attr_reads_writes == {}
    assert tracker.channel_attr_reads_writes == {}
    assert tracker.debug_attr_reads_writes == {}


def test_export_to_file_and_print_context_map(tmp_path, monkeypatch, capsys, fake_iio):
    coverage = import_coverage_module(monkeypatch, fake_iio)

    tracker = coverage.CoverageTracker(
        "ctx0",
        "ip:1.2.3.4",
        track_context_props=True,
        track_debug_props=True,
        results_folder=str(tmp_path / "cov"),
    )

    tracker.export_to_file("out.json")
    out_file = tmp_path / "cov" / "out.json"
    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert "device_attr_reads_writes" in data

    tracker.export_to_file()
    assert (tmp_path / "cov" / "ctx0_coverage.json").exists()

    tracker.print_context_map()
    std = capsys.readouterr().out
    assert "Context Attribute Reads" in std
    assert "Device Attribute Reads" in std
    assert "Channel Attribute Reads" in std
    assert "Debug Attribute Reads" in std


def test_calculate_coverage_without_optional_tracking(monkeypatch, fake_iio):
    coverage = import_coverage_module(monkeypatch, fake_iio)

    tracker = coverage.CoverageTracker("ctx0", "ip:1.2.3.4")
    tracker.device_attr_reads_writes = {"dev0": {"dev_attr": 2}}
    tracker.channel_attr_reads_writes = {"dev0": {"input": {"ch_in": {"in_attr": 1}}}}

    result = tracker.calculate_coverage()

    assert result["device_coverage"] == 2
    assert result["channel_coverage"] == 1
    assert result["total_device_reads_writes"] == 2
    assert result["total_channel_reads_writes"] == 1
    assert result["total_device_attributes"] == 1
    assert result["total_channel_attributes"] == 1
    assert result["total_coverage"] == 1.5


def test_calculate_coverage_with_context_and_debug(monkeypatch, fake_iio):
    coverage = import_coverage_module(monkeypatch, fake_iio)

    tracker = coverage.CoverageTracker(
        "ctx0", "ip:1.2.3.4", track_context_props=True, track_debug_props=True
    )
    tracker.context_attr_reads_writes = {"uri": 1, "hw": 1}
    tracker.device_attr_reads_writes = {"dev0": {"dev_attr": 2}}
    tracker.channel_attr_reads_writes = {"dev0": {"output": {"ch_out": {"out_attr": 3}}}}
    tracker.debug_attr_reads_writes = {"dev0": {"dbg_attr": 4}}

    result = tracker.calculate_coverage()

    assert result["context_coverage"] == 1
    assert result["debug_coverage"] == 4
    assert result["total_context_reads_writes"] == (2,)
    assert result["total_context_attributes"] == (2,)
    assert result["total_debug_reads_writes"] == 4
    assert result["total_debug_attributes"] == 1
