# Emulation

By leveraging [iio-emu](https://github.com/analogdevicesinc/iio-emu) hardware or contexts can be emulated for testing without physical devices. However, currently this emulation does not validate attribute rates, states of drivers, or equivalent data sources. This feature should be used to test a library itself rather than hardware drivers.

## Set up

To use device emulation you will need [libtinyiiod](https://github.com/analogdevicesinc/libtinyiiod) and [iio-emu](https://github.com/analogdevicesinc/iio-emu) libraries installed. **pytest-libiio** will take care of managing the *iio-emu* server automatically for you. **iio-emu** will also provide additional utilities incase XML need to be created for new devices.


## Adding device support

Emulating hardware is done through a XML file generated from an existing hardware set up and pointing the tool [xml_gen](https://github.com/analogdevicesinc/iio-emu/blob/master/GENERIC_EMULATOR.md) to the target context:

```bash
xml_gen ip:pluto.local > pluto.xml
```

This XML file can be manually used with **pytest-libiio** by leveraging the *--emu-xml* flag as so:

```bash
pytest --emu --emu-xml=pluto.xml
```

This will launch a server when testing is started with a device matching the provided context description in XML form.

### Device library

**pytest-libiio** does ship with a number of built-in XML files for different devices. When the flag *--emu* is used without *--emu-xml* these will be dynamically loaded based on different required hardware as defined by pytest markers.

However, since not all tests work with emulated hardware there is a input available to the test markers to mark tests to not run when in emulation mode. This would work as follows:

``` python
import pytest
import iio


@pytest.mark.iio_hardware("pluto", True)  # Set True disables test during emulation
def test_libiio_device(iio_uri):
    ctx = iio.Context(iio_uri)
    ...
```

When adding new devices to the library itself, they must be defined in the hardware map. The default one is the *[adi_hardware_map.yml](https://github.com/tfcollins/pytest-libiio/blob/master/pytest_libiio/resources/adi_hardware_map.yml)*. To define the device the name of the XML file must be provided along with which drivers interface with data (TX or RX drivers). Here is an example:

```yaml
pluto_rev_c:
  - ad9361-phy
  - cf-ad9361-lpc,2
  - ctx_attr:
    - hw_model: Analog Devices PlutoSDR Rev.C
  - emulate:
    - filename: pluto.xml
    - data_devices:
        - iio:device2
        - iio:device3
ad9081:
  - axi-ad9081-tx-hpc
  - axi-ad9081-rx-hpc
  - emulate:
    - filename: ad9081.xml
    - data_devices:
        - iio:device1
        - iio:device2
```

Note that the *data_devices* with names device* are the generic IIO driver names of the DMA drivers for TX and RX.
