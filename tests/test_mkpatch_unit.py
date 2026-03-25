import types

import pytest

import pytest_libiio.mkpatch as mkpatch


class DummyAttr:
    def __init__(self, name, channel, dev_name):
        self.name = name
        self._channel = channel
        self._name = dev_name
        self.read_called = 0
        self.writes = []

    def _read_org(self):
        self.read_called += 1
        return "orig-read"

    def _write_org(self, value):
        self.writes.append(value)


class DummyTracker:
    def __init__(self):
        self.channel_attr_reads_writes = {"dev": {"input": {"chan": {"attr": 0}}}}
        self.device_attr_reads_writes = {"dev": {"attr": 0}}
        self.context_attr_reads_writes = {"attr": 0}


def test_check_tracker_raises_when_unset(monkeypatch):
    monkeypatch.setattr(mkpatch, "coverage_tracker", None)
    with pytest.raises(RuntimeError, match="Coverage tracker is not set"):
        mkpatch._check_tracker()


def test_read_and_write_track_channel_attributes(monkeypatch):
    tracker = DummyTracker()
    mkpatch.set_coverage_tracker(tracker)

    monkeypatch.setattr(mkpatch.iio, "_c_get_id", lambda ch: b"chan")
    monkeypatch.setattr(mkpatch.iio, "_c_is_output", lambda ch: False)
    monkeypatch.setattr(mkpatch.iio, "_channel_get_device", lambda ch: object())
    monkeypatch.setattr(mkpatch.iio, "_d_get_name", lambda dev: b"dev")

    attr = DummyAttr("attr", object(), "ignored")

    assert mkpatch._read(attr) == "orig-read"
    mkpatch._write(attr, "v")

    assert tracker.channel_attr_reads_writes["dev"]["input"]["chan"]["attr"] == 2
    assert attr.writes == ["v"]


def test_read_and_write_track_device_and_context(monkeypatch):
    tracker = DummyTracker()
    mkpatch.set_coverage_tracker(tracker)

    attr_dev = DummyAttr("attr", None, "dev")
    mkpatch._read(attr_dev)
    mkpatch._write(attr_dev, "x")
    assert tracker.device_attr_reads_writes["dev"]["attr"] == 2

    attr_ctx = DummyAttr("attr", None, None)
    mkpatch._read(attr_ctx)
    mkpatch._write(attr_ctx, "x")
    assert tracker.context_attr_reads_writes["attr"] == 2


def test_unset_monkey_patch_restores_attr_methods(monkeypatch):
    dummy_type = types.SimpleNamespace(_read="patched_read", _write="patched_write")
    dummy_type._read_org = "orig_read"
    dummy_type._write_org = "orig_write"

    monkeypatch.setattr(mkpatch, "_Attr", dummy_type)
    mkpatch.set_coverage_tracker(DummyTracker())

    mkpatch.unset_monkey_patch()

    assert mkpatch.coverage_tracker is None
    assert mkpatch._Attr._read == "orig_read"
    assert mkpatch._Attr._write == "orig_write"


def test_reset_coverage_tracker():
    mkpatch.set_coverage_tracker(DummyTracker())
    mkpatch.reset_coverage_tracker()
    assert mkpatch.coverage_tracker is None
