import json

import pytest

from pytest_libiio import coverage


class V:
    def __init__(self, value):
        self.value = value


class FakeChannel:
    def __init__(self, cid, output, attrs):
        self.id = cid
        self.output = output
        self.attrs = attrs


class FakeDevice:
    def __init__(self, name, attrs, channels, debug_attrs=None):
        self.name = name
        self.attrs = attrs
        self.channels = channels
        self.debug_attrs = debug_attrs or {}


class FakeContext:
    def __init__(self):
        self.attrs = {"uri": V("ip:127.0.0.1"), "hw_model": V("Demo")}
        self.devices = [
            FakeDevice(
                "dev0",
                {"dev_a": V("1"), "dev_b": V("2")},
                [
                    FakeChannel("ch_in", False, {"ch_a": V("1")}),
                    FakeChannel("ch_out", True, {"ch_b": V("2"), "ch_c": V("3")}),
                ],
                debug_attrs={"dbg": V("1")},
            )
        ]


def test_multi_context_tracker_add_set_and_duplicate(monkeypatch):
    monkeypatch.setattr("pytest_libiio.coverage.iio.Context", lambda uri: FakeContext())

    mct = coverage.MultiContextTracker()
    mct.track_context_props = True
    mct.track_debug_props = True
    mct.add_instance("dut", "ip:1.2.3.4")

    captured = {}

    def fake_set_tracker(tracker):
        captured["tracker"] = tracker

    monkeypatch.setattr("pytest_libiio.mkpatch.set_coverage_tracker", fake_set_tracker)

    mct.set_tracker("dut")
    assert captured["tracker"] is mct.trackers["dut"]

    with pytest.raises(Exception, match="already in tracker list"):
        mct.add_instance("dut", "ip:1.2.3.4")

    with pytest.raises(ValueError, match="missing not tracked"):
        mct.set_tracker("missing")


def test_multi_context_tracker_do_monkey_patch_calls_reset(monkeypatch):
    called = {"reset": 0}

    def fake_reset():
        called["reset"] += 1

    monkeypatch.setattr("pytest_libiio.mkpatch.reset_coverage_tracker", fake_reset)

    coverage.MultiContextTracker().do_monkey_patch()
    assert called["reset"] == 1


def test_coverage_tracker_export_print_and_calculate(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("pytest_libiio.coverage.iio.Context", lambda uri: FakeContext())

    tracker = coverage.CoverageTracker(
        "dut",
        "ip:127.0.0.1",
        track_context_props=True,
        track_debug_props=True,
        results_folder=str(tmp_path / "cov"),
    )

    tracker.context_attr_reads_writes["uri"] = 1
    tracker.device_attr_reads_writes["dev0"]["dev_a"] = 1
    tracker.channel_attr_reads_writes["dev0"]["input"]["ch_in"]["ch_a"] = 1
    tracker.debug_attr_reads_writes["dev0"]["dbg"] = 1

    exported = tracker.export()
    assert "context_attr_reads_writes" in exported
    assert "debug_attr_reads_writes" in exported

    tracker.print_context_map()
    output = capsys.readouterr().out
    assert "Context Attribute Reads:" in output
    assert "Debug Attribute Reads:" in output

    out = tracker.calculate_coverage()
    assert out["device_coverage"] > 0
    assert out["channel_coverage"] > 0
    assert out["debug_coverage"] > 0
    assert out["context_coverage"] > 0

    tracker.export_to_file()
    out_file = tmp_path / "cov" / "dut_coverage.json"
    assert out_file.exists()
    payload = json.loads(out_file.read_text())
    assert "device_attr_reads_writes" in payload


def test_coverage_tracker_reset_and_zero_attribute_paths(monkeypatch):
    class EmptyContext:
        attrs = {}
        devices = [FakeDevice("dev", {}, [])]

    monkeypatch.setattr("pytest_libiio.coverage.iio.Context", lambda uri: EmptyContext())

    tracker = coverage.CoverageTracker("dut", "ip:1.2.3.4")
    with pytest.raises(ZeroDivisionError):
        tracker.calculate_coverage()

    tracker.device_attr_reads_writes["dev"]["x"] = 1
    tracker.reset()
    assert tracker.device_attr_reads_writes == {}
    assert tracker.channel_attr_reads_writes == {}
