# -*- coding: utf-8 -*-

import logging
import os
import pathlib
import pickle
import signal
import socket
import subprocess
import time
from shutil import which

import iio

import pytest
import pytest_libiio.meta as meta
import yaml

from .coverage import MultiContextTracker

IIO_EMU_BASE_PORT = 30431


class iio_emu_manager:
    def __init__(
        self,
        xml_path: str,
        auto: bool = True,
        rx_dev: str = None,
        tx_dev: str = None,
        custom_port: int = None,
    ):
        self.xml_path = xml_path
        self.rx_dev = rx_dev
        self.tx_dev = tx_dev
        self.current_device = None
        self.auto = auto
        self.data_devices = None
        self.custom_port = custom_port

        iio_emu = which("iio-emu") is None
        if iio_emu:
            raise Exception("iio-emu not found on path")

        hostname = socket.gethostname()
        self.local_ip = socket.gethostbyname(hostname)
        self.uri = f"ip:{self.local_ip}"
        if self.custom_port:
            self.uri += f":{self.custom_port}"
        self.p = None
        if os.getenv("IIO_EMU_URI"):
            self.uri = os.getenv("IIO_EMU_URI")

    def __del__(self):
        if self.p:
            self.stop()

    def start(self):
        with open("data.bin", "w"):
            pass
        cmd = ["iio-emu", "generic", self.xml_path]
        if self.data_devices:
            for dev in self.data_devices:
                cmd.append(f"{dev}@data.bin")
        if self.custom_port:
            cmd.append("-p")
            cmd.append(f"{self.custom_port}")
        self.p = subprocess.Popen(cmd)
        time.sleep(3)  # wait for server to boot
        if self.p.poll():
            self.p.send_signal(signal.SIGINT)
            raise Exception("iio-emu failed to start... exiting")

    def stop(self):
        if self.p:
            self.p.send_signal(signal.SIGINT)
        self.p = None


def gen_markdown_table(systems_data, filename):
    """Generate a markdown table from the coverage data."""
    table = "# IIO Coverage Report\n\n"
    table += "| System | Attribute Type | Coverage (%) |\n"
    table += "|--------|----------------|----------|\n"
    print(systems_data)
    for system in systems_data:
        for attr in systems_data[system]:
            print(f"Processing {system} - {attr}")
            if "coverage" in attr:
                coverage = systems_data[system][attr]
                table += f"| {system}  | {attr} | {coverage} |\n"
    with open(filename, "w") as f:
        f.write(table)


def get_hw_map(request):
    if request.config.getoption("--adi-hw-map"):
        path = pathlib.Path(__file__).parent.absolute()
        filename = os.path.join(path, "resources", "adi_hardware_map.yml")
    elif request.config.getoption("--custom-hw-map"):
        filename = request.config.getoption("--custom-hw-map")
    else:
        filename = None

    return import_hw_map(filename) if filename else None


def get_filename(map, hw):
    hw = map[hw]
    fn = None
    dd = None
    for f in hw:
        if isinstance(f, dict) and "emulate" in f.keys():
            emu = f["emulate"]
            for e in emu:
                if "filename" in e:
                    fn = e["filename"]
                if "data_devices" in e:
                    dd = e["data_devices"]
    return fn, dd


