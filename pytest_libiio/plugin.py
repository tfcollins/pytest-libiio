# -*- coding: utf-8 -*-

import os
import pathlib

import iio

import pytest
import yaml


def pytest_addoption(parser):
    group = parser.getgroup("libiio")
    group.addoption(
        "--uri",
        action="store",
        dest="uri",
        default=None,
        help="Set libiio URI to utilize",
    )
    group.addoption(
        "--scan-verbose",
        action="store_true",
        dest="scan_verbose",
        default=False,
        help="Print info of found contexts when scanning",
    )
    group.addoption(
        "--adi-hw-map",
        action="store_true",
        dest="adi_hw_map",
        default=False,
        help="Use ADI hardware map to determine hardware names based on context drivers",
    )
    group.addoption(
        "--custom-hw-map",
        action="store",
        dest="hw_map",
        default=None,
        help="Path to custom hardware map for drivers",
    )
    group.addoption(
        "--hw",
        action="store",
        dest="hw_select",
        default=None,
        help="Define hardware name of provided URI. Will ignore scan information and requires input URI argument",
    )


def pytest_configure(config):
    # register an additional marker
    config.addinivalue_line(
        "markers", "iio_hardware(hardware): Provide list of hardware applicable to test"
    )


@pytest.fixture(scope="function")
def iio_uri(single_ctx_desc):
    """ URI fixture which provides a string of the target uri of the
        found board filtered by iio_hardware marker. If no hardware matching
        the required hardware is found, the test is skipped. If no iio_hardware
        marker is applied, first context uri is returned. If list of hardware
        markers are provided, the first matching is returned.
    """
    if isinstance(single_ctx_desc, dict):
        return single_ctx_desc["uri"]
    else:
        return False


@pytest.fixture(scope="function")
def single_ctx_desc(request, _contexts):
    """ Contexts description fixture which provides a single dictionary of
        found board filtered by iio_hardware marker. If no hardware matching
        the required hardware is found, the test is skipped. If no iio_hardware
        marker is applied, first context is returned. If list of hardware markers
        are provided. First matching is returned.
    """
    marker = request.node.get_closest_marker("iio_hardware")
    if _contexts:
        if not marker or not marker.args:
            return _contexts[0]
        hardware = marker.args[0]
        hardware = hardware if isinstance(hardware, list) else [hardware]
        if not marker:
            return _contexts[0]
        else:
            for dec in _contexts:
                if dec["hw"] in marker.args[0]:
                    return dec
    pytest.skip("No required hardware found")


@pytest.fixture(scope="function")
def context_desc(request, _contexts):
    """ Contexts description fixture which provides a list of dictionaries of
        found board filtered by iio_hardware marker. If no hardware matching
        the required hardware if found, the test is skipped
    """
    marker = request.node.get_closest_marker("iio_hardware")
    if _contexts:
        if not marker or not marker.args:
            return _contexts
        hardware = marker.args[0]
        hardware = hardware if isinstance(hardware, list) else [hardware]
        if not marker:
            return _contexts
        desc = [dec for dec in _contexts if dec["hw"] in marker.args[0]]
        if desc:
            return desc
    pytest.skip("No required hardware found")


@pytest.fixture(scope="session")
def _contexts(request):
    """ Contexts fixture which provides a list of dictionaries of found boards
    """
    if request.config.getoption("--adi-hw-map"):
        path = pathlib.Path(__file__).parent.absolute()
        filename = os.path.join(path, "resources", "adi_hardware_map.yml")
    elif request.config.getoption("--custom-hw-map"):
        filename = request.config.getoption("--custom-hw-map")
    else:
        filename = None

    map = import_hw_map(filename) if filename else None
    uri = request.config.getoption("--uri")
    if uri:
        try:
            ctx = iio.Context(uri)
        except TimeoutError:
            raise Exception("URI {} has no reachable context".format(uri))

        devices = []
        for dev in ctx.devices:
            name = dev.name
            if name:
                devices.append(name)
        devices = ",".join(devices)

        hw = request.config.getoption("--hw") or lookup_hw_from_map(ctx, map)
        if "uri" in ctx.attrs:
            uri_type = ctx.attrs["uri"].split(":")[0]
        else:
            uri_type = uri.split(":")[0]

        ctx_plus_hw = {
            "uri": uri,
            "type": uri_type,
            "devices": devices,
            "hw": hw,
        }
        if request.config.getoption("--scan-verbose"):
            print("\nHardware found at specified uri:", ctx_plus_hw["hw"])
        return [ctx_plus_hw]

    return find_contexts(request.config, map)


def import_hw_map(filename):
    if not os.path.exists(filename):
        raise Exception("Hardware map file not found")
    with open(filename, "r") as stream:
        map = yaml.safe_load(stream)
    return map


def lookup_hw_from_map(ctx, map):
    if not map:
        return "Unknown"
    hw = []
    for device in ctx.devices:
        chans = sum(chan.scan_element for chan in device.channels)
        dev = {"name": device.name, "num_channels": chans}
        hw.append(dev)

    ctx_attrs = {attr: ctx.attrs[attr] for attr in ctx.attrs}

    map_tally = {}
    best = 0
    bestDev = "Unknown"
    # Loop over devices
    for device in map:
        drivers_and_attrs = map[device]
        found = 0
        for driver_or_attr in drivers_and_attrs:
            # Check attributes
            if isinstance(driver_or_attr, dict):
                for attr_type in driver_or_attr:
                    # Compare context attrs
                    if attr_type == "ctx_attr":
                        for attr_dict in driver_or_attr["ctx_attr"]:
                            for attr_name in attr_dict:
                                # loop over found and compare to
                                for hw_ctx_attr in ctx_attrs:
                                    if (
                                        hw_ctx_attr == attr_name
                                        and attr_dict[attr_name]
                                        in ctx_attrs[hw_ctx_attr]
                                    ):
                                        found += 1
                    # Compare other attribute types ...
                    if attr_type == "dev_attr":
                        pass
                continue
            # Loop over drivers
            for h in hw:
                d = driver_or_attr.split(",")
                name = d[0]
                if h["name"] == name:
                    found += 1
                else:
                    continue
                if len(d) > 1 and h["num_channels"] == int(d[1]):
                    found += 1

        map_tally[device] = found
        if found > best:
            best = found
            bestDev = device

    return bestDev


def find_contexts(config, map):
    ctxs = iio.scan_contexts()
    if not ctxs:
        print("\nNo libiio contexts found")
        return False
    ctxs_plus_hw = []
    for uri in ctxs:
        info = ctxs[uri]
        type = uri.split(":")[0]
        devices = info.split("(")[1].split(")")[0]

        if config.getoption("--scan-verbose"):
            string = "\nContext: {}".format(uri)
            string += "\n\tType: {}".format(type)
            string += "\n\tInfo: {}".format(info)
            string += "\n\tDevices: {}".format(devices)
            print(string)

        ctx_plus_hw = {
            "uri": uri,
            "type": type,
            "devices": devices,
            "hw": lookup_hw_from_map(iio.Context(uri), map),
        }
        ctxs_plus_hw.append(ctx_plus_hw)
    else:
        if config.getoption("--scan-verbose"):
            print("\nNo libiio contexts found")

    return ctxs_plus_hw
