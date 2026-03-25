# Fixtures

pytest-libiio provides three public fixtures for accessing libiio hardware contexts in tests.
All fixtures integrate with the `@pytest.mark.iio_hardware` marker to filter contexts by
hardware name, and skip the test automatically when no matching hardware is found.

---

## `iio_uri`

**Scope:** function

Returns a URI string for the first matching hardware context. If no context matches the
`@pytest.mark.iio_hardware` marker (or no hardware is detected at all), the test is skipped.

When `--iio-coverage` is passed, this fixture starts per-test attribute coverage tracking
automatically. When `--telm` is passed, telemetry collection is started and stopped around
the test body.

**Returns:** `str` — a libiio URI such as `"ip:192.168.1.1"` or `"usb:1.2.3"`

**Example:**

```python
import pytest
import iio


@pytest.mark.iio_hardware(["adrv9361", "pluto"])
def test_identify_device(iio_uri):
    ctx = iio.Context(iio_uri)
    assert ctx is not None
```

---

## `single_ctx_desc`

**Scope:** function

Returns a single context-description dict for the first matching hardware context.
The test is skipped if no matching context is found.

**Returns:** `dict` — see [Context dict schema](#context-dict-schema) below.

**Example:**

```python
import pytest
import iio


@pytest.mark.iio_hardware("adrv9361")
def test_device_drivers(single_ctx_desc):
    ctx = iio.Context(single_ctx_desc["uri"])
    assert single_ctx_desc["hw"] == "adrv9361"
    assert "ad9361-phy" in single_ctx_desc["devices"]
```

---

## `context_desc`

**Scope:** function

Returns a list of all matching context-description dicts. This is useful when multiple
boards of the same type are connected simultaneously. The test is skipped if no matching
contexts are found.

**Returns:** `list[dict]` — each element follows the [Context dict schema](#context-dict-schema).

**Example — multi-board pattern:**

```python
import pytest
import iio


@pytest.mark.iio_hardware("fmcomms2")
def test_all_boards(context_desc):
    for ctx_d in context_desc:
        ctx = iio.Context(ctx_d["uri"])
        phy = ctx.find_device("ad9361-phy")
        assert phy is not None
```

---

## `@pytest.mark.iio_hardware` marker

The marker controls which hardware a test requires. It is optional — without it, `context_desc`
returns all found contexts and no filtering is applied.

| Usage | Behaviour |
|---|---|
| `@pytest.mark.iio_hardware("pluto")` | Accept only contexts whose `hw` key equals `"pluto"` |
| `@pytest.mark.iio_hardware(["pluto", "adrv9361"])` | Accept contexts matching any name in the list |
| `@pytest.mark.iio_hardware("pluto", True)` | Second arg `True` disables the test when running under `--emu` |

**Single hardware name:**

```python
@pytest.mark.iio_hardware("pluto")
def test_pluto_only(iio_uri):
    ctx = iio.Context(iio_uri)
    ...
```

**Accept any of a list:**

```python
@pytest.mark.iio_hardware(["pluto", "adrv9361"])
def test_pluto_or_adrv(iio_uri):
    ctx = iio.Context(iio_uri)
    ...
```

**Disable during emulation:**

```python
@pytest.mark.iio_hardware("pluto", True)
def test_real_hw_only(iio_uri):
    # This test is skipped when --emu is used
    ctx = iio.Context(iio_uri)
    ...
```

---

## Context dict schema

Each context-description dict returned by `context_desc` and `single_ctx_desc` contains:

| Key | Type | Example | Description |
|---|---|---|---|
| `uri` | `str` | `"ip:192.168.1.1"` | libiio connection URI |
| `type` | `str` | `"ip"` | Context transport type |
| `devices` | `str` | `"ad9361-phy,cf-ad9361-lpc"` | Comma-separated IIO driver names found in the context |
| `hw` | `str` | `"adrv9361"` | Hardware name resolved from the hardware map |
