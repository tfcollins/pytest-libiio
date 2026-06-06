# pytest Command Line Parameters

The pytest-libiio plugin extends the pytest cli with a few options to help with
debugging tests, accessing specific hardware, and adding hardware maps between
drivers and tests.


## Available CLI options

| Flag | Default | Description |
|---|---|---|
| `--uri=URI` | _(scan)_ | Skip the scan and use this libiio URI directly. See [URI](#uri). |
| `--scan-verbose` | off | Print details of every discovered context during scanning. |
| `--adi-hw-map` | off | Use the bundled [ADI hardware map](https://github.com/tfcollins/pytest-libiio/blob/main/pytest_libiio/resources/adi_hardware_map.yml). See [Hardware maps](#hardware-maps). |
| `--custom-hw-map=PATH` | _(none)_ | Path to a custom hardware map YAML. See [Hardware maps](#hardware-maps). |
| `--hw=NAME` | _(none)_ | Treat the `--uri` target as this hardware name, ignoring the map. Requires `--uri`. |
| `--skip-scan` | off | Skip the Zeroconf/avahi scan. Typically used in CI together with `--uri` or `--emu`. |
| `--emu` | off | Launch [iio-emu](https://github.com/analogdevicesinc/iio-emu) and run tests against the emulator. See [Emulation](emulation.md) and [Scenario: emulation mode](fixtures.md#scenario-emulation-mode). |
| `--emu-xml=PATH` | _(auto)_ | Path or name of an iio-emu XML to load. Without it, XML files are picked from the hardware map. |
| `--emu-xml-dir=DIR` | _(bundled)_ | Override the directory that holds emulator XML files (defaults to `pytest_libiio/resources/devices`). |
| `--telm` | off | Capture before/after telemetry for every test that uses `iio_uri`. See [Telemetry](#telemetry). |
| `--telm-data-folder=DIR` | `telm_data` | Folder for telemetry pickle files. |
| `--iio-coverage` | off | Track IIO attribute reads/writes across the session. See [Coverage tracking](#coverage-tracking). |
| `--iio-coverage-folder=DIR` | `iio_coverage_results` | Folder for per-context coverage JSON + the aggregated markdown report. |
| `--iio-coverage-debug-props` | off | Also track IIO debug attributes. |
| `--iio-coverage-print-results` | off | Print the per-context attribute map to stdout after the session. |

## URI

When **--uri=<input uri\>** is used, scanning is skipped and that URI is checked for a context. The URI can be in any form supported by the installed version of libiio:

- **Network:** ip:192.168.2.1
- **USB:** usb:1.2.3 or usb:
- **Local:** local:
- **Serial:** serial:/dev/ttyUSB0,115200

When a URI is not supplied a scan is performed and all found contexts are used to determine which tests to enable.

## Hardware maps

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

## Telemetry

When the flag **--telm** is used, hardware telemetry is collected on each test. This enables a fixture that is autouse, meaning it is automatically used by all tests. The telemetry is collected in a folder defined by **--telm-data-folder=<path\>**. The folder is created if it does not exist. Telemetry data is stored in individual files that are specific to a URI. So after a test suite run there should one file for every hardware platform under test. The test files are generated at pickle files and contain different metadata. This is primarily just IIO based information. However, if the optional SSH dependency is installed, additional metadata is collected from the target hardware if it uses an IP context.

For a worked example see [Scenario: telemetry capture](fixtures.md#scenario-telemetry-capture).

## Coverage tracking

When **--iio-coverage** is set, pytest-libiio monkey-patches both
`iio.ChannelAttr` and `iio.DeviceAttr` to record every attribute read and write
performed by your tests, grouped by the matched hardware context. Both
device-level attributes and per-channel attributes are tracked by default. The
`iio_uri` fixture installs the per-context tracker automatically — no per-test
plumbing is required.

After the session finishes the plugin writes:

- One `<hw>_coverage.json` file per context with the raw per-attribute counts,
  split into `device_attr_reads_writes` and `channel_attr_reads_writes`
  sections (plus `debug_attr_reads_writes` when **--iio-coverage-debug-props**
  is set).
- One `iio_coverage_report.md` aggregating coverage percentages across all
  contexts, with a row per system for `device_coverage`, `channel_coverage`,
  and `total_coverage`.

Both land in the directory named by **--iio-coverage-folder** (default
`iio_coverage_results`). Pass **--iio-coverage-print-results** to also dump the
per-context attribute map to stdout, or **--iio-coverage-debug-props** to
include debug attributes in the tally.

For a worked example see [Scenario: attribute coverage](fixtures.md#scenario-attribute-coverage).
