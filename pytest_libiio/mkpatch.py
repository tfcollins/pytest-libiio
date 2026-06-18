import logging
from pprint import pprint

import iio
from iio import ChannelAttr as _CAttr
from iio import Context as _CtxAttr
from iio import DeviceAttr as _DAttr
from iio import _d_get_id, _d_get_name

logger = logging.getLogger(__name__)

coverage_tracker = None


def _get_tracker():
    """Return the active coverage tracker, raising if not set."""
    if coverage_tracker is None:
        raise RuntimeError(
            "Coverage tracker is not set. Call set_coverage_tracker first."
        )
    return coverage_tracker


def _read(self):
    """MP Read method to capture attribute reads"""
    attr_name = self.name
    if hasattr(self, "_channel") and self._channel:
        name_raw = iio._c_get_id(self._channel)
        channel_name = name_raw.decode("ascii") if name_raw is not None else None
        output = iio._c_is_output(self._channel)
        dev_ptr = iio._channel_get_device(self._channel)
        name_raw = iio._d_get_name(dev_ptr)
        device_name = name_raw.decode("ascii") if name_raw is not None else None
    else:
        channel_name = None
        name_raw = _d_get_name(self._device)
        device_name = name_raw.decode("ascii") if name_raw is not None else None

    tracker = _get_tracker()
    ig = getattr(tracker, "ignore", None)
    if channel_name and device_name:
        inout = "output" if output else "input"
        if not (ig and ig.attr_ignored(device_name, channel_name, attr_name, inout)):
            tracker.channel_attr_reads_writes[device_name][inout][channel_name][
                attr_name
            ] += 1
    elif device_name:
        if not (ig and ig.attr_ignored(device_name, None, attr_name, None)):
            tracker.device_attr_reads_writes[device_name][attr_name] += 1
    else:
        tracker.context_attr_reads_writes[attr_name] += 1

    logger.debug(
        f"Reading attribute: {attr_name}, Channel: {channel_name}, Device: {device_name}"
    )
    if channel_name and device_name:
        return _orig_chan_read(self)
    elif device_name:
        return _orig_dev_read(self)
    else:
        raise ValueError("Context properties not supported yet")


def _write(self, value):
    """MP Write method to capture attribute writes"""
    attr_name = self.name
    if hasattr(self, "_channel") and self._channel:
        name_raw = iio._c_get_id(self._channel)
        channel_name = name_raw.decode("ascii") if name_raw is not None else None
        output = iio._c_is_output(self._channel)
        dev_ptr = iio._channel_get_device(self._channel)
        name_raw = iio._d_get_name(dev_ptr)
        device_name = name_raw.decode("ascii") if name_raw is not None else None
    else:
        channel_name = None
        name_raw = _d_get_name(self._device)
        device_name = name_raw.decode("ascii") if name_raw is not None else None

    tracker = _get_tracker()
    ig = getattr(tracker, "ignore", None)
    if channel_name and device_name:
        inout = "output" if output else "input"
        if not (ig and ig.attr_ignored(device_name, channel_name, attr_name, inout)):
            tracker.channel_attr_reads_writes[device_name][inout][channel_name][
                attr_name
            ] += 1
    elif device_name:
        if not (ig and ig.attr_ignored(device_name, None, attr_name, None)):
            tracker.device_attr_reads_writes[device_name][attr_name] += 1
    else:
        tracker.context_attr_reads_writes[attr_name] += 1

    logger.debug(
        f"Writing attribute: {attr_name}, Channel: {channel_name}, Device: {device_name}, Value: {value}"
    )
    if channel_name and device_name:
        _orig_chan_write(self, value)
    elif device_name:
        _orig_dev_write(self, value)
    else:
        raise ValueError("Context properties not supported yet")


_orig_chan_read = _CAttr._read
_orig_chan_write = _CAttr._write
_orig_dev_read = _DAttr._read
_orig_dev_write = _DAttr._write
# _orig_ctx_read = _CtxAttr._read
# _orig_ctx_write = _CtxAttr._write

# Monkey-patch ChannelAttr to capture reads/writes; setattr is intentional
# to make the dynamic patching explicit to type checkers.
setattr(_CAttr, "_read", _read)  # noqa: B010
setattr(_CAttr, "_write", _write)  # noqa: B010
setattr(_DAttr, "_read", _read)  # noqa: B010
setattr(_DAttr, "_write", _write)  # noqa: B010
# setattr(_CtxAttr, "_read", _read)  # noqa: B010
# setattr(_CtxAttr, "_write", _write)  # noqa: B010


def set_coverage_tracker(tracker):
    """Set up the coverage tracker for iio attributes."""
    global coverage_tracker

    coverage_tracker = tracker


def reset_coverage_tracker():
    """Reset the coverage tracker."""
    global coverage_tracker
    coverage_tracker = None


def unset_monkey_patch():
    """Unset the monkey patch for iio attributes."""
    global coverage_tracker
    if coverage_tracker:
        coverage_tracker = None

    setattr(_CAttr, "_read", _orig_chan_read)  # noqa: B010
    setattr(_CAttr, "_write", _orig_chan_write)  # noqa: B010
    setattr(_DAttr, "_read", _orig_dev_read)  # noqa: B010
    setattr(_DAttr, "_write", _orig_dev_write)  # noqa: B010
    # setattr(_CtxAttr, "_read", _orig_ctx_read)  # noqa: B010
    # setattr(_CtxAttr, "_write", _orig_ctx_write)  # noqa: B010


logger.debug("iio.py monkey patch applied")
