# Fixtures

pytest-libiio provides a set of fixtures that can be used to find and utilize libiio contexts.

### Accessing contexts

Pass a list of context descriptions of all found during scan

``` python
  import pytest
  import iio


  def test_libiio_device(context_desc):
      hardware = ["pluto", "adrv9361", "fmcomms2"]
      for ctx_desc in context_desc:
          if ctx_desc["hw"] in hardware:
              ctx = iio.Context(ctx_desc["uri"])
      if not ctx:
          pytest.skip("No required hardware found")
```


Require certain hardware through marks

``` python
  import pytest
  import iio


  @pytest.mark.iio_hardware("adrv9361")
  def test_libiio_device(context_desc):
      for ctx_desc in context_desc:
          ctx = iio.Context(ctx_desc["uri"])
          ...
```


Pass the first URI of the first matching context found with the desired hardware

``` python
  import pytest
  import iio


  @pytest.mark.iio_hardware(["adrv9361","pluto"])
  def test_libiio_device(iio_uri):
        ctx = iio.Context(iio_uri)
          ...
```

Disable during emulation

``` python
  import pytest
  import iio


  @pytest.mark.iio_hardware("pluto", True)
  def test_libiio_device(iio_uri):
        ctx = iio.Context(iio_uri)
          ...
```
