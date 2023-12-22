# -*- coding: utf-8 -*-
import os
import time

import pytest

sleep = 1
uri = "ip:192.168.86.35"
devs = [
    "ad7291",
    "ad9361-phy",
    "xadc",
    "ad9517-3",
    "cf-ad9361-dds-core-lpc",
    "cf-ad9361-lpc",
]


# Mocks
def mock_Context(uri):
    class Channel(object):
        scan_element = True

    class Device(object):
        channels = [Channel()]

        def __init__(self, name):
            self.name = name

    class Context(object):
        def __init__(self, uri, devs):
            self.attrs = {"uri": uri}
            self.devices = []
            for dev in devs:
                self.devices.append(Device(dev))

    return Context(uri, devs)


def mock_scan_contexts():
    info = uri[3:]
    uri_s = "ip:" + info
    info += " (" + ",".join(devs) + ")"
    return {uri_s: info}


# Tests
def test_check_version():
    from pytest_libiio import __version__ as v
    import re

    matched = re.match("[0-9].[0-9].[0-9]", v)
    assert bool(matched)


def test_context_fixture_smoke(testdir, use_mocking, mocker):
    """Make sure that pytest accepts our fixture."""
    if use_mocking:
        mocker.patch("iio.scan_contexts", mock_scan_contexts)
        mocker.patch("iio.Context", mock_Context)

    time.sleep(sleep)

    # create a temporary pytest test module
    testdir.makepyfile(
        """
        def test_sth(context_desc):
            print(context_desc)
            assert isinstance(context_desc,list)

    """
    )

    # run pytest with the following cmd args
    result = testdir.runpytest("--scan-verbose", "-v", "-s")

    # fnmatch_lines does an assertion internally
    print(result.stdout.str())
    assert "PASSED" in result.stdout.str()
    assert result.ret == 0


def test_context_fixture_uri_unknown(testdir, use_mocking, uri_select, mocker):
    """Make sure that pytest accepts our fixture."""
    if use_mocking:
        mocker.patch("iio.scan_contexts", mock_scan_contexts)
        mocker.patch("iio.Context", mock_Context)

    time.sleep(sleep)

    # create a temporary pytest test module
    testdir.makepyfile(
        """
        def test_sth(context_desc):
            assert context_desc
            found = False
            for ctx in context_desc:
                if ctx['hw'] == 'Unknown':
                    found = True
            assert found
    """
    )

    # run pytest with the following cmd args
    result = testdir.runpytest("--uri=" + uri_select, "-v", "-s")

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::test_sth PASSED*"])

    # make sure that that we get a '0' exit code for the testsuite
    assert result.ret == 0


def test_context_fixture_scan_adi_map(testdir, use_mocking, hw_select, mocker):
    """Make sure that pytest accepts our fixture."""
    if use_mocking:
        mocker.patch("iio.scan_contexts", mock_scan_contexts)
        mocker.patch("iio.Context", mock_Context)

    time.sleep(sleep)

    # create a temporary pytest test module
    testdir.makepyfile(
        """
        def test_sth(context_desc):
            assert context_desc
            found = False
            for ctx in context_desc:
                if ctx['hw'] == '"""
        + hw_select
        + """':
                    found = True
            assert found
    """
    )

    # run pytest with the following cmd args
    result = testdir.runpytest("--adi-hw-map", "-v", "-s")

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::test_sth PASSED*"])

    # make sure that that we get a '0' exit code for the testsuite
    assert result.ret == 0


def test_context_fixture_scan_adi_map_single(testdir, use_mocking, hw_select, mocker):
    """Make sure that pytest accepts our fixture."""
    if use_mocking:
        mocker.patch("iio.scan_contexts", mock_scan_contexts)
        mocker.patch("iio.Context", mock_Context)

    time.sleep(sleep)

    # create a temporary pytest test module
    testdir.makepyfile(
        """
        def test_sth(single_ctx_desc):
            assert single_ctx_desc
            found = False
            assert single_ctx_desc["hw"] == '"""
        + hw_select
        + """'
    """
    )

    # run pytest with the following cmd args
    result = testdir.runpytest("--adi-hw-map", "-v", "-s")

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::test_sth PASSED*"])

    # make sure that that we get a '0' exit code for the testsuite
    assert result.ret == 0


def test_context_fixture_scan_adi_map_single_uri(
    testdir, use_mocking, hw_select, mocker
):
    """Make sure that pytest accepts our fixture."""
    if use_mocking:
        mocker.patch("iio.scan_contexts", mock_scan_contexts)
        mocker.patch("iio.Context", mock_Context)

    time.sleep(sleep)

    # create a temporary pytest test module
    testdir.makepyfile(
        """
        def test_sth(iio_uri):
            assert iio_uri
            found = False
            assert iio_uri == '"""
        + uri
        + """'
    """
    )

    # run pytest with the following cmd args
    result = testdir.runpytest("--adi-hw-map", "-v", "-s")

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::test_sth PASSED*"])

    # make sure that that we get a '0' exit code for the testsuite
    assert result.ret == 0