def handle_iio_emu(ctx, request, _iio_emu):
    if "hw" in ctx and hasattr(_iio_emu, "auto") and _iio_emu.auto:
        if _iio_emu.current_device != ctx["hw"]:
            # restart with new hw
            if _iio_emu.p:
                print("Stopping iio-emu")
                _iio_emu.stop()
            elif _iio_emu.current_device:
                print("Using same hardware not restarting iio-emu")

            map = get_hw_map(request)
            fn, dd = get_filename(map, ctx["hw"])
            if not fn:
                return ctx
            if request.config.getoption("--emu-xml-dir"):
                path = request.config.getoption("--emu-xml-dir")
                exml = os.path.join(path, fn)
                print("exml", exml)
            else:
                path = pathlib.Path(__file__).parent.absolute()
                exml = os.path.join(path, "resources", "devices", fn)
            if not os.path.exists(exml):
                pytest.skip(f"No XML file found for hardware {ctx['hw']}")
            _iio_emu.xml_path = exml
            _iio_emu.current_device = ctx["hw"]
            _iio_emu.data_devices = dd
            print("Starting iio-emu")
            _iio_emu.start()

    return ctx


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
    group.addoption(
        "--skip-scan",
        action="store_true",
        dest="skip_scan",
        default=False,
        help="Skip avahi scan. This is usually used within CI.",
    )
    group.addoption(
        "--emu",
        action="store_true",
        dest="emu",
        default=False,
        help="Enable context emulation with iio-emu.",
    )
    group.addoption(
        "--emu-xml",
        action="store",
        dest="emu_xml",
        default=False,
        help="Path or name of built-in XML for back-end context",
    )
    group.addoption(
        "--emu-xml-dir",
        action="store",
        dest="emu_xml_dir",
        default=False,
        help="Path to folder with XML files for back-end context",
    )
    group.addoption(
        "--telm",
        action="store_true",
        dest="telm",
        default=False,
        help="Enable hardware telemetry collection on each test",
    )
    group.addoption(
        "--telm-data-folder",
        action="store",
        dest="telm_data_folder",
        default="telm_data",
        help="Folder to store telemetry data",
    )
    group.addoption(
        "--iio-coverage",
        action="store_true",
        dest="iio_coverage",
        default=False,
        help="Enable iio attribute coverage tracking",
    )
    group.addoption(
        "--iio-coverage-debug-props",
        action="store_true",
        dest="iio_coverage_debug_props",
        default=False,
        help="Enable iio attribute coverage tracking for debug properties",
    )
    group.addoption(
        "--iio-coverage-folder",
        action="store",
        dest="iio_coverage_folder",
        default="iio_coverage_results",
        help="Folder to store iio coverage data. Defaults to 'iio_coverage_results'.",
    )
    group.addoption(
        "--iio-coverage-print-results",
        action="store_true",
        dest="iio_coverage_print_results",
        default=False,
        help="Print iio coverage results to console after tests",
    )


def pytest_configure(config):
    # register an additional marker
    config.addinivalue_line(
        "markers", "iio_hardware(hardware): Provide list of hardware applicable to test"
    )

    worker_id = os.environ.get("PYTEST_XDIST_WORKER")
    if worker_id is not None:
        logging.basicConfig(
            format=config.getini("log_file_format"),
            filename=f"tests_{worker_id}.log",
            level=logging.INFO,
        )


def pytest_collection_modifyitems(config, items):
    # Get list of contexts and mapped hardware
    class Object(object):
        config = None

    request = Object()
    request.config = config
    pytest._context_table = find_contexts(config, get_hw_map(request), request)
    if not pytest._context_table:
        return

    # Add xdist marker to split tests based on context
    for item in items:
        mark = item.get_closest_marker("iio_hardware")
        if hasattr(mark, "name") and mark.name == "iio_hardware":
            hw = mark.args[0]
            for info in pytest._context_table:
                if info["hw"] == hw:
                    item.add_marker(
                        pytest.mark.xdist_group(name=f"xdist_{info['uri']}")
                    )


# initialize coverage tracker
def pytest_sessionstart(session):
    class Object(object):
        coverage_tracker = None

    if session.config.getoption("--iio-coverage"):
        session.config.pytest_libiio = Object()
        session.config.pytest_libiio.coverage_tracker = MultiContextTracker()
        session.config.pytest_libiio.coverage_tracker.do_monkey_patch()
        session.config.pytest_libiio.coverage_tracker.track_debug_props = bool(
            session.config.getoption("--iio-coverage-debug-props")
        )
        print("IIO coverage tracking enabled")
    else:
        session.config.pytest_libiio = Object()
        session.config.pytest_libiio.coverage_tracker = None


