from click.testing import CliRunner

from pytest_libiio.tools import gen_xml


class DummyContext:
    pass


def test_gen_xml_prints_to_stdout(monkeypatch):
    monkeypatch.setattr("pytest_libiio.tools.iio.Context", lambda uri: DummyContext())
    monkeypatch.setattr(
        "pytest_libiio.tools.meta.get_emulated_context", lambda ctx: "<xml/>"
    )

    result = CliRunner().invoke(gen_xml, ["--uri", "ip:1.2.3.4"])

    assert result.exit_code == 0
    assert "<xml/>" in result.output


def test_gen_xml_writes_output_file(tmp_path, monkeypatch):
    out = tmp_path / "ctx.xml"

    monkeypatch.setattr("pytest_libiio.tools.iio.Context", lambda uri: DummyContext())
    monkeypatch.setattr(
        "pytest_libiio.tools.meta.get_emulated_context", lambda ctx: "<context/>"
    )

    result = CliRunner().invoke(gen_xml, ["--uri", "ip:1.2.3.4", "--xml", str(out)])

    assert result.exit_code == 0
    assert out.read_text() == "<context/>"


def test_gen_xml_raises_when_context_creation_fails(monkeypatch):
    monkeypatch.setattr("pytest_libiio.tools.iio.Context", lambda uri: None)

    result = CliRunner().invoke(gen_xml, ["--uri", "ip:1.2.3.4"])

    assert result.exit_code != 0
    assert "Failed to create IIO context" in str(result.exception)
