import logging
from pprint import pprint

import iio
from iio import ChannelAttr as _Attr

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
    if self._channel:
        name_raw = iio._c_get_id(self._channel)
        channel_name = name_raw.decode("ascii") if name_raw is not None else None
        output = iio._c_is_output(self._channel)
        dev_ptr = iio._channel_get_device(self._channel)
        name_raw = iio._d_get_name(dev_ptr)
        device_name = name_raw.decode("ascii") if name_raw is not None else None
    else:
        channel_name = None
        device_name = self._name

    tracker = _get_tracker()
    if channel_name and device_name:
        inout = "output" if output else "input"
        tracker.channel_attr_reads_writes[device_name][inout][channel_name][
            attr_name
        ] += 1
    elif device_name:
        tracker.device_attr_reads_writes[device_name][attr_name] += 1
    else:
        tracker.context_attr_reads_writes[attr_name] += 1

    logger.debug(
        f"Reading attribute: {attr_name}, Channel: {channel_name}, Device: {device_name}"
    )
    return _orig_read(self)


def _write(self, value):
    """MP Write method to capture attribute writes"""
    attr_name = self.name
    if self._channel:
        name_raw = iio._c_get_id(self._channel)
        channel_name = name_raw.decode("ascii") if name_raw is not None else None
        output = iio._c_is_output(self._channel)
        dev_ptr = iio._channel_get_device(self._channel)
        name_raw = iio._d_get_name(dev_ptr)
        device_name = name_raw.decode("ascii") if name_raw is not None else None
    else:
        channel_name = None
        device_name = self._name

    tracker = _get_tracker()
    if channel_name and device_name:
        inout = "output" if output else "input"
        tracker.channel_attr_reads_writes[device_name][inout][channel_name][
            attr_name
        ] += 1
    elif device_name:
        tracker.device_attr_reads_writes[device_name][attr_name] += 1
    else:
        tracker.context_attr_reads_writes[attr_name] += 1

    logger.debug(
        f"Writing attribute: {attr_name}, Channel: {channel_name}, Device: {device_name}, Value: {value}"
    )
    _orig_write(self, value)


_orig_read = _Attr._read
_orig_write = _Attr._write
# Monkey-patch ChannelAttr to capture reads/writes; setattr is intentional
# to make the dynamic patching explicit to type checkers.
setattr(_Attr, "_read", _read)  # noqa: B010
setattr(_Attr, "_write", _write)  # noqa: B010


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

    setattr(_Attr, "_read", _orig_read)  # noqa: B010
    setattr(_Attr, "_write", _orig_write)  # noqa: B010


logger.debug("iio.py monkey patch applied")