def test_context_fixture_uri_adi_map(
    testdir, use_mocking, uri_select, hw_select, mocker
):
    """Make sure that pytest accepts our fixture."""
    if use_mocking:
        mocker.patch("iio.scan_contexts", mock_scan_contexts)
        mocker.patch("iio.Context", mock_Context)

    time.sleep(sleep)

    # create a temporary pytest test module
    testdir.makepyfile(
        """
        def test_sth(context_desc):
            assert context_desc
            found = False
            for ctx in context_desc:
                if ctx['hw'] == '"""
        + hw_select
        + """':
                    found = True
            assert found
    """
    )

    # run pytest with the following cmd args
    result = testdir.runpytest("--adi-hw-map", "--uri=" + uri_select, "-v", "-s")

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::test_sth PASSED*"])

    # make sure that that we get a '0' exit code for the testsuite
    assert result.ret == 0


def test_context_desc_fixture_uri_adi_map(
    testdir, use_mocking, uri_select, hw_select, mocker
):
    """Make sure that pytest accepts our fixture."""
    if use_mocking:
        mocker.patch("iio.scan_contexts", mock_scan_contexts)
        mocker.patch("iio.Context", mock_Context)

    time.sleep(sleep)

    # create a temporary pytest test module
    testdir.makepyfile(
        """
        import pytest

        @pytest.mark.iio_hardware('"""
        + hw_select
        + """')
        def test_sth(context_desc):
            assert context_desc
            found = False
            for ctx in context_desc:
                if ctx['hw'] == '"""
        + hw_select
        + """':
                    found = True
            assert found
    """
    )

    # run pytest with the following cmd args
    result = testdir.runpytest("--adi-hw-map", "--uri=" + uri_select, "-v", "-s")

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::test_sth PASSED*"])

    # make sure that that we get a '0' exit code for the testsuite
    assert result.ret == 0


@pytest.mark.parametrize("hw", ["pluto", "ad9081", "adrv9371", "adrv9002"])
def test_iio_uri_fixture_emulation(testdir, hw):
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
    result = testdir.runpytest("--adi-hw-map", "--scan-verbose", "-vvv", "-s", "--emu")

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*PASSED*"])
    result.stdout.fnmatch_lines(["*Starting iio-emu*"])

    # make sure that that we get a '0' exit code for the testsuite
    assert result.ret == 0


@pytest.mark.parametrize("hw", ["pluto_rev_c"])
def test_iio_uri_fixture_emulation_xml_path(testdir, resource_folder, hw):
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
        "-v",
        "-s",
        "--scan-verbose",
        "--emu",
        f"--emu-xml={resource_folder}/pluto.xml",
    )

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*PASSED*"])

    # make sure that that we get a '0' exit code for the testsuite
    assert result.ret == 0


@pytest.mark.parametrize("hw", ["pluto_rev_c"])
def test_metadata_collection(testdir, resource_folder, hw):
    """Make sure that pytest accepts our fixture."""
    time.sleep(sleep)

    # create a temporary pytest test module
    test_name = "test_sth"
    testdir.makepyfile(
        """
        import pytest
        import iio

        @pytest.mark.iio_hardware('"""
        + hw
        + f"""')
        def {test_name}(iio_uri):
            assert iio_uri
            ctx = iio.Context(iio_uri)
    """
    )

    # run pytest with the following cmd args
    tdf = "test_data_folder"
    result = testdir.runpytest(
        "--adi-hw-map",
        "-v",
        "-s",
        "--scan-verbose",
        "--telm",
        f"--telm-data-folder={tdf}",
        "--emu",
        f"--emu-xml={resource_folder}/pluto.xml",
    )

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*PASSED*"])

    # make sure that that we get a '0' exit code for the testsuite
    assert result.ret == 0

    # make sure pickle file generated
    file_name = f"{tdf}/{test_name}.pkl"
    assert os.path.isfile(file_name)


# def test_help_message(testdir):
#     result = testdir.runpytest("--help",)
#     # fnmatch_lines does an assertion internally
#     result.stdout.fnmatch_lines(["libiio:", "*--uri=URI*Set libiio URI to utilize"])


# def test_print_scan_message(testdir):
#     result = testdir.runpytest("--scan-verbose", "--help")
#     # fnmatch_lines does an assertion internally
#     result.stdout.fnmatch_lines(
#         ["libiio:", "*--uri=URI*Set libiio URI to utilize",]
#     )
