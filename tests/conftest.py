import pytest

pytest_plugins = "pytester"


def pytest_addoption(parser):
    parser.addoption(
        "--disable_mock", action="store_true", help="Disable mocking",
    )
    parser.addoption(
        "--hw",
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


@pytest.fixture(scope="session")
def use_mocking(request):
    if request.config.getoption("--disable_mock"):
        return False
    else:
        return True


@pytest.fixture(scope="session")
def hw_select(request):
    val = request.config.getoption("--hw")
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
