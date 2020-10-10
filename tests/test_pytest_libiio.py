# -*- coding: utf-8 -*-

uri = "ip:192.168.86.35"


def test_context_fixture(testdir):
    """Make sure that pytest accepts our fixture."""

    # create a temporary pytest test module
    testdir.makepyfile(
        """
        def test_sth(context_desc):
            assert isinstance(context_desc,list)

    """
    )

    # run pytest with the following cmd args
    result = testdir.runpytest("--scan-verbose", "-v", "-s")

    # fnmatch_lines does an assertion internally
    print(result.stdout.str())
    assert "PASSED" in result.stdout.str()
    assert result.ret == 0


def test_context_fixture_uri(testdir):
    """Make sure that pytest accepts our fixture."""

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
    result = testdir.runpytest("--uri=" + uri, "-v", "-s")

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::test_sth PASSED*"])

    # make sure that that we get a '0' exit code for the testsuite
    assert result.ret == 0


def test_context_fixture_uri_adi_map(testdir):
    """Make sure that pytest accepts our fixture."""

    # create a temporary pytest test module
    testdir.makepyfile(
        """
        def test_sth(context_desc):
            assert context_desc
            found = False
            for ctx in context_desc:
                if ctx['hw'] == 'adrv9361':
                    found = True
            assert found
    """
    )

    # run pytest with the following cmd args
    result = testdir.runpytest("--adi-hw-map", "--uri=" + uri, "-v", "-s")

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::test_sth PASSED*"])

    # make sure that that we get a '0' exit code for the testsuite
    assert result.ret == 0


def test_context_desc_fixture_uri_adi_map(testdir):
    """Make sure that pytest accepts our fixture."""

    # create a temporary pytest test module
    testdir.makepyfile(
        """
        import pytest

        @pytest.mark.iio_hardware("adrv9361")
        def test_sth(context_desc):
            assert context_desc
            found = False
            for ctx in context_desc:
                if ctx['hw'] == 'adrv9361':
                    found = True
            assert found
    """
    )

    # run pytest with the following cmd args
    result = testdir.runpytest("--adi-hw-map", "--uri=" + uri, "-v", "-s")

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["*::test_sth PASSED*"])

    # make sure that that we get a '0' exit code for the testsuite
    assert result.ret == 0


def test_help_message(testdir):
    result = testdir.runpytest("--help",)
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(["libiio:", "*--uri=URI*Set libiio URI to utilize"])


# def test_print_scan_message(testdir):
#     result = testdir.runpytest("--scan-verbose", "--help")
#     # fnmatch_lines does an assertion internally
#     result.stdout.fnmatch_lines(
#         ["libiio:", "*--uri=URI*Set libiio URI to utilize",]
#     )
