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

## Scenario: emulation mode

Pass `--emu` together with `--adi-hw-map` to run tests against an
[iio-emu](https://github.com/analogdevicesinc/iio-emu) server instead of real
hardware. The plugin starts and stops `iio-emu` automatically based on the
hardware map and the markers on collected tests. `iio_uri` returns the
emulator's URI (e.g. `ip:127.0.0.1:30432` for an xdist worker).

```bash
pytest --emu --adi-hw-map
```

Tests that cannot be exercised under emulation (e.g. tests that depend on real
sample rates or signal paths) can opt out with the second marker argument:

```python
import iio
import pytest


@pytest.mark.iio_hardware("pluto", True)  # True = skip when --emu is active
def test_real_pluto(iio_uri):
    ctx = iio.Context(iio_uri)
    ...
```

See [Emulation](emulation.md) for details on adding new device XML files.

---

## Scenario: attribute coverage

When `--iio-coverage` is passed, `iio_uri` activates a per-context
[attribute coverage tracker](https://github.com/tfcollins/pytest-libiio/blob/main/pytest_libiio/coverage.py)
that records every IIO attribute read or written during the test session via a
monkey-patch on `iio.ChannelAttr`. No change to your test code is required.

```bash
pytest --emu --adi-hw-map --iio-coverage --iio-coverage-folder=cov_out
```

After the session finishes the plugin writes one `<hw>_coverage.json` file per
context plus an aggregated `iio_coverage_report.md` into the coverage folder
(default `iio_coverage_results/`). Pass `--iio-coverage-print-results` to also
dump the per-context attribute map to stdout, or `--iio-coverage-debug-props`
to track debug attributes too.

---

## Scenario: telemetry capture

With `--telm`, the `iio_uri` fixture wraps each test with a before/after
telemetry snapshot of the target hardware. Snapshots are pickled per test into
`--telm-data-folder` (default `telm_data/`). When `pytest-libiio` is installed
with the `[ssh]` extra and the URI is an IP context, additional metadata is
collected over SSH.

```bash
pytest --uri ip:pluto.local --telm --telm-data-folder=telm_out
```

```
telm_out/
├── test_capture_loopback.pkl
└── test_set_rx_lo.pkl
```

Each pickle is a dict shaped `{"before_test": {...}, "after_test": {...}}`
with IIO context, device, and (optionally) SSH-collected metadata.

---

## Scenario: parallel execution with pytest-xdist

Tests that request the same `iio_uri` must run sequentially per board — two
parallel writers will fight over a single piece of hardware. The plugin
handles this automatically: during collection it stamps every
`@pytest.mark.iio_hardware`-marked test with
`xdist_group(name=f"xdist_{uri}")`, so `pytest-xdist`'s `--dist=loadgroup`
routes all tests for a given URI to a single worker.

```bash
pytest --adi-hw-map -n auto --dist=loadgroup
```

Under `--emu`, each xdist worker also gets its own iio-emu port allocated from
`IIO_EMU_BASE_PORT = 30431 + worker_index`, so multiple workers can emulate
independently without colliding.

---

## API reference

The following docstrings are extracted directly from `pytest_libiio.plugin`:

```{eval-rst}
.. autofunction:: pytest_libiio.plugin.iio_uri

.. autofunction:: pytest_libiio.plugin.single_ctx_desc

.. autofunction:: pytest_libiio.plugin.context_desc
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
