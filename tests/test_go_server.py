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


def test_parser_go_server_ping_no_metrics(tmp_path, capsys):
    """Test that no files are generated if only ping definitions
    are provided without any metrics."""
    translate.translate(
        ROOT / "data" / "server_pings.yaml",
        "go_server",
        tmp_path,
    )
    assert all(False for _ in tmp_path.iterdir())


def test_parser_go_server_metrics_unsupported_type(tmp_path, capsys):
    """Test that no files are generated with unsupported metric types."""
    translate.translate(
        [
            ROOT / "data" / "go_server_metrics_unsupported.yaml",
        ],
        "go_server",
        tmp_path,
    )
    captured = capsys.readouterr()
    assert "Ignoring unsupported metric type" in captured.out
    unsupported_types = [
        "boolean",
        "labeled_boolean",
        "labeled_string",
        "string_list",
        "timespan",
        "uuid",
        "url",
    ]
    for t in unsupported_types:
        assert t in captured.out


def test_parser_go_server_events_only(tmp_path):
    """Test that parser works for definitions that only use events ping"""
    translate.translate(
        ROOT / "data" / "go_server_events_only_metrics.yaml",
        "go_server",
        tmp_path,
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(["server_events.go"])

    # Make sure generated file matches expected
    with (tmp_path / "server_events.go").open("r", encoding="utf-8") as fd:
        content = fd.read()
        with (ROOT / "data" / "server_events_only_compare.go").open(
            "r", encoding="utf-8"
        ) as cd:
            compare_raw = cd.read()

    glean_version = f"glean_parser v{glean_parser.__version__}"
    # use replace instead of format since Go uses { }
    compare = compare_raw.replace("{current_version}", glean_version)
    assert content == compare


def test_parser_go_server_events_and_custom_ping(tmp_path):
    """Test that parser works for definitions that use events ping and custom pings"""
    translate.translate(
        [
            ROOT / "data" / "go_server_events_and_custom_ping_metrics.yaml",
            ROOT / "data" / "go_server_events_and_custom_ping_pings.yaml"
        ],
        "go_server",
        tmp_path,
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(["server_events.go"])

    # Make sure generated file matches expected
    with (tmp_path / "server_events.go").open("r", encoding="utf-8") as fd:
        content = fd.read()
        with (ROOT / "data" / "server_events_and_custom_ping_compare.go").open(
            "r", encoding="utf-8"
        ) as cd:
            compare_raw = cd.read()

    glean_version = f"glean_parser v{glean_parser.__version__}"
    # use replace instead of format since Go uses { }
    compare = compare_raw.replace("{current_version}", glean_version)
    assert content == compare


def test_parser_go_server_custon_ping_only(tmp_path):
    """Test that parser works for definitions that only use custom pings"""
    translate.translate(
        [
            ROOT / "data" / "go_server_custom_ping_only_metrics.yaml",
            ROOT / "data" / "go_server_custom_ping_only_pings.yaml"
        ],
        "go_server",
        tmp_path,
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(["server_events.go"])

    # Make sure generated file matches expected
    with (tmp_path / "server_events.go").open("r", encoding="utf-8") as fd:
        content = fd.read()
        with (ROOT / "data" / "server_custom_ping_only_compare.go").open(
            "r", encoding="utf-8"
        ) as cd:
            compare_raw = cd.read()

    glean_version = f"glean_parser v{glean_parser.__version__}"
    # use replace instead of format since Go uses { }
    compare = compare_raw.replace("{current_version}", glean_version)
    assert content == compare


def run_logger(code_dir, code):
    """
    Run the Go logger and capture the output sent to STDOUT.
    """

    tmpl_code = ""
    with open(ROOT / "test-go" / "test.go.tmpl", "r") as fp:
        tmpl_code = fp.read()

    tmpl_code = tmpl_code.replace("/* CODE */", code)

    with open(code_dir / "test.go", "w") as fp:
        fp.write(tmpl_code)

    subprocess.call(["go", "mod", "init", "glean"], cwd=code_dir)
    subprocess.call(["go", "mod", "tidy"], cwd=code_dir)

    return subprocess.check_output(["go", "run", "test.go"], cwd=code_dir).decode(
        "utf-8"
    )


@pytest.mark.go_dependency
def test_run_logging_events_ping(tmp_path):
    glean_module_path = tmp_path / "glean"

    translate.translate(
        [
            ROOT / "data" / "go_server_events_only_metrics.yaml",
        ],
        "go_server",
        glean_module_path,
    )

    code = """
    logger.RecordEventBackendTestEvent(
        glean.RequestInfo{
            UserAgent: "glean-test/1.0",
            IpAddress: "127.0.0.1",
        },
        glean.EventBackendTestEvent{
            MetricName:            "string value",
            MetricRequestBool:     true,
            MetricRequestCount:    10,
            MetricRequestDatetime: time.Now(),
            EventFieldString:      "event extra string value",
            EventFieldQuantity:    100,
            EventFieldBool:        false,
        },
    )
    """

    logged_output = run_logger(tmp_path, code)
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


@pytest.mark.go_dependency
def test_run_logging_custom_ping(tmp_path):
    glean_module_path = tmp_path / "glean"

    translate.translate(
        [
            ROOT / "data" / "go_server_custom_ping_only_metrics.yaml",
            ROOT / "data" / "go_server_custom_ping_only_pings.yaml"
        ],
        "go_server",
        glean_module_path,
    )

    code = """
    logger.RecordPingServerTelemetryScenarioOne(
        glean.RequestInfo{
            UserAgent: "glean-test/1.0",
            IpAddress: "127.0.0.1",
        },
        glean.PingServerTelemetryScenarioOne{
            MetricName:            "string value",
            MetricRequestBool:     true,
            MetricRequestCount:    20,
            MetricRequestDatetime: time.Now(),
        },
    )
    """

    logged_output = run_logger(tmp_path, code)
    logged_output = json.loads(logged_output)
    fields = logged_output["Fields"]
    payload = fields["payload"]

    assert "glean-server-event" == logged_output["Type"]
    assert "glean.test" == fields["document_namespace"]
    assert "server-telemetry-scenario-one" == fields["document_type"]
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
