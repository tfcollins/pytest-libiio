import importlib
import sys
import types

from click.testing import CliRunner


def import_tools_with_fake_iio(monkeypatch, context_factory):
    fake_iio = types.ModuleType("iio")
    fake_iio.Context = context_factory
    fake_meta = types.ModuleType("pytest_libiio.meta")
    fake_meta.get_emulated_context = lambda ctx: "<xml/>"
    monkeypatch.setitem(sys.modules, "iio", fake_iio)
    monkeypatch.setitem(sys.modules, "pytest_libiio.meta", fake_meta)
    sys.modules.pop("pytest_libiio.tools", None)
    return importlib.import_module("pytest_libiio.tools")


def test_gen_xml_prints_to_stdout(monkeypatch):
    class FakeContext:
        def __init__(self, uri):
            self.uri = uri

    tools = import_tools_with_fake_iio(monkeypatch, FakeContext)
    monkeypatch.setattr(
        tools.meta, "get_emulated_context", lambda ctx: "<xml>abc</xml>"
    )

    runner = CliRunner()
    result = runner.invoke(tools.gen_xml, ["--uri", "ip:1.2.3.4"])

    assert result.exit_code == 0
    assert "<xml>abc</xml>" in result.output


def test_gen_xml_writes_file(monkeypatch, tmp_path):
    class FakeContext:
        def __init__(self, uri):
            self.uri = uri

    tools = import_tools_with_fake_iio(monkeypatch, FakeContext)
    monkeypatch.setattr(
        tools.meta, "get_emulated_context", lambda ctx: "<xml>to-file</xml>"
    )

    out_file = tmp_path / "ctx.xml"
    runner = CliRunner()
    result = runner.invoke(
        tools.gen_xml,
        ["--uri", "ip:1.2.3.4", "--xml", str(out_file)],
    )

    assert result.exit_code == 0
    assert out_file.read_text() == "<xml>to-file</xml>"


def test_gen_xml_raises_when_context_creation_fails(monkeypatch):
    tools = import_tools_with_fake_iio(monkeypatch, lambda uri: None)

    runner = CliRunner()
    result = runner.invoke(tools.gen_xml, ["--uri", "ip:1.2.3.4"])

    assert result.exit_code != 0
    assert str(result.exception) == "Failed to create IIO context"
