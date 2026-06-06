import types

import pytest

import pytest_libiio.mkpatch as mkpatch


class DummyAttr:
    def __init__(self, name, channel, device):
        self.name = name
        self._channel = channel
        self._device = device
        self.read_called = 0
        self.writes = []


class DummyTracker:
    def __init__(self):
        self.channel_attr_reads_writes = {"dev": {"input": {"chan": {"attr": 0}}}}
        self.device_attr_reads_writes = {"dev": {"attr": 0}}
        self.context_attr_reads_writes = {"attr": 0}


def test_get_tracker_raises_when_unset(monkeypatch):
    monkeypatch.setattr(mkpatch, "coverage_tracker", None)
    with pytest.raises(RuntimeError, match="Coverage tracker is not set"):
        mkpatch._get_tracker()


def test_read_and_write_track_channel_attributes(monkeypatch):
    tracker = DummyTracker()
    mkpatch.set_coverage_tracker(tracker)

    monkeypatch.setattr(mkpatch.iio, "_c_get_id", lambda ch: b"chan")
    monkeypatch.setattr(mkpatch.iio, "_c_is_output", lambda ch: False)
    monkeypatch.setattr(mkpatch.iio, "_channel_get_device", lambda ch: object())
    monkeypatch.setattr(mkpatch.iio, "_d_get_name", lambda dev: b"dev")

    def fake_read(self):
        self.read_called += 1
        return "orig-read"

    def fake_write(self, value):
        self.writes.append(value)

    monkeypatch.setattr(mkpatch, "_orig_chan_read", fake_read)
    monkeypatch.setattr(mkpatch, "_orig_chan_write", fake_write)

    attr = DummyAttr("attr", object(), None)

    assert mkpatch._read(attr) == "orig-read"
    mkpatch._write(attr, "v")

    assert tracker.channel_attr_reads_writes["dev"]["input"]["chan"]["attr"] == 2
    assert attr.writes == ["v"]


def test_read_and_write_track_device_and_context(monkeypatch):
    tracker = DummyTracker()
    mkpatch.set_coverage_tracker(tracker)

    monkeypatch.setattr(mkpatch, "_d_get_name", lambda dev: b"dev" if dev else None)
    monkeypatch.setattr(mkpatch, "_orig_dev_read", lambda self: None)
    monkeypatch.setattr(mkpatch, "_orig_dev_write", lambda self, value: None)

    attr_dev = DummyAttr("attr", None, object())
    mkpatch._read(attr_dev)
    mkpatch._write(attr_dev, "x")
    assert tracker.device_attr_reads_writes["dev"]["attr"] == 2

    # Context-level attributes are tracked but not yet supported for I/O, so
    # the read/write helpers raise after recording the access.
    attr_ctx = DummyAttr("attr", None, None)
    with pytest.raises(ValueError, match="Context properties not supported"):
        mkpatch._read(attr_ctx)
    with pytest.raises(ValueError, match="Context properties not supported"):
        mkpatch._write(attr_ctx, "x")
    assert tracker.context_attr_reads_writes["attr"] == 2


def test_unset_monkey_patch_restores_attr_methods(monkeypatch):
    dummy_chan = types.SimpleNamespace(_read="patched_read", _write="patched_write")
    dummy_dev = types.SimpleNamespace(_read="patched_read", _write="patched_write")

    monkeypatch.setattr(mkpatch, "_CAttr", dummy_chan)
    monkeypatch.setattr(mkpatch, "_DAttr", dummy_dev)
    monkeypatch.setattr(mkpatch, "_orig_chan_read", "orig_chan_read")
    monkeypatch.setattr(mkpatch, "_orig_chan_write", "orig_chan_write")
    monkeypatch.setattr(mkpatch, "_orig_dev_read", "orig_dev_read")
    monkeypatch.setattr(mkpatch, "_orig_dev_write", "orig_dev_write")
    mkpatch.set_coverage_tracker(DummyTracker())

    mkpatch.unset_monkey_patch()

    assert mkpatch.coverage_tracker is None
    assert dummy_chan._read == "orig_chan_read"
    assert dummy_chan._write == "orig_chan_write"
    assert dummy_dev._read == "orig_dev_read"
    assert dummy_dev._write == "orig_dev_write"


def test_reset_coverage_tracker():
    mkpatch.set_coverage_tracker(DummyTracker())
    mkpatch.reset_coverage_tracker()
    assert mkpatch.coverage_tracker is None
