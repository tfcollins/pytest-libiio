import logging
from pprint import pprint

import iio

import pytest

# Set logging to debug level
logging.basicConfig(level=logging.DEBUG)


@pytest.mark.skip(reason="This is a smoke test manual testing with hardware")
def test_coverage_smoke():
    """Test to ensure coverage tracking is working."""
    from pytest_libiio import coverage

    # Initialize the coverage tracker
    cov = coverage.MultiContextTracker()
    cov.do_monkey_patch()

    # Simulate some attribute reads and writes
    uri = "ip:192.168.2.1"
    context = iio.Context(uri)

    cov.add_instance("Pluto", uri)
    cov.set_tracker("Pluto")

    device = context.find_device("ad9361-phy")
    channel = device.find_channel("altvoltage0", True)

    # Perform some operations to generate coverage data
    channel.attrs["frequency"].value = "1000000000"

    # Calculate and print coverage
    coverage_data = cov.trackers["Pluto"].calculate_coverage()
    pprint(coverage_data)
    assert coverage_data

    # Verify we hit 1 read/write for the frequency attribute
    assert coverage_data["total_channel_reads_writes"] == 1
    assert coverage_data["channel_coverage"] > 0


@pytest.mark.iio_hardware(["pluto"])
def test_coverage_tracker(iio_uri):
    ctx = iio.Context(iio_uri)

    device = ctx.find_device("ad9361-phy")
    channel = device.find_channel("altvoltage0", True)

    attr_name = "frequency"
    channel.attrs[attr_name].value = "2000000000"
