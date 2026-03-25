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

.. image:: https://coveralls.io/repos/github/tfcollins/pytest-libiio/badge.svg?branch=master
    :target: https://coveralls.io/github/tfcollins/pytest-libiio?branch=master
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

This plugin is used to make the access of libiio contexts easier and to provide a unified API through fixtures.

Accessing contexts
^^^^^^^^^^^^^^^^^^

Get list of context descriptions of all found contexts:

.. code-block:: python

  import pytest
  import iio


  def test_libiio_device(context_desc):
      hardware = ["pluto", "adrv9361", "fmcomms2"]
      for ctx_desc in context_desc:
          if ctx_desc["hw"] in hardware:
              ctx = iio.Context(ctx_desc["uri"])
      if not ctx:
          pytest.skip("No required hardware found")

Require certain hardware through marks:

.. code-block:: python

  import pytest
  import iio


  @pytest.mark.iio_hardware("adrv9361")
  def test_libiio_device(context_desc):
      for ctx_desc in context_desc:
          ctx = iio.Context(ctx_desc["uri"])
          ...

Contributing
------------

Contributions are very welcome. Tests can be run with `nox`_, please ensure
the coverage at least stays the same before you submit a pull request.

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