def pytest_sessionfinish(session, exitstatus):
    """Called after all tests have run."""
    if session.config.getoption("--iio-coverage"):
        if tracker := session.config.pytest_libiio.coverage_tracker:
            all_systems_tracked = {}
            for name in tracker.trackers:
                if session.config.getoption("--iio-coverage-print-results"):
                    tracker.trackers[name].print_context_map()
                if session.config.getoption("--iio-coverage-folder"):
                    tracker.trackers[name].results_folder = session.config.getoption(
                        "--iio-coverage-folder"
                    )
                tracker.trackers[name].export_to_file()
                all_systems_tracked[name] = tracker.trackers[name].calculate_coverage()
            # Export to markdown report
            full_path = os.path.join(
                os.getcwd(),
                session.config.getoption(
                    "--iio-coverage-folder", "iio_coverage_results"
                ),
                "iio_coverage_report.md",
            )
            print(f"Generating markdown report at {full_path}")
            gen_markdown_table(all_systems_tracked, full_path)
            print("IIO coverage tracking finished")
        else:
            print("No IIO coverage tracking was set up")


@pytest.fixture(scope="function")
def iio_uri(request, _iio_emu_func):
    """URI fixture which provides a string of the target uri of the
    found board filtered by iio_hardware marker. If no hardware matching
    the required hardware is found, the test is skipped. If no iio_hardware
    marker is applied, first context uri is returned. If list of hardware
    markers are provided, the first matching is returned.
    """
    if isinstance(_iio_emu_func, dict):
        get_telemetry_data(request, _iio_emu_func, before_test=True)
        # Start coverage tracking
        if request.config.getoption("--iio-coverage"):
            c_name = _iio_emu_func["hw"]
            tracker = request.config.pytest_libiio.coverage_tracker
            if c_name not in tracker.trackers:
                tracker.add_instance(c_name, _iio_emu_func["uri"])
            tracker.set_tracker(c_name)
        yield _iio_emu_func["uri"]
        get_telemetry_data(request, _iio_emu_func, before_test=False)
    else:
        return False


@pytest.fixture(scope="function")
def single_ctx_desc(request, _contexts):
    """Contexts description fixture which provides a single dictionary of
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
    """Contexts description fixture which provides a list of dictionaries of
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


@pytest.fixture(scope="function")
def _iio_emu_func(request, _contexts, _iio_emu):
    marker = request.node.get_closest_marker("iio_hardware")
    if _contexts:
        if not marker or not marker.args:
            return _contexts[0]
        hardware = marker.args[0]
        eskip = marker.args[1] if len(marker.args) > 1 else False

        if eskip and request.config.getoption("--emu"):
            pytest.skip("Test not valid in emulation mode")
            return

        hardware = hardware if isinstance(hardware, list) else [hardware]
        if not marker:
            return _contexts[0]
        else:
            for dec in _contexts:
                if dec["hw"] == marker.args[0]:
                    return handle_iio_emu(dec, request, _iio_emu)
            for dec in _contexts:
                if dec["hw"] in marker.args[0]:
                    return handle_iio_emu(dec, request, _iio_emu)
    pytest.skip("No required hardware found")


@pytest.fixture(scope="session", autouse=True)
def _iio_emu(request, worker_id):
    """Initialization emulation fixture"""
    if request.config.getoption("--emu"):
        if worker_id == "master":
            custom_port = None
        else:
            worker_id = worker_id.replace("gw", "")
            custom_port = IIO_EMU_BASE_PORT + int(worker_id)
            logger = logging.getLogger()
            logger.info(f"Using custom port {custom_port}")

        exml = request.config.getoption("--emu-xml")
        if exml:
            if not os.path.exists(exml):
                raise Exception(f"{exml} not found")

            emu = iio_emu_manager(xml_path=exml, auto=False, custom_port=custom_port)
            emu.start()
            yield emu
            emu.stop()
            return

        # Get list of all devices available to emulate
        map = get_hw_map(request)
        if not map:
            raise Exception("No hardware map selected (ex: --adi-hw-map)")
        hw_w_emulation = {}
        for hw in map:
            for field in map[hw]:
                if isinstance(field, dict) and "emulate" in field:
                    hw_w_emulation[hw] = field
            if hw in hw_w_emulation:
                devices = []
                for field in map[hw]:
                    if isinstance(field, str):
                        devices.append(field)
                hw_w_emulation[hw]["devices"] = devices

        emu = iio_emu_manager(xml_path="auto", auto=True, custom_port=custom_port)
        emu.hw = hw_w_emulation

        yield emu
        emu.stop()
    else:
        yield None


