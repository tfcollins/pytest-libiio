import types

import pytest

import pytest_libiio.meta as meta


class ValueObj:
    def __init__(self, value):
        self.value = value


class MaybeFailAttr:
    def __init__(self, value=None, fail=False):
        self.value = value
        self.fail = fail

    @property
    def value(self):
        if getattr(self, "fail", False):
            raise OSError("boom")
        return self._value

    @value.setter
    def value(self, v):
        self._value = v


class FakeChannel:
    def __init__(self, attrs):
        self.attrs = attrs


class FakeDevice:
    def __init__(self):
        self.attrs = {
            "dev_ok": ValueObj("dev-value"),
            "dev_err": MaybeFailAttr(fail=True),
        }
        self.debug_attrs = {
            "dbg_ok": ValueObj("dbg-value"),
            "dbg_err": MaybeFailAttr(fail=True),
        }
        self.buffer_attrs = {
            "buf_ok": ValueObj("buf-value"),
            "buf_err": MaybeFailAttr(fail=True),
        }
        self.in_channel = FakeChannel(
            {"ch_ok": ValueObj("ch-value"), "ch_err": MaybeFailAttr(fail=True)}
        )
        self.out_channel = FakeChannel({"out_ok": ValueObj("out-value")})

    def find_channel(self, name, is_output):
        if is_output:
            return self.out_channel
        return self.in_channel


class FakeContext:
    def __init__(self, xml):
        self.xml = xml
        self.attrs = {
            "uri": "ip:127.0.0.1",
            "hw_model": "DemoBoard",
            "ctx_ok": ValueObj("ctx-value"),
        }
        self.dev = FakeDevice()

    def find_device(self, name):
        return self.dev


def test_dprint_respects_debug_env(monkeypatch, capsys):
    monkeypatch.setenv("DEBUG", "1")
    meta.dprint("hello")
    assert "hello" in capsys.readouterr().out

    monkeypatch.delenv("DEBUG", raising=False)
    meta.dprint("quiet")
    assert "quiet" not in capsys.readouterr().out


def test_get_emulated_context_populates_attribute_values():
    xml = """
    <context name='ctx'>
      <context-attribute name='ctx_ok'/>
      <device id='dev0' name='dev0'>
        <attribute name='dev_ok'/>
        <attribute name='dev_err'/>
        <channel id='ch0' type='input' name='ch0'>
          <scan-element index='0' format='le:s16/16'/>
          <attribute name='ch_ok'/>
          <attribute name='ch_err'/>
          <attribute name='no_attr'/>
        </channel>
        <channel id='ch1' type='output' name='ch1'>
          <attribute name='out_ok'/>
        </channel>
        <debug-attribute name='dbg_ok'/>
        <debug-attribute name='dbg_err'/>
        <buffer-attribute name='buf_ok'/>
        <buffer-attribute name='buf_err'/>
      </device>
    </context>
    """
    out = meta.get_emulated_context(FakeContext(xml))

    assert "ctx-value" in out
    assert "dev-value" in out
    assert "ERROR" in out
    assert "NO ATTRS FOR CHANNEL" in out
    assert "<!DOCTYPE context" in out


def test_get_emulated_context_unknown_types_raise():
    bad_channel = """
    <context>
      <device id='dev0'>
        <channel id='c0' type='weird'><attribute name='a'/></channel>
      </device>
    </context>
    """
    with pytest.raises(Exception, match="Unknown channel type"):
        meta.get_emulated_context(FakeContext(bad_channel))

    bad_device_item = """
    <context>
      <device id='dev0'>
        <oops name='x'/>
      </device>
    </context>
    """
    with pytest.raises(Exception, match="Unknown device item"):
        meta.get_emulated_context(FakeContext(bad_device_item))

    bad_root = "<context><oops/></context>"
    with pytest.raises(Exception, match="Unknown item"):
        meta.get_emulated_context(FakeContext(bad_root))


def test_get_ssh_session_branches(monkeypatch, capsys):
    class Ctx:
        attrs = {"uri": "serial:/dev/ttyUSB0"}

    monkeypatch.setattr(meta, "useSSH", False)
    assert meta.get_ssh_session(Ctx()) is None
    assert "Paramiko is not installed" in capsys.readouterr().out

    class FakeSSH:
        def __init__(self):
            self.connected = None
            self.policy = None

        def set_missing_host_key_policy(self, policy):
            self.policy = policy

        def connect(self, ip, username, password):
            self.connected = (ip, username, password)

    class FakeParamiko:
        SSHClient = FakeSSH
        AutoAddPolicy = object()

    monkeypatch.setattr(meta, "useSSH", True)
    monkeypatch.setattr(meta, "paramiko", FakeParamiko)

    class IPCtx:
        attrs = {"uri": "ip:10.0.0.2"}

    ssh = meta.get_ssh_session(IPCtx())
    assert isinstance(ssh, FakeSSH)
    assert ssh.connected == ("10.0.0.2", "root", "analog")

    assert meta.get_ssh_session(Ctx()) is None
    assert "not supported for SSH telemetry" in capsys.readouterr().out


def test_get_hardware_info_with_and_without_ssh(monkeypatch):
    class Ctx:
        attrs = {"uri": "ip:1.2.3.4"}

    monkeypatch.setattr(meta, "get_emulated_context", lambda ctx: "<ctx/>")
    monkeypatch.setattr(meta.iio, "version", (0, 23, "x"))

    class FakeOut:
        def __init__(self, data):
            self._data = data

        def read(self):
            return self._data

    class FakeSSH:
        def exec_command(self, command):
            return None, FakeOut(f"out:{command}".encode()), None

    info_no_ssh = meta.get_hardware_info(Ctx(), None)
    assert info_no_ssh["local"]["libiio"] == (0, 23, "x")
    assert info_no_ssh["remote"]["iio_context"] == "<ctx/>"
    assert "dmesg" not in info_no_ssh["remote"]

    info_with_ssh = meta.get_hardware_info(Ctx(), FakeSSH())
    assert "out:dmesg" in info_with_ssh["remote"]["dmesg"]
    assert "out:iio_info" in info_with_ssh["remote"]["iio_info"]
