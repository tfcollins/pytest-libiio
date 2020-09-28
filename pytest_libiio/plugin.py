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
        "--device",
        action="store",
        dest="device",
        default=None,
        help="Use only tests with this hardware name. If URI is set that device is assumed to have that uri",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "hw(list_of_hardware): Marker for tests that require specific hardware.",
    )


def common_member(a, b):
    a_set = set(a)
    b_set = set(b)
    if a_set & b_set:
        return True
    else:
        return False


def pytest_collection_modifyitems(config, items):
    # Go out and determine the hardware available
    contexts = search_contexts(config)
    hws = [ctx["hw"] for ctx in contexts]

    skip = pytest.mark.skip(reason="Skipping since hardware not found")
    # Filter tests based on hardware
    for item in items:
        skip_test = False
        # hwnames = [mark.args[0] for mark in item.iter_markers(name='hw')]
        for mark in item.iter_markers(name="iio"):
            print(mark)
            if "hardware" in mark.kwargs:
                if not common_member(mark.kwargs["hardware"], hws):
                    skip_test = True
        if skip_test:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def contexts(request):
    """ Contexts fixture which provides a list of dictionaries of found boards
    """
    return search_contexts(request.config)


def search_contexts(config):
    if config.getoption("--adi-hw-map"):
        path = pathlib.Path(__file__).parent.absolute()
        filename = os.path.join(path, "resources", "adi_hardware_map.yml")
    elif config.getoption("--custom-hw-map"):
        filename = config.getoption("--custom-hw-map")
    else:
        filename = None

    if filename:
        map = import_hw_map(filename)
    else:
        map = None

    uri = config.getoption("--uri")
    in_device_name = config.getoption("--device")
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

        ctx_plus_hw = {
            "uri": uri,
            "type": ctx.attrs["uri"].split(":")[0],
            "devices": devices,
            "hw": lookup_hw_from_map(ctx, map, in_device_name),
        }
        return [ctx_plus_hw]

    return find_contexts(config, map)


def import_hw_map(filename):
    if not os.path.exists(filename):
        raise Exception("Hardware map file not found")
    stream = open(filename, "r")
    map = yaml.safe_load(stream)
    stream.close()
    return map


def lookup_hw_from_map(ctx, map, in_device_name):
    if not map:
        return in_device_name if in_device_name else "Unknown"
    hw = []
    for device in ctx.devices:
        chans = 0
        for chan in device.channels:
            chans = chans + chan.scan_element
        dev = {"name": device.name, "num_channels": chans}
        hw.append(dev)

    map_tally = {}
    best = 0
    bestDev = "Unknown"
    # Loop over devices
    for device in map:
        drivers = map[device]
        found = 0
        for driver in drivers:
            # Loop over drivers
            for h in hw:
                d = driver.split(",")
                name = d[0]
                if h["name"] == name:
                    found += 1
                else:
                    continue
                if len(d) > 1:
                    if h["num_channels"] == int(d[1]):
                        found += 1
        # print("---------",device,"found",found)

        map_tally[device] = found
        if found > best:
            best = found
            bestDev = device

    return bestDev


def find_contexts(config, map):
    ctxs = iio.scan_contexts()
    if not ctxs:
        print("No libiio contexts found")
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
    return ctxs_plus_hw
