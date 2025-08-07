import logging
from pprint import pprint

import iio
from iio import ChannelAttr as _Attr

logger = logging.getLogger(__name__)

coverage_tracker = None


def _check_tracker():
    """Check if the coverage tracker is set."""
    global coverage_tracker  # noqa: F824
    if coverage_tracker is None:
        raise RuntimeError(
            "Coverage tracker is not set. Call set_coverage_tracker first."
        )


def _read(self):
    """MP Read method to capture attribute reads"""
    attr_name = self.name
    if self._channel:
        name_raw = iio._c_get_id(self._channel)
        channel_name = name_raw.decode("ascii") if name_raw is not None else None
        dev_ptr = iio._channel_get_device(self._channel)
        name_raw = iio._d_get_name(dev_ptr)
        device_name = name_raw.decode("ascii") if name_raw is not None else None
    else:
        channel_name = None
        device_name = self._name

    _check_tracker()

    global coverage_tracker  # noqa: F824
    if channel_name and device_name:
        coverage_tracker.channel_attr_reads_writes[device_name][channel_name][
            attr_name
        ] += 1
    elif device_name:
        coverage_tracker.device_attr_reads_writes[device_name][attr_name] += 1
    else:
        coverage_tracker.context_attr_reads_writes[attr_name] += 1

    logger.debug(
        f"Reading attribute: {attr_name}, Channel: {channel_name}, Device: {device_name}"
    )
    return self._read_org()


def _write(self, value):
    """MP Write method to capture attribute writes"""
    attr_name = self.name
    if self._channel:
        name_raw = iio._c_get_id(self._channel)
        channel_name = name_raw.decode("ascii") if name_raw is not None else None
        dev_ptr = iio._channel_get_device(self._channel)
        name_raw = iio._d_get_name(dev_ptr)
        device_name = name_raw.decode("ascii") if name_raw is not None else None
    else:
        channel_name = None
        device_name = self._name

    _check_tracker()

    global coverage_tracker  # noqa: F824
    if channel_name and device_name:
        coverage_tracker.channel_attr_reads_writes[device_name][channel_name][
            attr_name
        ] += 1
    elif device_name:
        coverage_tracker.device_attr_reads_writes[device_name][attr_name] += 1
    else:
        coverage_tracker.context_attr_reads_writes[attr_name] += 1

    logger.debug(
        f"Writing attribute: {attr_name}, Channel: {channel_name}, Device: {device_name}, Value: {value}"
    )
    self._write_org(value)


_Attr._read_org = _Attr._read
_Attr._read = _read

_Attr._write_org = _Attr._write
_Attr._write = _write


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

    _Attr._read = _Attr._read_org
    _Attr._write = _Attr._write_org


logger.debug("iio.py monkey patch applied")
