=============
pytest-libiio
=============

.. image:: https://img.shields.io/pypi/v/pytest-libiio.svg
    :target: https://pypi.org/project/pytest-libiio
    :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/pytest-libiio.svg
    :target: https://pypi.org/project/pytest-libiio
    :alt: Python versions

.. image:: https://github.com/tfcollins/pytest-libiio/actions/workflows/test.yml/badge.svg
    :target: https://github.com/tfcollins/pytest-libiio/actions/workflows/test.yml
    :alt: See Build Status on GitHub Actions

.. image:: https://coveralls.io/repos/github/tfcollins/pytest-libiio/badge.svg?branch=main
    :target: https://coveralls.io/github/tfcollins/pytest-libiio?branch=main
    :alt: See Coverage Status on Coveralls

.. image:: https://github.com/tfcollins/pytest-libiio/actions/workflows/doc.yml/badge.svg
    :target: https://github.com/tfcollins/pytest-libiio/actions/workflows/doc.yml
    :alt: Documentation Build Status

A pytest plugin to manage interfacing with libiio contexts

----

pytest-libiio is pytest plugin to manage interfacing with libiio contexts. This plugin is handy for leveraging the zeroconf features of libiio to find, filter, and map libiio contexts to tests. It was created for `pyadi-iio <https://pypi.org/project/pyadi-iio/>`_ testing but is used in other applications that need an organized way to handle libiio contexts without hardcoding URIs or lots of boilerplate code.


Requirements
------------

* libiio and pylibiio
* pytest
* pyyaml

Optional for emulation support:

* `iio-emu <https://github.com/analogdevicesinc/iio-emu>`_

Optional for SSH telemetry collection:

* `paramiko <https://pypi.org/project/paramiko/>`_ (or install with ``pip install pytest-libiio[ssh]``)

For development the following are also needed:

* nox
* pytest-mock
* pre-commit
* ruff


Installation
------------

You can install "pytest-libiio" via `pip`_ from `PyPI`_::

    $ pip install pytest-libiio


Usage
-----

The plugin exposes three pytest fixtures — ``iio_uri``, ``single_ctx_desc``,
and ``context_desc`` — plus an ``iio_hardware`` marker that filters tests by
detected hardware. The full reference and scenario walkthroughs (emulation,
attribute coverage, telemetry, xdist) live in the
`hosted documentation <https://tfcollins.github.io/pytest-libiio/>`_.

Quickstart — get a URI for a marked board and open the context:

.. code-block:: python

  import iio
  import pytest


  @pytest.mark.iio_hardware("pluto")
  def test_pluto(iio_uri):
      ctx = iio.Context(iio_uri)
      assert ctx.find_device("ad9361-phy") is not None

Fan out across every matching board with ``context_desc``:

.. code-block:: python

  import iio
  import pytest


  @pytest.mark.iio_hardware(["pluto", "adrv9361", "fmcomms2"])
  def test_all_matching_boards(context_desc):
      for ctx_desc in context_desc:
          ctx = iio.Context(ctx_desc["uri"])
          ...

Run against the bundled ADI hardware map so the marker names resolve:

.. code-block:: bash

  pytest --adi-hw-map

Track how much of each context's IIO attributes your tests exercise with
``--iio-coverage``:

.. code-block:: bash

  pytest --adi-hw-map --iio-coverage

This records every device- and channel-level attribute read or written, then
writes a per-context JSON file plus an aggregate Markdown report. To keep noise
(diagnostic devices, unsupported attributes, etc.) out of the tally, add a
per-hardware ``ignore:`` section to the hardware map listing devices, channels,
or attributes to exclude (glob patterns supported):

.. code-block:: yaml

  pluto:
    - ad9361-phy
    - cf-ad9361-lpc,2
    - ignore:
        devices: [xadc]
        attributes:
          - {device: ad9361-phy, name: calib_mode_available}

Ignored items are dropped from both the access counts and the coverage
denominator. See the `coverage tracking docs
<https://tfcollins.github.io/pytest-libiio/cli.html#coverage-tracking>`_ for the
full schema.

Contributing
------------

Contributions are very welcome. Tests run via `nox`_ (``nox -s tests``);
please ensure coverage at least stays the same before submitting a pull
request.

License
-------

Distributed under the terms of the `BSD-3`_ license, "pytest-libiio" is free and open source software


Issues
------

If you encounter any problems, please `file an issue`_ along with a detailed description.

.. _`BSD-3`: http://opensource.org/licenses/BSD-3-Clause
.. _`file an issue`: https://github.com/tfcollins/pytest-libiio/issues
.. _`nox`: https://nox.thea.codes/en/stable/
.. _`pip`: https://pypi.org/project/pip/
.. _`PyPI`: https://pypi.org/project
