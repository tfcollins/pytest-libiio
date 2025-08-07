import logging
import time
from pprint import pprint

import iio

import pytest

# Set logging to debug level
logging.basicConfig(level=logging.DEBUG)

sleep = 1


@pytest.fixture(scope="module", autouse=True)
def reset_monkey_patch():
    """Reset the monkey patch before and after tests."""
    from pytest_libiio import mkpatch

    mkpatch.unset_monkey_patch()
    yield


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


@pytest.mark.parametrize("hw", ["pluto", "ad9081", "adrv9371", "adrv9002"])
def test_emulation_with_coverage(testdir, hw):
    """Make sure that pytest accepts our fixture."""
    time.sleep(sleep)

    # create a temporary pytest test module
    testdir.makepyfile(
        """
        import pytest
        import iio

        @pytest.mark.iio_hardware('"""
        + hw
        + """')
        def test_sth(iio_uri):
            assert iio_uri
            ctx = iio.Context(iio_uri)
    """
    )

    # run pytest with the following cmd args
    result = testdir.runpytest(
        "--adi-hw-map",
        "--scan-verbose",
        "-vvv",
        "-s",
        "--emu",
        "--iio-coverage",
        "--iio-coverage-debug-props",
        "--iio-coverage-print-results",
        "--iio-coverage-folder=iio_coverage_results_test",
    )

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*PASSED*"])
    result.stdout.fnmatch_lines(["*Starting iio-emu*"])
    result.stdout.fnmatch_lines(["*IIO coverage tracking enabled*"])

    # Check output for coverage data
    result.stdout.fnmatch_lines(["*Debug Attribute Reads:*"])

    # Check for generated coverage data files
    here = testdir.tmpdir
    coverage_files = list(here.join("iio_coverage_results_test").visit("*.json"))
    assert coverage_files, "No coverage data files generated"

    # make sure that that we get a '0' exit code for the testsuite
    assert result.ret == 0
