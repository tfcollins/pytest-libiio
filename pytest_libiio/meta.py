"""This is a set of function to help extract metadata from tests and hardware"""

import iio
import os
import paramiko
from pprint import pprint
import xml.etree.ElementTree as ET


def convert_to_xml_method1(data_str):
    root = ET.fromstring(data_str)
    # return ET.tostring(root, encoding='unicode')
    return root


def __get_value_from_hw(
    ctx, attrib, ptype, attr_name, dev_name=None, ch_name=None, is_output=False
):
    if "value" in attrib:
        value = attrib["value"]
    else:
        if ptype == "context":
            value = ctx.attrs[attr_name].value
        elif ptype == "device":
            dev = ctx.find_device(str(dev_name))
            try:
                value = dev.attrs[attr_name].value
            except OSError:
                value = "ERROR"
        elif ptype == "channel":
            dev = ctx.find_device(str(dev_name))
            ch = dev.find_channel(str(ch_name), is_output)
            try:
                value = ch.attrs[attr_name].value
            except OSError:
                value = "ERROR"
        elif ptype == "debug":
            dev = ctx.find_device(str(dev_name))
            try:
                value = dev.debug_attrs[attr_name].value
            except OSError:
                value = "ERROR"
        elif ptype == "buffer":
            dev = ctx.find_device(str(dev_name))
            try:
                value = dev.buffer_attrs[attr_name].value
            except OSError:
                value = "ERROR"
        else:
            raise Exception("Unknown property type")

    return value


def __get_name_id(item):
    return item.attrib["name"] if "name" in item.attrib else item.attrib["id"]


def dprint(*args, **kwargs):
    """Debug print"""
    if os.environ.get("DEBUG"):
        print(*args, **kwargs)


def get_emulated_context(ctx: iio.Context):
    cxml = ctx.xml
    cxml = str(cxml)

    # Convert string to xml
    root = ET.fromstring(cxml)

    # loop through items
    for item in root:
        if item.tag == "context-attribute":
            dprint("Context-attribute---")
            attr_name_id = __get_name_id(item)
            value = __get_value_from_hw(ctx, item.attrib, "context", attr_name_id)
            dprint("CONTEXT", attr_name_id, value)
            item.attrib["value"] = value
        elif item.tag == "device":
            dprint("Device---")
            device_name_id = __get_name_id(item)
            # Devices
            for sitem in item:
                attr_name_id = __get_name_id(sitem)
                # Device attributes
                if sitem.tag == "attribute":
                    value = __get_value_from_hw(
                        ctx, sitem.attrib, "device", attr_name_id, device_name_id
                    )
                    dprint("DEVICE", device_name_id, attr_name_id, value)
                    sitem.attrib["value"] = value
                # Channel attributes
                elif sitem.tag == "channel":
                    channel_name_id = attr_name_id
                    if sitem.attrib["type"] == "output":
                        is_output = True
                    elif sitem.attrib["type"] == "input":
                        is_output = False
                    else:
                        raise Exception("Unknown channel type")
                    for ssitem in sitem:
                        if ssitem.tag == "scan-element":
                            continue  # FIXME
                        channel_attr_name_id = __get_name_id(ssitem)
                        value = __get_value_from_hw(
                            ctx,
                            ssitem.attrib,
                            "channel",
                            channel_attr_name_id,
                            device_name_id,
                            channel_name_id,
                            is_output,
                        )
                        dprint(
                            "CHANNEL",
                            device_name_id,
                            channel_name_id,
                            is_output,
                            channel_attr_name_id,
                            value,
                        )
                        ssitem.attrib["value"] = value

                elif sitem.tag == "debug-attribute":
                    value = __get_value_from_hw(
                        ctx, sitem.attrib, "debug", attr_name_id, device_name_id
                    )
                    dprint("DEBUG", device_name_id, attr_name_id, value)
                    sitem.attrib["value"] = value

                elif sitem.tag == "buffer-attribute":
                    value = __get_value_from_hw(
                        ctx, sitem.attrib, "buffer", attr_name_id, device_name_id
                    )
                    dprint("BUFFER", device_name_id, attr_name_id, value)
                    sitem.attrib["value"] = value
                else:
                    raise Exception("Unknown device item")
        else:
            raise Exception("Unknown item")

    xml_str = ET.tostring(root, encoding="unicode")

    return xml_str


def get_ssh_session(ctx: iio.Context):
    """Get ssh session"""
    uri = ctx.attrs["uri"].split(":")
    if uri[0] == "ip":
        print(f"Starting SSH session for uri: {ctx.attrs['uri']}")
        ip = uri[1]
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        ssh.connect(ip, username="root", password="analog")
        return ssh
    else:
        print(f"URI: {ctx.attrs['uri']} is not supported for SSH telemetry")
        return None


def get_hardware_info(ctx: iio.Context, ssh: paramiko.SSHClient = None):
    """Get hardware information from the context"""
    local = {}
    remote = {}

    local["libiio"] = iio.version

    # Get context xml and values from HW
    remote["iio_context"] = get_emulated_context(ctx)

    # Get telemetry data from remote linux system
    uri = ctx.attrs["uri"].split(":")
    if uri[0] == "ip" and ssh is not None:
        stdin, stdout, stderr = ssh.exec_command("dmesg")
        remote["dmesg"] = stdout.read().decode()
        stdin, stdout, stderr = ssh.exec_command("uname -a")
        remote["uname"] = stdout.read().decode()
        stdin, stdout, stderr = ssh.exec_command("cat /proc/cpuinfo")
        remote["cpuinfo"] = stdout.read().decode()
        stdin, stdout, stderr = ssh.exec_command("cat /proc/meminfo")
        remote["meminfo"] = stdout.read().decode()
        stdin, stdout, stderr = ssh.exec_command("cat /proc/version")
        remote["version"] = stdout.read().decode()
        stdin, stdout, stderr = ssh.exec_command("cat /etc/os-release")
        remote["os-release"] = stdout.read().decode()
        stdin, stdout, stderr = ssh.exec_command("df -h")
        remote["df"] = stdout.read().decode()
        stdin, stdout, stderr = ssh.exec_command(
            'python -c "import iio; print(iio.version)"'
        )
        remote["libiio"] = stdout.read().decode()
        stdin, stdout, stderr = ssh.exec_command("iio_info")
        remote["iio_info"] = stdout.read().decode()
        # ssh.close()

    metadata = {}
    metadata["local"] = local
    metadata["remote"] = remote

    return metadata


if __name__ == "__main__":
    ctx = iio.Context("ip:analog.local")
    root = get_hardware_info(ctx)
