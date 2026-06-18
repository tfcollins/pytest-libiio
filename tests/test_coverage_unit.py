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


def test_blacklist_empty_spec_matches_nothing():
    bl = coverage.Blacklist(None)
    assert not bl.device_blacklisted("dev0")
    assert not bl.channel_blacklisted("dev0", "voltage0", "input")
    assert not bl.attr_blacklisted("dev0", None, "dev_a", None)
    assert not bl.attr_blacklisted("dev0", "voltage0", "scale", "input")

    bl = coverage.Blacklist({})
    assert not bl.device_blacklisted("dev0")


def test_blacklist_device_exact_and_glob():
    bl = coverage.Blacklist({"devices": ["xadc", "cf-*"]})
    assert bl.device_blacklisted("xadc")
    assert bl.device_blacklisted("cf-ad9361-lpc")
    assert not bl.device_blacklisted("ad9361-phy")
    # A blacklisted device cascades to its attrs and channels.
    assert bl.attr_blacklisted("xadc", None, "in_temp0_input", None)
    assert bl.attr_blacklisted("cf-ad9361-lpc", "voltage0", "scale", "input")
    assert bl.channel_blacklisted("cf-ad9361-lpc", "voltage0", "input")


def test_blacklist_channel_with_and_without_direction():
    bl = coverage.Blacklist(
        {
            "channels": [
                {"device": "ad9361-phy", "id": "voltage0"},
                {"device": "ad9361-phy", "id": "voltage*", "direction": "output"},
            ]
        }
    )
    # No direction in spec -> matches either direction.
    assert bl.channel_blacklisted("ad9361-phy", "voltage0", "input")
    assert bl.channel_blacklisted("ad9361-phy", "voltage0", "output")
    # Direction-qualified glob entry.
    assert bl.channel_blacklisted("ad9361-phy", "voltage1", "output")
    assert not bl.channel_blacklisted("ad9361-phy", "voltage1", "input")
    # Wrong device.
    assert not bl.channel_blacklisted("cf-ad9361-lpc", "voltage0", "input")
    # A blacklisted channel cascades to its attrs.
    assert bl.attr_blacklisted("ad9361-phy", "voltage0", "scale", "input")


def test_blacklist_device_level_attribute():
    bl = coverage.Blacklist(
        {"attributes": [{"device": "ad9361-phy", "name": "in_temp0_input"}]}
    )
    assert bl.attr_blacklisted("ad9361-phy", None, "in_temp0_input", None)
    assert not bl.attr_blacklisted("ad9361-phy", None, "frequency", None)
    # A device-level attribute entry (no channel) must not match a channel attr.
    assert not bl.attr_blacklisted("ad9361-phy", "voltage0", "in_temp0_input", "input")


def test_blacklist_channel_attribute_with_direction():
    bl = coverage.Blacklist(
        {
            "attributes": [
                {
                    "device": "ad9361-phy",
                    "channel": "voltage0",
                    "name": "hardwaregain",
                    "direction": "output",
                }
            ]
        }
    )
    assert bl.attr_blacklisted("ad9361-phy", "voltage0", "hardwaregain", "output")
    # Wrong direction.
    assert not bl.attr_blacklisted("ad9361-phy", "voltage0", "hardwaregain", "input")
    # A channel-attr entry (has channel) must not match a device-level attr.
    assert not bl.attr_blacklisted("ad9361-phy", None, "hardwaregain", None)


def test_blacklist_attribute_globs_everywhere():
    bl = coverage.Blacklist(
        {"attributes": [{"device": "*", "channel": "*", "name": "raw"}]}
    )
    assert bl.attr_blacklisted("ad9361-phy", "voltage0", "raw", "input")
    assert bl.attr_blacklisted("cf-ad9361-lpc", "voltage7", "raw", "output")
    assert not bl.attr_blacklisted("ad9361-phy", "voltage0", "scale", "input")


def test_build_context_map_excludes_blacklisted(monkeypatch):
    monkeypatch.setattr("pytest_libiio.coverage.iio.Context", lambda uri: FakeContext())
    spec = {
        "attributes": [
            {"device": "dev0", "name": "dev_a"},
            {"device": "dev0", "channel": "ch_out", "name": "ch_b"},
        ],
        "channels": [{"device": "dev0", "id": "ch_in"}],
    }
    tracker = coverage.CoverageTracker("dut", "ip:1.2.3.4", blacklist=spec)

    # Device-level attr dev_a removed, dev_b kept.
    assert "dev_a" not in tracker.device_attr_reads_writes["dev0"]
    assert "dev_b" in tracker.device_attr_reads_writes["dev0"]
    # Whole input channel removed.
    assert "ch_in" not in tracker.channel_attr_reads_writes["dev0"].get("input", {})
    # Output channel kept, but ch_b attr removed and ch_c kept.
    chout = tracker.channel_attr_reads_writes["dev0"]["output"]["ch_out"]
    assert "ch_b" not in chout
    assert "ch_c" in chout


