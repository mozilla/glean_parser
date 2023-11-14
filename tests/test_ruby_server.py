# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from pathlib import Path
import io
import json
import pytest
import subprocess

import glean_parser
from glean_parser import translate
from glean_parser import validate_ping

ROOT = Path(__file__).parent


def test_parser_rb_server_ping_file(tmpdir, capsys):
    """Test that no files are generated if ping definition
    is provided."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        [
            ROOT / "data" / "server_metrics_with_event.yaml",
            ROOT / "data" / "ruby_server_pings.yaml",
        ],
        "ruby_server",
        tmpdir,
    )
    captured = capsys.readouterr()
    assert all(False for _ in tmpdir.iterdir())
    assert (
        "Ping definition found. Server-side environment is simplified" in captured.out
    )


def test_parser_rb_server_no_event_metrics(tmpdir, capsys):
    """Test that no files are generated if no event metrics."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        [ROOT / "data" / "ruby_server_no_events.yaml"],
        "ruby_server",
        tmpdir,
    )
    captured = capsys.readouterr()
    assert all(False for _ in tmpdir.iterdir())
    assert (
        "No event metrics found...at least one event metric is required" in captured.out
    )


def test_parser_rb_server_metrics_unsupported_type(tmpdir, capsys):
    """Test that no files are generated with unsupported metric types."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        [
            ROOT / "data" / "ruby_server_metrics_unsupported.yaml",
        ],
        "ruby_server",
        tmpdir,
    )
    captured = capsys.readouterr()
    assert "Ignoring unsupported metric type" in captured.out
    assert "boolean" in captured.out


def test_parser_rb_server_pings_unsupported_type(tmpdir, capsys):
    """Test that no files are generated with ping types that are not `events`."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        [
            ROOT / "data" / "ruby_server_pings_unsupported.yaml",
        ],
        "ruby_server",
        tmpdir,
    )
    captured = capsys.readouterr()
    assert "Non-events ping reference found" in captured.out
    assert "Ignoring the tests ping type" in captured.out


def test_parser_rb_server(tmpdir):
    """Test that parser works"""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        [ROOT / "data" / "server_metrics_with_event.yaml"],
        "ruby_server",
        tmpdir,
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["server_events.rb"])

    # Make sure string metric made it in
    with (tmpdir / "server_events.rb").open("r", encoding="utf-8") as fd:
        content = fd.read()
        with (ROOT / "data" / "server_events_compare.rb").open(
            "r", encoding="utf-8"
        ) as cd:
            compare_raw = cd.read()
    compare = compare_raw.format(
        current_version=f"glean_parser v{glean_parser.__version__}"
    )
    assert content == compare


def run_logger(code_dir, import_file, code):
    """
    Run the Ruby logger with a mocked logger
    that just prints the ping payload to STDOUT.
    """

    tmpl_code = ""
    with open(ROOT / "test-rb" / "test.rb.tmpl", "r") as fp:
        tmpl_code = fp.read()

    tmpl_code = tmpl_code.replace("/* IMPORT */", import_file).replace(
        "/* CODE */", code
    )

    with open(code_dir / "test.rb", "w") as fp:
        fp.write(tmpl_code)

    return subprocess.check_output(["ruby", "test.rb"], cwd=code_dir).decode("utf-8")


@pytest.mark.ruby_dependency
def test_run_logging(tmpdir):
    tmpdir = Path(str(tmpdir))

    translate.translate(
        [
            ROOT / "data" / "server_metrics_with_event.yaml",
        ],
        "ruby_server",
        tmpdir,
    )

    code = """
events.backend_object_update.record(
    object_type: "type",
    object_state: "state",
    identifiers_fxa_account_id: nil,
    user_agent: "glean-test/1.0",
    ip_address: "127.0.0.1"
)
    """

    logged_output = run_logger(tmpdir, "server_events.rb", code)
    logged_output = json.loads(logged_output)
    fields = logged_output["Fields"]
    payload = fields["payload"]

    assert "glean-server-event" == logged_output["Type"]
    assert "glean.test" == fields["document_namespace"]
    assert "events" == fields["document_type"]
    assert "1" == fields["document_version"]
    assert "glean-test/1.0" == fields["user_agent"]

    schema_url = (
        "https://raw.githubusercontent.com/mozilla-services/"
        "mozilla-pipeline-schemas/main/"
        "schemas/glean/glean/glean.1.schema.json"
    )

    input = io.StringIO(payload)
    output = io.StringIO()
    assert (
        validate_ping.validate_ping(input, output, schema_url=schema_url) == 0
    ), output.getvalue()
