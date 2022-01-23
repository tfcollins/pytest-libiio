from glob import glob
import iio
from jinja2 import Environment, FileSystemLoader
import os
import glob
import yaml


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
            v = print(at.value)
        except:
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
                v = print(at.value)
            except:
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


def render_template_mkdocs(devices):
    template_filename = "mkdocs.tmpl"
    output_filename = "mkdocs.yml"

    # Import template
    loc = os.path.dirname(__file__)
    loc = os.path.join(loc, "_templates")
    file_loader = FileSystemLoader(loc)
    env = Environment(loader=file_loader)

    loc = os.path.join(template_filename)
    template = env.get_template(loc)
    output = template.render(xmls=devices)

    loc = os.path.dirname(__file__)
    output_filename = os.path.join(loc, "..", output_filename)

    with open(output_filename, "w") as f:
        f.write(output)


def parse_all_library_context(root=None):

    if not root:
        loc = os.path.dirname(__file__)
        loc = os.path.join(loc, "..", "pytest_libiio", "resources", "devices")

    cfgs = parse_hw_map()

    xmls = {}
    for cfg in cfgs:
        file = os.path.join(loc, cfgs[cfg])
        print(file)
        fn = os.path.split(file)[-1]
        ctx = iio.XMLContext(file)
        devices = {}
        for dev in ctx.devices:
            device_info = parse_device(dev)
            path = render_template(device_info, cfg + "_" + device_info["name"])
            devices[device_info["name"]] = path

        xmls[cfg] = devices
    render_template_mkdocs(xmls)


if __name__ == "__main__":
    parse_all_library_context()