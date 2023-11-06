import os
import pathlib

import pytest

pytest_plugins = "pytester"

path = pathlib.Path(__file__).parent.absolute()
default_resource_dir = os.path.join(path, "..", "pytest_libiio", "resources", "devices")


def pytest_addoption(parser):
    parser.addoption(
        "--disable_mock", action="store_true", help="Disable mocking",
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
    return "adrv9361" if not val else val


@pytest.fixture(scope="session")
def uri_select(request):
    val = request.config.getoption("--test-uri")
    return "ip:192.168.86.56" if not val else val


@pytest.fixture(scope="session")
def resource_folder(request):
    return request.config.getoption("--resource-dir")
