# Command Line Parameters

The pytest-libiio plugin extends the pytest cli with a few options to help with debugging tests, accessing specific hardware, and adding hardware maps between drivers and tests.


### Available CLI options

```
$ pytest -h
...
libiio:
  --uri=URI             Set libiio URI to utilize
  --scan-verbose        Print info of found contexts when scanning
  --adi-hw-map          Use ADI hardware map to determine hardware names based on context drivers
  --custom-hw-map=HW_MAP
                        Path to custom hardware map for drivers
  --hw=HW_SELECT        Define hardware name of provided URI. Will ignore scan information and requires input URI
                        argument
...
```

### URI

When **--uri=<input uri\>** is used, scanning is skipped and that URI is checked for a context. The URI can be in any form supported by the installed version of libiio:

- **Network:** ip:192.168.2.1
- **USB:** usb:1.2.3 or usb:
- **Local:** local:
- **Serial:** serial:/dev/ttyUSB0,115200

When a URI is not supplied a scan is performed and all found contexts are used to determine which tests to enable.

### Hardware maps

pytest-libiio allows tests to be filtered based on markers with specific hardware maps. These maps are essentially a list of IIO device names and attributes which make up or identify a specific platform or board. These are defined in a yaml file which will have contents similar to the one below:

``` yaml
pluto:
  - adm1177
  - ad9361-phy
  - cf-ad9361-lpc,2
pluto_rev_c:
  - ad9361-phy
  - cf-ad9361-lpc,2
  - ctx_attr:
    - hw_model: Analog Devices PlutoSDR Rev.C
fmcomms5:
  - ad9361-phy
  - ad9361-phy-b
  - cf-ad9361-lpc,8
```

These are arranged in the form:
``` yaml
<platform name>:
  - <driver 1>,<number of channels of driver 1 (optional)>
  - <driver 2>,<number of channels of driver 2 (optional)>
  - ctx_attr:
    - <context attribute name>: <value>
...
```

When the decorator **@pytest.mark.iio_hardware(hardware)** is used, any tests using this decorator will be used where **hardware** is a string or list of strings that match anything in the hardware map. Otherwise the test is filtered. Note that contexts must be found with matching hardware for the test to not be filtered as well.

By default, all devices are labeled as unknown if no map exists or they are not found in the current map. If the decorator is not used, the test will not be filtered based on these criteria.

When the flag **--adi-hw-map** is used the provided map from [plugin itself is used](https://github.com/tfcollins/pytest-libiio/blob/master/pytest_libiio/resources/adi_hardware_map.yml). Alternatively, a custom map can be used by supply the path with **--custom-hw-map=<path to yaml\>**.

If the flag **--hw=<hardware name>** is used the hardware map is ignored and the provided URI is defined as that hardware. This is handy if you do not want to create a custom map or are debugging. Note that **--hw** is only applicable when **--uri** is also used.
