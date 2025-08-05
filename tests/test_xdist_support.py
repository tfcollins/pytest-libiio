"""Tests for verifying plugin works with pytest-xdist."""

import logging

import iio

import pytest

# Create file logger
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
# fh = logging.FileHandler('/tmp/test_xdist_support.log')
# fh.setLevel(logging.INFO)
# logger.addHandler(fh)


@pytest.mark.iio_hardware("fmcomms2")
def test_fmcomms2_xdist(iio_uri):
    print(f"iio_uri: {iio_uri}")
    logging.info(f"iio_uri: {iio_uri}")

    ctx = iio.Context(iio_uri)
    for dev in ctx.devices:
        print(f"dev: {dev.name}, {dev.id}")
        logging.info(f"dev: {dev.name}, {dev.id}")


@pytest.mark.iio_hardware("ad9081")
def test_ad9081_xdist(iio_uri):
    print(f"iio_uri: {iio_uri}")
    logging.info(f"iio_uri: {iio_uri}")

    ctx = iio.Context(iio_uri)
    for dev in ctx.devices:
        print(f"dev: {dev.name}, {dev.id}")
        logging.info(f"dev: {dev.name}, {dev.id}")