@pytest.fixture(scope="session")
def _contexts(request, _iio_emu):
    """Contexts fixture which provides a list of dictionaries of found boards"""
    map = get_hw_map(request)
    uri = request.config.getoption("--uri")

    if _iio_emu:
        if _iio_emu.auto:
            ctx_plus_hw = []
            for hw in _iio_emu.hw:
                ctx_plus_hw.append(
                    {
                        "uri": _iio_emu.uri,
                        "type": "emu",
                        "devices": _iio_emu.hw[hw]["devices"],
                        "hw": hw,
                    }
                )
            return ctx_plus_hw
        else:
            uri = _iio_emu.uri

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

    return find_contexts(request.config, map, request)


@pytest.fixture(scope="session", autouse=True)
def cleanup_ssh_sessions():
    yield
    if hasattr(pytest, "hw_telemetry_ssh_sessions"):
        for uri in pytest.hw_telemetry_ssh_sessions:
            if pytest.hw_telemetry_ssh_sessions[uri]:
                print(f"Closing SSH session for URI {uri}")
                pytest.hw_telemetry_ssh_sessions[uri].close()


@pytest.fixture(scope="session", autouse=True)
def save_telemtry_logs_to_files(request):
    yield

    if hasattr(pytest, "hw_telemetry"):
        folder = request.config.getoption("--telm-data-folder")
        if not os.path.exists(folder):
            os.makedirs(folder)
        for uri in pytest.hw_telemetry:
            print(f"Saving telemetry data for URI {uri} to {folder}")
            for test in pytest.hw_telemetry[uri]:
                filename = f"{folder}/{test}.pkl"
                with open(filename, "wb") as f:
                    pickle.dump(pytest.hw_telemetry[uri][test], f)


def get_telemetry_data(request, ctx, before_test=True):
    if not request.config.getoption("--telm"):
        return

    if not hasattr(pytest, "hw_telemetry"):
        pytest.hw_telemetry = {}

    if not hasattr(pytest, "hw_telemetry_ssh_sessions"):
        pytest.hw_telemetry_ssh_sessions = {}

    ctx_o = iio.Context(ctx["uri"])
    ssh_sessions = pytest.hw_telemetry_ssh_sessions

    if ctx["uri"] not in ssh_sessions:
        if request.config.getoption("--emu"):
            ssh_sessions[ctx["uri"]] = None
        else:
            ssh_sessions[ctx["uri"]] = meta.get_ssh_session(ctx_o)

    metadata = meta.get_hardware_info(ctx_o, ssh_sessions[ctx["uri"]])
    msg = "before" if before_test else "after"
    print(f"\nCollecting telemetry data {msg} test for URI {ctx['uri']}")

    if ctx["uri"] not in pytest.hw_telemetry:
        pytest.hw_telemetry[ctx["uri"]] = {}

    if request.node.name not in pytest.hw_telemetry[ctx["uri"]]:
        pytest.hw_telemetry[ctx["uri"]][request.node.name] = {}

    if before_test:
        pytest.hw_telemetry[ctx["uri"]][request.node.name]["before_test"] = metadata
    else:
        pytest.hw_telemetry[ctx["uri"]][request.node.name]["after_test"] = metadata


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


def find_contexts(config, map, request):
    if request.config.getoption("--skip-scan"):
        ctxs = None
    else:
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
            print(string)

        try:
            ctx = iio.Context(uri)
        except Exception as ex:
            if ex.errno == 16:
                print(f"\nContext {uri} is not reachable: {ex}")
                continue
            raise ex

        if config.getoption("--scan-verbose"):
            devices = []
            for dev in ctx.devices:
                name = dev.name
                if name:
                    devices.append(name)
                else:
                    devices.append(dev.id)

            if not devices:
                print("\tNo devices found")
            else:
                string = f"\tDevices: {', '.join(devices)}"
                string += f"\n\tMapped to: {lookup_hw_from_map(ctx, map)}"
                print(string)

        ctx_plus_hw = {
            "uri": uri,
            "type": type,
            "devices": devices,
            "hw": lookup_hw_from_map(ctx, map),
        }
        ctxs_plus_hw.append(ctx_plus_hw)
    else:
        if config.getoption("--scan-verbose"):
            print("\nNo libiio contexts found")

    return ctxs_plus_hw
