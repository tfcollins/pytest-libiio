#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import os

from setuptools import setup


def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding="utf-8").read()


setup(
    name="pytest-libiio",
    version="0.0.4",
    author="Travis F. Collins",
    author_email="travis.collins@analog.com",
    maintainer="Travis F. Collins",
    maintainer_email="travis.collins@analog.com",
    license="BSD-3",
    url="https://github.com/tfcollins/pytest-libiio",
    description="A pytest plugin to manage interfacing with libiio contexts",
    long_description=read("README.rst"),
    packages=["pytest_libiio"],
    package_data={"pytest_libiio": ["resources/*"]},
    python_requires=">=3.5",
    install_requires=["pytest>=3.5.0", "pylibiio>=0.21", "pyyaml"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: Pytest",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: BSD License",
    ],
    include_package_data=True,
    entry_points={"pytest11": ["libiio = pytest_libiio.plugin"]},
)
