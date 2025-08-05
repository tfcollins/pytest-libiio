"""This is a set of function to help extract metadata from tests and hardware"""

import os
import re
import xml.etree.ElementTree as ET
from io import BytesIO, StringIO
from pprint import pprint

import iio

import lxml.etree as etree

try:
    import paramiko

    useSSH = True
except ImportError:
    useSSH = False


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
            if hasattr(ch, "attrs") and attr_name in ch.attrs:
                try:
                    value = ch.attrs[attr_name].value
                except OSError:
                    value = "ERROR"
            else:
                value = "NO ATTRS FOR CHANNEL"
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

    context_fields = list(root.attrib.keys())

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

    # Update context ATTLIST of DOCTYPE to include all context fields
    context_fields += ["description"]
    context_fields = list(set(context_fields))
    template = "<!ATTLIST context "
    context_fields_list = [
        f"{field.replace(',','').replace(' ','_')} CDATA #IMPLIED "
        for field in context_fields
    ]
    full = template + "".join(context_fields_list)
    full = f"{full[:-1]}>"

    doctype = f"<!DOCTYPE context [\n\
        <!ELEMENT context (device | context-attribute)*>\n\
        <!ELEMENT context-attribute EMPTY>\n\
        <!ELEMENT device (channel | attribute | debug-attribute | buffer-attribute)*>\n\
        <!ELEMENT channel (scan-element?, attribute*)>\n\
        <!ELEMENT attribute EMPTY><!ELEMENT scan-element EMPTY>\n\
        <!ELEMENT debug-attribute EMPTY>\n\
        <!ELEMENT buffer-attribute EMPTY>\n\
        {full}\n\
        <!ATTLIST context-attribute name CDATA #REQUIRED value CDATA #REQUIRED>\n\
        <!ATTLIST device id CDATA #REQUIRED name CDATA #IMPLIED>\n\
        <!ATTLIST channel id CDATA #REQUIRED type (input|output) #REQUIRED name CDATA #IMPLIED>\n\
        <!ATTLIST scan-element index CDATA #REQUIRED format CDATA #REQUIRED scale CDATA #IMPLIED>\n\
        <!ATTLIST attribute name CDATA #REQUIRED filename CDATA #IMPLIED value CDATA #IMPLIED>\n\
        <!ATTLIST debug-attribute name CDATA #REQUIRED value CDATA #IMPLIED>\n\
        <!ATTLIST buffer-attribute name CDATA #REQUIRED value CDATA #IMPLIED>\n\
    ]>"

    xml_str = ET.tostring(root, encoding="unicode")

    tree = etree.parse(StringIO(xml_str))
    xml_str = etree.tostring(
        tree, pretty_print=True, xml_declaration=True, doctype=doctype, encoding="utf-8"
    )
    xml_str = str(xml_str, "utf-8")  # type: ignore
    return xml_str


def get_ssh_session(ctx: iio.Context):
    """Get ssh session"""
    uri = ctx.attrs["uri"].split(":")
    if not useSSH:
        print("Paramiko is not installed, cannot use SSH")
        return None
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


def get_hardware_info(ctx: iio.Context, ssh=None):
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
    # root = get_hardware_info(ctx)
    root = get_emulated_context(ctx)
