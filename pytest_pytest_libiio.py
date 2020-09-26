# -*- coding: utf-8 -*-

import iio
import pytest


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
        "--iio-scan",
        action="store_true",
        dest="iio_scan",
        default=False,
        help="Scan for available libiio contexts",
    )


@pytest.fixture(scope="session")
def contexts(request):
    """ Contexts fixture which provides a list of dictionaries of found boards 
    """
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

        ctx_plus_hw = {
            "uri": uri,
            "type": ctx.attrs["uri"].split(":")[0],
            "devices": devices,
            "hw": check_board_other(ctx),
        }
        return [ctx_plus_hw]

    return find_contexts(request.config)


def find_contexts(config):
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
            "hw": lookup_hw(uri),
        }
        ctxs_plus_hw.append(ctx_plus_hw)
    return ctxs_plus_hw


def lookup_hw(uri):
    ctx = iio.Context(uri)
    return check_board_other(ctx)


class device:
    def __init__(self, name, channels=[]):
        self.name = name
        self.channels = channels


def check_config(ctx, devices):
    found = 0
    try:
        for dev in ctx.devices:
            for fdev in devices:
                if not dev.name:
                    continue
                if dev.name.lower() == fdev.name.lower():
                    if fdev.channels:
                        chans = 0
                        for chan in dev.channels:
                            chans = chans + chan.scan_element
                        found = found + (chans == fdev.channels)
                    else:
                        found = found + 1
        return found == len(devices)
    except:
        return False


def check_board_other(ctx):
    if check_config(
        ctx, [device("ad7291-ccbox"), device("ad9361-phy"), device("cf-ad9361-lpc", 4)]
    ):
        return "packrf"
    if check_config(
        ctx, [device("ad9517"), device("ad9361-phy"), device("cf-ad9361-lpc", 4)]
    ):
        return "adrv9361"
    if check_config(ctx, [device("ad7291-bob"), device("cf-ad9361-lpc", 2)]):
        return "adrv9364"
    if check_config(
        ctx, [device("adm1177"), device("ad9361-phy"), device("cf-ad9361-lpc", 2)]
    ):
        return "pluto"
    if check_config(
        ctx, [device("ad7291"), device("ad9361-phy"), device("cf-ad9361-lpc", 4)]
    ):
        return "fmcomms2"
    if check_config(
        ctx, [device("ad7291"), device("ad9361-phy"), device("cf-ad9361-lpc", 2),],
    ):
        return "fmcomms4"
    if check_config(ctx, [device("ad9361-phy"), device("ad9361-phy-b")]):
        return "fmcomms5"
    if check_config(ctx, [device("ad9361-phy"), device("cf-ad9361-lpc", 2)]):
        return "ad9364"
    if check_config(ctx, [device("ad9361-phy"), device("cf-ad9361-lpc", 4)]):
        return "ad9361"

    if check_config(ctx, [device("axi-ad9144-hpc", 4), device("axi-ad9680-hpc", 2)]):
        return "daq2"

    if check_config(ctx, [device("axi-ad9152-hpc", 2), device("axi-ad9680-hpc", 2)]):
        return "daq3"

    if check_config(ctx, [device("adrv9009-phy"), device("adrv9009-phy-b")]):
        return "adrv9009-dual"
    if check_config(ctx, [device("adrv9009-phy")]):
        return "adrv9009"

    if check_config(ctx, [device("ad9371-phy")]):
        return "ad9371"

    if check_config(ctx, [device("adrv9002-phy")]):
        return "adrv9002"

    for dev in ctx.devices:
        if dev.name:
            return dev.name

    return "Unknown"
