import iio

import click
import pytest_libiio.meta as meta


@click.command()
@click.option("--uri", "-u", help="URI of the device to connect to", required=True)
@click.option("--xml", "-x", help="XML file to write output to")
def gen_xml(uri, xml):
    """Generate IIO XML context file from device"""
    ctx = iio.Context(uri)
    if not ctx:
        raise Exception("Failed to create IIO context")
    xml_str = meta.get_emulated_context(ctx)
    if xml:
        with open(xml, "w") as f:
            f.write(xml_str)
    else:
        print(xml_str)
