# pytest-libiio

<p align="center">
<img src="https://raw.githubusercontent.com/analogdevicesinc/libiio/master/doc/html/img/iio_logo.png" width="400" alt="libiio Logo"> </br>
</p>

<p align="center">
<a href="https://pypi.org/project/pytest-libiio">
<img alt="PyPI version" src="https://img.shields.io/pypi/v/pytest-libiio.svg">
</a>
<a href="https://pypi.org/project/pytest-libiio">
<img alt="Python versions" src="https://img.shields.io/pypi/pyversions/pytest-libiio.svg">
</a>
<a href="https://travis-ci.org/tfcollins/pytest-libiio">
<img alt="See Build Status on Travis CI" src="https://travis-ci.org/tfcollins/pytest-libiio.svg?branch=master">
</a>
<a href="https://coveralls.io/github/tfcollins/pytest-libiio?branch=master">
<img alt="See Coverage Status on Coveralls" src="https://coveralls.io/repos/github/tfcollins/pytest-libiio/badge.svg?branch=master">
</a>
</p>

pytest-libiio is pytest plugin to manage interfacing with libiio contexts. This plugin is handy for leveraging the (new) zeroconf features of libiio to find, filter, and map libiio contexts to tests. It was created for [pyadi-iio](https://pypi.org/project/pyadi-iio/) testing but is used in other applications that need an organized way to handle libiio contexts without hardcoding URIs or lots of boilerplate code.

### Requirements

* [libiio](https://github.com/analogdevicesinc/libiio) and [pylibiio](https://pypi.org/project/pylibiio/)
    - Install with [zeroconf support](https://github.com/analogdevicesinc/libiio/blob/master/README_BUILD.md) to enable scanning
* pytest
* pyyaml

Optional for emulation support:

* [libtinyiiod](https://github.com/analogdevicesinc/libtinyiiod) and [iio-emu](https://github.com/analogdevicesinc/iio-emu)
* [paramiko](https://pypi.org/project/paramiko/) for additional metadata collection. Use the optional *ssh* argument when installing the package to get this automatically.
  * `pip install pytest-libiio[ssh]`


For [development the following are also needed](https://github.com/tfcollins/pytest-libiio/blob/master/requirements_dev.txt):

* tox
* pytest-mock
* pre-commit
* isort
* flake8
* codespell
* black


### Installation

You can install **pytest-libiio** via __pip__ from **PyPI**:

    $ pip install pytest-libiio

### Usage

Please see the [CLI](cli.md) and [fixtures](fixtures.md) sections for information about using the plugin.

### Future ideas

Mock testing is common with libiio's python library since hardware is needed otherwise. In future releases, we hope to extend features in pytest-mock through this plugin to make mocking libiio more streamlined.

### Contributing

Contributions are very welcome. Tests can be run with **tox**, please ensure
the coverage at least stays the same before you submit a pull request.

### License

Distributed under the terms of the [BSD-3 license](https://github.com/tfcollins/pytest-libiio/blob/master/LICENSE), **pytest-libiio** is free and open source software


###Issues

If you encounter any problems, please [file an issue](https://github.com/tfcollins/pytest-libiio/issues) along with a detailed description.