def test_build_context_map_excludes_whole_device(monkeypatch):
    monkeypatch.setattr("pytest_libiio.coverage.iio.Context", lambda uri: FakeContext())
    tracker = coverage.CoverageTracker(
        "dut",
        "ip:1.2.3.4",
        track_debug_props=True,
        blacklist={"devices": ["dev0"]},
    )
    assert tracker.device_attr_reads_writes == {}
    assert tracker.channel_attr_reads_writes == {}
    assert tracker.debug_attr_reads_writes == {}


def test_multi_context_tracker_passes_per_hw_blacklist(monkeypatch):
    monkeypatch.setattr("pytest_libiio.coverage.iio.Context", lambda uri: FakeContext())
    mct = coverage.MultiContextTracker()
    mct.blacklists = {"dut": {"devices": ["dev0"]}}

    mct.add_instance("dut", "ip:1.2.3.4")
    assert mct.trackers["dut"].device_attr_reads_writes == {}

    # A hardware name with no blacklist entry is tracked normally.
    mct.add_instance("other", "ip:5.6.7.8")
    assert mct.trackers["other"].device_attr_reads_writes != {}


def test_mkpatch_skips_blacklisted_device_attr(monkeypatch):
    from pytest_libiio import mkpatch

    monkeypatch.setattr("pytest_libiio.coverage.iio.Context", lambda uri: FakeContext())
    tracker = coverage.CoverageTracker(
        "dut",
        "ip:1.2.3.4",
        blacklist={"attributes": [{"device": "dev0", "name": "dev_a"}]},
    )
    mkpatch.set_coverage_tracker(tracker)
    try:
        monkeypatch.setattr(mkpatch, "_d_get_name", lambda dev: b"dev0")
        reads = []
        monkeypatch.setattr(
            mkpatch, "_orig_dev_read", lambda self: reads.append(self.name) or "val"
        )

        class Attr:
            def __init__(self, name):
                self.name = name
                self._device = object()

        # Blacklisted attr: original still runs, but no count is recorded and
        # the (absent) key is never indexed -> no KeyError.
        out = mkpatch._read(Attr("dev_a"))
        assert out == "val"
        assert "dev_a" not in tracker.device_attr_reads_writes["dev0"]

        # Non-blacklisted attr still increments.
        mkpatch._read(Attr("dev_b"))
        assert tracker.device_attr_reads_writes["dev0"]["dev_b"] == 1
    finally:
        mkpatch.reset_coverage_tracker()


def test_mkpatch_skips_blacklisted_channel_attr(monkeypatch):
    from pytest_libiio import mkpatch

    monkeypatch.setattr("pytest_libiio.coverage.iio.Context", lambda uri: FakeContext())
    tracker = coverage.CoverageTracker(
        "dut",
        "ip:1.2.3.4",
        blacklist={
            "attributes": [{"device": "dev0", "channel": "ch_out", "name": "ch_b"}]
        },
    )
    mkpatch.set_coverage_tracker(tracker)
    try:
        monkeypatch.setattr(mkpatch.iio, "_c_get_id", lambda ch: b"ch_out")
        monkeypatch.setattr(mkpatch.iio, "_c_is_output", lambda ch: True)
        monkeypatch.setattr(mkpatch.iio, "_channel_get_device", lambda ch: object())
        monkeypatch.setattr(mkpatch.iio, "_d_get_name", lambda dev: b"dev0")
        writes = []
        monkeypatch.setattr(
            mkpatch, "_orig_chan_write", lambda self, value: writes.append(value)
        )

        class Attr:
            def __init__(self, name):
                self.name = name
                self._channel = object()

        # Blacklisted channel attr: original still runs, no count, no KeyError.
        mkpatch._write(Attr("ch_b"), "5")
        assert writes == ["5"]
        assert (
            "ch_b" not in tracker.channel_attr_reads_writes["dev0"]["output"]["ch_out"]
        )

        # Non-blacklisted channel attr still increments.
        mkpatch._write(Attr("ch_c"), "6")
        assert (
            tracker.channel_attr_reads_writes["dev0"]["output"]["ch_out"]["ch_c"] == 1
        )
    finally:
        mkpatch.reset_coverage_tracker()


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

    monkeypatch.setattr(
        "pytest_libiio.coverage.iio.Context", lambda uri: EmptyContext()
    )

    tracker = coverage.CoverageTracker("dut", "ip:1.2.3.4")
    with pytest.raises(ZeroDivisionError):
        tracker.calculate_coverage()

    tracker.device_attr_reads_writes["dev"]["x"] = 1
    tracker.reset()
    assert tracker.device_attr_reads_writes == {}
    assert tracker.channel_attr_reads_writes == {}
