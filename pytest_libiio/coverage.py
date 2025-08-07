"""Coverage tracking for iio attributes using monkey patching."""

import json
import os
from pprint import pprint

import iio


class MultiContextTracker:
    """Class to track coverage across multiple DUTs."""

    def __init__(self):
        self.trackers = {}
        self.track_debug_props = False
        self.results_folder = "iio_coverage_results"

    def do_monkey_patch(self):
        """Apply monkey patch to iio.py."""
        from . import mkpatch
        from .mkpatch import reset_coverage_tracker

        reset_coverage_tracker()

    def add_instance(self, name, uri):
        """Add a new context to track.

        Args:
            name (str): Name of the context. Just a label, not used in iio.
            uri (str): URI of the context.
        """
        if uri not in self.trackers:
            self.trackers[name] = CoverageTracker(name, uri, self.track_debug_props)

    def set_tracker(self, name):
        from .mkpatch import set_coverage_tracker

        if name not in self.trackers:
            raise ValueError(f"{name} not tracked.")

        set_coverage_tracker(tracker=self.trackers[name])


class CoverageTracker:
    """Class to track coverage of iio attributes."""

    def __init__(self, name, uri, track_debug_props=False, results_folder=None):
        self.name = name
        self.context_attr_reads_writes = {}
        self.device_attr_reads_writes = {}
        self.channel_attr_reads_writes = {}
        self.debug_attr_reads_writes = {}
        self.uri = uri
        self.ctx = iio.Context(uri)
        self.track_debug_props = track_debug_props
        self.results_folder = results_folder or "iio_coverage_results"
        self.build_context_map()

    def reset(self):
        """Reset the coverage tracker."""
        self.context_attr_reads_writes.clear()
        self.device_attr_reads_writes.clear()
        self.channel_attr_reads_writes.clear()
        self.debug_attr_reads_writes.clear()

    def build_context_map(self):
        """Build a map of context attributes."""
        self.context_attr_reads_writes = {attr: 0 for attr in self.ctx.attrs}
        for dev in self.ctx.devices:
            self.device_attr_reads_writes[dev.name] = {attr: 0 for attr in dev.attrs}
            self.channel_attr_reads_writes[dev.name] = {
                chn.id: {attr: 0 for attr in chn.attrs} for chn in dev.channels
            }
            if self.track_debug_props:
                self.debug_attr_reads_writes[dev.name] = {
                    attr: 0 for attr in dev.debug_attrs
                }

    def export(self):
        """Export raw coverage data."""
        out = {
            "context_attr_reads_writes": self.context_attr_reads_writes,
            "device_attr_reads_writes": self.device_attr_reads_writes,
            "channel_attr_reads_writes": self.channel_attr_reads_writes,
        }
        if self.track_debug_props:
            out["debug_attr_reads_writes"] = self.debug_attr_reads_writes
        return out

    def export_to_file(self, filename=None):
        """Export coverage data to a file.

        Args:
            filename (str, optional): Name of the file to save the coverage data.
            If None, defaults to "{self.name}_coverage.json".
        """
        if filename is None:
            filename = f"{self.name}_coverage.json"
        if not os.path.exists(self.results_folder):
            os.makedirs(self.results_folder)
        filename = os.path.join(os.getcwd(), self.results_folder, filename)
        with open(filename, "w") as f:
            json.dump(self.export(), f, indent=4)
        print(f"Coverage data exported to {filename}")

    def print_context_map(self):
        print("Context Attribute Reads:")
        pprint(self.context_attr_reads_writes)
        print("Device Attribute Reads:")
        pprint(self.device_attr_reads_writes)
        print("Channel Attribute Reads:")
        pprint(self.channel_attr_reads_writes)
        if self.track_debug_props:
            print("Debug Attribute Reads:")
            pprint(self.debug_attr_reads_writes)

    def calculate_coverage(self):
        """Calculate coverage based on attribute reads and writes."""

        total_context_reads_writes = sum(self.context_attr_reads_writes.values())
        total_context_attributes = len(self.context_attr_reads_writes)

        total_device_reads_writes = sum(
            sum(device.values()) for device in self.device_attr_reads_writes.values()
        )
        total_device_attributes = sum(
            len(device) for device in self.device_attr_reads_writes.values()
        )
        if self.track_debug_props:
            total_debug_reads_writes = 0
            for dev in self.debug_attr_reads_writes:
                for attr in self.debug_attr_reads_writes[dev]:
                    total_debug_reads_writes += self.debug_attr_reads_writes[dev][attr]

            total_device_attributes = sum(
                len(self.debug_attr_reads_writes[dev])
                for dev in self.debug_attr_reads_writes
            )

        total_channel_reads_writes = 0
        total_channel_attributes = 0
        for device in self.channel_attr_reads_writes:
            for channel in self.channel_attr_reads_writes[device]:
                total_channel_reads_writes += sum(
                    self.channel_attr_reads_writes[device][channel].values()
                )
                total_channel_attributes += len(
                    self.channel_attr_reads_writes[device][channel]
                )

        out = {
            "context_coverage": (
                total_context_reads_writes / total_context_attributes
                if total_context_attributes
                else 0
            ),
            "device_coverage": (
                total_device_reads_writes / total_device_attributes
                if total_device_attributes
                else 0
            ),
            "channel_coverage": (
                total_channel_reads_writes / total_channel_attributes
                if total_channel_attributes
                else 0
            ),
            "total_coverage": (
                total_context_reads_writes
                + total_device_reads_writes
                + total_channel_reads_writes
            )
            / (
                total_context_attributes
                + total_device_attributes
                + total_channel_attributes
            ),
            "total_context_reads_writes": total_context_reads_writes,
            "total_device_reads_writes": total_device_reads_writes,
            "total_channel_reads_writes": total_channel_reads_writes,
            "total_context_attributes": total_context_attributes,
            "total_device_attributes": total_device_attributes,
            "total_channel_attributes": total_channel_attributes,
        }

        if self.track_debug_props:
            out["total_debug_reads_writes"] = total_debug_reads_writes
            out["total_debug_attributes"] = total_device_attributes
            out["debug_coverage"] = (
                total_debug_reads_writes / total_device_attributes
                if total_device_attributes
                else 0
            )
        return out
