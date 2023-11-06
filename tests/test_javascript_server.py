# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from pathlib import Path
import io
import json
import pytest
import shutil
import subprocess

from glean_parser import javascript_server
from glean_parser import translate
from glean_parser import validate_ping


ROOT = Path(__file__).parent


def test_parser_js_server_ping_no_metrics(tmpdir):
    """Test that no files are generated if only ping definitions
    are provided without any metrics."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "fxa-server-pings.yaml",
        "javascript_server",
        tmpdir,
    )

    assert all(False for _ in tmpdir.iterdir())


def test_parser_js_server_metrics_no_ping(tmpdir):
    """Test that no files are generated if only metric definitions
    are provided without pings."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "fxa-server-metrics.yaml",
        "javascript_server",
        tmpdir,
    )

    assert all(False for _ in tmpdir.iterdir())


def test_parser_js_server(tmpdir):
    """Test that no files are generated if only metric definitions
    are provided without pings."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        [
            ROOT / "data" / "fxa-server-pings.yaml",
            ROOT / "data" / "fxa-server-metrics.yaml",
        ],
        "javascript_server",
        tmpdir,
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["server_events.js"])

    # Make sure string metric made it in
    with (tmpdir / "server_events.js").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "'event.name': event_name" in content


def test_generate_ping_factory_method():
    ping = "accounts_events"
    expected_result = "createAccountsEventsEvent"
    result = javascript_server.generate_ping_factory_method(
        ping, event_metric_exists=False
    )
    assert result == expected_result

    ping = "accounts_events"
    expected_result = "createAccountsEventsServerEventLogger"
    result = javascript_server.generate_ping_factory_method(
        ping, event_metric_exists=True
    )
    assert result == expected_result


def run_logger(code_dir, import_file, factory, code):
    """
    Run the JavaScript logger with a mocked logger
    that just prints the ping payload to STDOUT.
    """

    shutil.copy(ROOT / "test-js" / "package.json", code_dir)
    subprocess.check_call(["npm", "install"], cwd=code_dir)

    tmpl_code = ""
    with open(ROOT / "test-js" / "test.js.tmpl", "r") as fp:
        tmpl_code = fp.read()

    tmpl_code = (
        tmpl_code.replace("/* IMPORT */", import_file)
        .replace("/* FACTORY */", factory)
        .replace("/* CODE */", code)
    )

    with open(code_dir / "test.js", "w") as fp:
        fp.write(tmpl_code)

    return subprocess.check_output(["node", "test.js"], cwd=code_dir).decode("utf-8")


@pytest.mark.node_dependency
def test_run_logging(tmpdir):
    tmpdir = Path(str(tmpdir))

    translate.translate(
        [
            ROOT / "data" / "fxa-server-pings.yaml",
            ROOT / "data" / "fxa-server-metrics.yaml",
        ],
        "javascript_server",
        tmpdir,
    )

    factory = "createAccountsEventsEvent"
    code = """
events.record({ user_agent: "glean-test/1.0", event_name: "testing" });
    """

    logged_output = run_logger(tmpdir, "server_events.js", factory, code)
    logged_output = json.loads(logged_output)
    fields = logged_output["Fields"]
    payload = fields["payload"]

    assert "glean-server-event" == logged_output["Type"]
    assert "glean.test" == fields["document_namespace"]
    assert "accounts-events" == fields["document_type"]
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
