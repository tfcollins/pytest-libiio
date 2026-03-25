import os
from glob import glob

import iio
import yaml
from jinja2 import Environment, FileSystemLoader


def parse_hw_map(map_filename=None):

    if not map_filename:
        loc = os.path.dirname(__file__)
        loc = os.path.join(loc, "..", "pytest_libiio", "resources")
        map_filename = os.path.join(loc, "adi_hardware_map.yml")

    with open(map_filename, "r") as stream:
        map = yaml.safe_load(stream)

    vconfigs = {}
    for cfg in map:
        for item in map[cfg]:

            if "emulate" in item:
                esettings = item["emulate"]
                for setting in esettings:
                    print(setting)
                    if "filename" in setting:
                        vconfigs[cfg] = setting["filename"]
    return vconfigs


def parse_device(dev: iio.Device):
    device_info = {}
    dev_attributes = {}
    chan_attributes = {}

    device_info["name"] = dev.name if dev.name else dev.id

    for attr in dev.attrs:
        at = dev.attrs[attr]
        fn = at.filename
        try:
            print(at.value)
            v = str(at.value)
        except Exception:
            v = ""
        dev_attributes[at.name] = {"filename": fn, "value": v}

    device_info["device_attributes"] = dev_attributes

    for chan in dev.channels:
        cn = chan.name if chan.name else chan.id
        channel = {}
        for attr in chan.attrs:
            at = chan.attrs[attr]
            fn = at.filename
            try:
                print(at.value)
                v = str(at.value)
            except Exception:
                v = ""
            channel[at.name] = {"filename": fn, "value": v}

        chan_attributes[cn] = channel

    device_info["channel_attributes"] = chan_attributes

    return device_info


def render_template(dev_info, output_filename):
    template_filename = "iio_device.tmpl"

    # Import template
    loc = os.path.dirname(__file__)
    loc = os.path.join(loc, "_templates")
    file_loader = FileSystemLoader(loc)
    env = Environment(loader=file_loader)

    loc = os.path.join(template_filename)
    template = env.get_template(loc)
    output = template.render(device=dev_info)

    output_filename = os.path.join("devices", output_filename + ".md")
    print("Rendering:", output_filename)
    with open(output_filename, "w") as f:
        f.write(output)

    return output_filename


def render_devices_index(xmls):
    """Write docs/devices/index.md with a MyST toctree for all generated device pages."""
    lines = ["# Emulated Driver Contexts\n", "\n"]
    lines.append("```{toctree}\n")
    lines.append(":maxdepth: 1\n")
    lines.append("\n")
    for hw_name in sorted(xmls.keys()):
        for _dev_name, path in xmls[hw_name].items():
            # path is like "devices/pluto_ad9361-phy.md" — strip the dir and extension
            basename = os.path.splitext(os.path.basename(path))[0]
            lines.append(f"{basename}\n")
    lines.append("```\n")

    output_path = os.path.join("devices", "index.md")
    print("Rendering:", output_path)
    with open(output_path, "w") as f:
        f.writelines(lines)


def parse_all_library_context(root=None):

    if not root:
        loc = os.path.dirname(__file__)
        loc = os.path.join(loc, "..", "pytest_libiio", "resources", "devices")

    cfgs = parse_hw_map()

    xmls = {}
    for cfg in cfgs:
        file = os.path.join(loc, cfgs[cfg])
        print(file)
        ctx = iio.XMLContext(file)
        devices = {}
        for dev in ctx.devices:
            device_info = parse_device(dev)
            path = render_template(device_info, cfg + "_" + device_info["name"])
            devices[device_info["name"]] = path

        xmls[cfg] = devices
    render_devices_index(xmls)


if __name__ == "__main__":
    parse_all_library_context()
