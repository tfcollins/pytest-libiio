import os
import pathlib

import pytest

pytest_plugins = "pytester"

path = pathlib.Path(__file__).parent.absolute()
default_resource_dir = os.path.join(path, "..", "pytest_libiio", "resources", "devices")


@pytest.fixture
def testdir(testdir):
    """Override testdir to disable labgrid plugin in pytester subprocesses.

    labgrid's pytest_configure hook asserts StepLogger is not already started,
    which fails when pytester spawns a subprocess that inherits the plugin.
    """
    testdir.makeini("[pytest]\naddopts = -p no:labgrid -p no:asyncio -p no:anyio")
    return testdir


def pytest_addoption(parser):
    parser.addoption(
        "--disable_mock",
        action="store_true",
        help="Disable mocking",
    )
    parser.addoption(
        "--hw-manual",
        action="store",
        dest="hw_map",
        default=None,
        help="Set expected hardware",
    )
    parser.addoption(
        "--test-uri",
        action="store",
        dest="uri_val",
        default=None,
        help="Set uri to test against",
    )
    parser.addoption(
        "--resource-dir",
        action="store",
        dest="resource_dir",
        default=default_resource_dir,
        help="Set path of resource folder",
    )


@pytest.fixture(scope="session")
def use_mocking(request):
    return not request.config.getoption("--disable_mock")


@pytest.fixture(scope="session")
def hw_select(request):
    val = request.config.getoption("--hw-manual")
    if not val:
        return "adrv9361"
    else:
        return val


@pytest.fixture(scope="session")
def uri_select(request):
    val = request.config.getoption("--test-uri")
    if not val:
        return "ip:192.168.86.56"
    else:
        return val


@pytest.fixture(scope="session")
def resource_folder(request):
    return os.path.abspath(request.config.getoption("--resource-dir"))
