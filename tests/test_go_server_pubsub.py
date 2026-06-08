# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
Tests for the `go_server` outputter's Pub/Sub and combined transports
(`-s transport=pubsub` / `-s transport=combined`) and their runtime behavior.
"""

from pathlib import Path
import base64
import gzip
import io
import json
import pytest
import subprocess
import uuid

from glean_parser import translate
from glean_parser import validate_ping

ROOT = Path(__file__).parent

SCHEMA_URL = (
    "https://raw.githubusercontent.com/mozilla-services/"
    "mozilla-pipeline-schemas/main/"
    "schemas/glean/glean/glean.1.schema.json"
)

# YAML fixture lists shared across pubsub scenarios.
YAML_EVENTS_PING = ["go_server_events_only_metrics.yaml"]
YAML_CUSTOM_PING = [
    "go_server_custom_ping_only_metrics.yaml",
    "go_server_custom_ping_only_pings.yaml",
]


# Helpers


def _translate(glean_module_path, yaml_filenames, transport="pubsub"):
    """Translate the given YAML fixtures with the given go_server transport."""
    yaml_files = [ROOT / "data" / name for name in yaml_filenames]
    translate.translate(
        yaml_files, "go_server", glean_module_path, {"transport": transport}
    )


def _gofmt_parse_ok(path):
    """Syntax validation of generated Go code.

    go_server templates emit space-indented code which is valid
    Go but not gofmt-formatted, so we assert that gofmt can parse it
    (`gofmt -e` exits non-zero on a parse error).
    """
    result = subprocess.run(["gofmt", "-e", str(path)], capture_output=True, text=True)
    assert result.returncode == 0, (
        f"gofmt could not parse generated Go:\n{result.stderr}"
    )


def _run_publisher(code_dir, code, imports=""):
    """Compile and run the test Go program against an in-process Pub/Sub
    fake (pstest). Returns the captured messages as a list of
    {"data": base64, "attributes": dict}."""
    with open(ROOT / "test-go" / "test_publisher.go.tmpl", "r") as fp:
        tmpl_code = fp.read()
    tmpl_code = tmpl_code.replace("/* CODE */", code).replace("/* IMPORTS */", imports)

    with open(code_dir / "test.go", "w") as fp:
        fp.write(tmpl_code)

    subprocess.check_call(["go", "mod", "init", "glean"], cwd=code_dir)
    subprocess.check_call(["go", "mod", "tidy"], cwd=code_dir)

    out = subprocess.check_output(["go", "run", "test.go"], cwd=code_dir)
    return json.loads(out.decode("utf-8"))


def _validate_payload_against_schema(payload_bytes):
    """Validate the inner Glean ping JSON against the pipeline schema."""
    input = io.StringIO(payload_bytes.decode("utf-8"))
    output = io.StringIO()
    assert validate_ping.validate_ping(input, output, schema_url=SCHEMA_URL) == 0, (
        output.getvalue()
    )


# Code generation tests


def test_parser_pubsub_ping_no_metrics(tmp_path, capsys):
    """No files are generated if only ping definitions are provided
    without any metrics."""
    translate.translate(
        ROOT / "data" / "server_pings.yaml",
        "go_server",
        tmp_path,
        {"transport": "pubsub"},
    )
    assert all(False for _ in tmp_path.iterdir())


def test_parser_pubsub_metrics_unsupported_type(tmp_path, capsys):
    """No files are generated with unsupported metric types; warnings are
    emitted for each unsupported type."""
    translate.translate(
        [ROOT / "data" / "go_server_metrics_unsupported.yaml"],
        "go_server",
        tmp_path,
        {"transport": "pubsub"},
    )
    captured = capsys.readouterr()
    assert "Ignoring unsupported metric type" in captured.out
    unsupported_types = ["labeled_string", "timespan", "uuid", "url"]
    for t in unsupported_types:
        assert t in captured.out


def test_parser_pubsub_labeled_boolean_without_labels(tmp_path, capsys):
    """labeled_boolean without static labels is rejected."""
    translate.translate(
        [ROOT / "data" / "go_server_metrics_unsupported.yaml"],
        "go_server",
        tmp_path,
        {"transport": "pubsub"},
    )
    captured = capsys.readouterr()
    assert "Ignoring labeled_boolean metric without static labels" in captured.out


@pytest.mark.go_dependency
def test_parser_pubsub_labeled_boolean(tmp_path):
    """labeled_boolean metrics generate proper struct types."""
    translate.translate(
        ROOT / "data" / "go_server_labeled_boolean_metrics.yaml",
        "go_server",
        tmp_path,
        {"transport": "pubsub"},
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(["server_events.go"])

    with (tmp_path / "server_events.go").open("r", encoding="utf-8") as fd:
        content = fd.read()

    # The labeled_boolean struct type is generated.
    assert "type TelemetryFeatureFlags struct {" in content
    assert "FeatureOne *bool" in content
    assert "FeatureTwo *bool" in content
    assert "FeatureThree *bool" in content

    # ...and used in the ping struct.
    assert "TelemetryFeatureFlags TelemetryFeatureFlags" in content

    _gofmt_parse_ok(tmp_path / "server_events.go")


@pytest.mark.go_dependency
def test_parser_pubsub_generation(tmp_path):
    """The pubsub outputter generates a stateless GleanEventsBuilder, not a
    publisher with transport lifecycle.

    This guards the one thing the runtime test (test_run_record_pubsub)
    cannot: that we don't also emit unwanted but valid generated code. The
    runtime test exercises only the builder happy path, so a stray publisher
    struct, lifecycle methods, Prometheus instrumentation, or a MozLog
    envelope would compile and pass there unnoticed. Everything observable in
    the published message (attributes, gzipped body, document_id shape,
    absent submission_timestamp) is asserted in the runtime test instead, so
    we don't re-check it here."""
    translate.translate(
        ROOT / "data" / "go_server_events_only_metrics.yaml",
        "go_server",
        tmp_path,
        {"transport": "pubsub"},
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(["server_events.go"])

    with (tmp_path / "server_events.go").open("r", encoding="utf-8") as fd:
        content = fd.read()

    # Positive contract: a builder that returns *pubsub.Message.
    assert "type GleanEventsBuilder struct" in content
    assert "func (g GleanEventsBuilder) BuildEventsPingMessage(" in content
    assert "(*pubsub.Message, error)" in content

    # Negative: no other transport's shape
    assert "type GleanEventsPublisher struct" not in content
    assert "type GleanEventsLogger struct" not in content
    # No MozLog envelope (logging path) or envelope-ping wrapper
    assert "type logEnvelope struct" not in content
    assert "RecordEventsPing(" not in content

    _gofmt_parse_ok(tmp_path / "server_events.go")


# Runtime tests
#
# Each scenario builds a *pubsub.Message via the generated
# `Build<Ping>Message` method, publishes it via topic.Publish, and asserts
# the message arrives at the pstest fake. Routing fields live on the
# message's Attributes; the body is the inner Glean ping gzipped.

PUBSUB_SCENARIOS = {
    "events_ping": {
        "yaml": YAML_EVENTS_PING,
        "code": """
        msg, err := builder.BuildEventsPingMessage(
            glean.RequestInfo{
                UserAgent: "glean-test/1.0",
                IpAddress: "127.0.0.1",
            },
            glean.EventsPing{
                MetricName:              "string value",
                MetricRequestBool:       true,
                MetricRequestCount:      10,
                MetricRequestDatetime:   time.Now(),
                MetricRequestStringList: []string{"list", "of", "strings"},
                Event: glean.BackendTestEventEvent{
                    EventFieldString:   "event extra string value",
                    EventFieldQuantity: 100,
                    EventFieldBool:     false,
                },
            },
        )
        """,
        "expected_doc_type": "events",
        "expected_event_count": 1,
    },
    "custom_ping_without_event": {
        "yaml": YAML_CUSTOM_PING,
        "code": """
        msg, err := builder.BuildServerTelemetryScenarioOnePingMessage(
            glean.RequestInfo{
                UserAgent: "glean-test/1.0",
                IpAddress: "127.0.0.1",
            },
            glean.ServerTelemetryScenarioOnePing{
                MetricName:              "string value",
                MetricRequestBool:       true,
                MetricRequestCount:      20,
                MetricRequestDatetime:   time.Now(),
                MetricRequestStringList: []string{"list", "of", "strings"},
            },
        )
        """,
        "expected_doc_type": "server-telemetry-scenario-one",
        "expected_event_count": 0,
    },
    "custom_ping_with_event": {
        "yaml": YAML_CUSTOM_PING,
        "code": """
        msg, err := builder.BuildServerTelemetryScenarioOnePingMessage(
            glean.RequestInfo{
                UserAgent: "glean-test/1.0",
                IpAddress: "127.0.0.1",
            },
            glean.ServerTelemetryScenarioOnePing{
                MetricName:              "string value",
                MetricRequestBool:       true,
                MetricRequestCount:      20,
                MetricRequestDatetime:   time.Now(),
                MetricRequestStringList: []string{"list", "of", "strings"},
                Event: glean.BackendSpecialEventEvent{
                    EventFieldString:   "extra value string",
                    EventFieldQuantity: 30,
                    EventFieldBool:     true,
                },
            },
        )
        """,
        "expected_doc_type": "server-telemetry-scenario-one",
        "expected_event_count": 1,
    },
}


@pytest.mark.go_dependency
@pytest.mark.parametrize("scenario_name", list(PUBSUB_SCENARIOS))
def test_run_record_pubsub(tmp_path, scenario_name):
    """Build a Pub/Sub message and publish it via topic.Publish;
    Then assert the wire format on the captured message."""
    scenario = PUBSUB_SCENARIOS[scenario_name]
    glean_module_path = tmp_path / "glean"
    _translate(glean_module_path, scenario["yaml"])

    msgs = _run_publisher(tmp_path, scenario["code"])
    assert len(msgs) == 1, f"expected one published message, got {len(msgs)}"
    attrs = msgs[0]["attributes"]
    payload_bytes = gzip.decompress(base64.b64decode(msgs[0]["data"]))
    payload = json.loads(payload_bytes)

    # Pub/Sub attributes carry ping metadata.
    # submission_timestamp is set by the decoder from publishTime, not by the publisher.
    assert attrs["document_namespace"] == "glean.test"
    assert attrs["document_type"] == scenario["expected_doc_type"]
    assert attrs["document_version"] == "1"
    assert attrs["user_agent"] == "glean-test/1.0"
    assert attrs["x_forwarded_for"] == "127.0.0.1"
    parsed = uuid.UUID(attrs["document_id"])
    assert parsed.version == 4
    assert attrs["document_id"] == attrs["document_id"].lower()
    assert "submission_timestamp" not in attrs

    assert len(payload["events"]) == scenario["expected_event_count"]
    assert payload["client_info"]["app_display_version"] == "0.0.1"
    assert payload["client_info"]["app_channel"] == "nightly"

    _validate_payload_against_schema(payload_bytes)


@pytest.mark.go_dependency
def test_run_pubsub_nil_string_list(tmp_path):
    """Test that nil string_list metrics serialize as empty arrays, not null."""
    glean_module_path = tmp_path / "glean"
    _translate(glean_module_path, YAML_EVENTS_PING)

    code = """
        msg, err := builder.BuildEventsPingMessage(
            glean.RequestInfo{
                UserAgent: "glean-test/1.0",
                IpAddress: "127.0.0.1",
            },
            glean.EventsPing{
                MetricName:            "string value",
                MetricRequestBool:     true,
                MetricRequestCount:    10,
                MetricRequestDatetime: time.Now(),
                // MetricRequestStringList intentionally omitted (nil)
                Event: glean.BackendTestEventEvent{
                    EventFieldString:   "event extra string value",
                    EventFieldQuantity: 100,
                    EventFieldBool:     false,
                },
            },
        )
        """

    msgs = _run_publisher(tmp_path, code)
    assert len(msgs) == 1, f"expected one published message, got {len(msgs)}"
    payload_bytes = gzip.decompress(base64.b64decode(msgs[0]["data"]))
    payload = json.loads(payload_bytes)

    string_list_value = payload["metrics"]["string_list"]["metric.request_string_list"]
    assert string_list_value == [], (
        f"Expected empty array for nil string_list, got: {string_list_value}"
    )

    _validate_payload_against_schema(payload_bytes)


@pytest.mark.go_dependency
def test_run_combined_transport(tmp_path):
    """`transport=combined` emits both the logging Logger and the pubsub
    Builder into one package, sharing common types. This is what lets a server
    dual-write during a logging->pubsub migration. Assert both APIs coexist
    with shared types emitted once, then compile + publish via the builder to
    prove the combined package builds and the pubsub path still works."""
    glean_module_path = tmp_path / "glean"
    _translate(glean_module_path, YAML_EVENTS_PING, transport="combined")

    with (glean_module_path / "server_events.go").open("r", encoding="utf-8") as fd:
        content = fd.read()

    # Both transports' entry types and APIs are present in the single file.
    assert "type GleanEventsBuilder struct" in content
    assert "type GleanEventsLogger struct" in content
    assert "func (g GleanEventsBuilder) BuildEventsPingMessage(" in content
    assert "func (g GleanEventsLogger) RecordEventsPing(" in content
    # Shared types are emitted once, not duplicated across the two paths.
    # gofmt validates syntax but not duplicate declarations, so guard here.
    assert content.count("type clientInfo struct") == 1
    assert content.count("type pingInfo struct") == 1

    # The combined package compiles and the builder publishes a message.
    msgs = _run_publisher(tmp_path, PUBSUB_SCENARIOS["events_ping"]["code"])
    assert len(msgs) == 1, f"expected one published message, got {len(msgs)}"
    assert msgs[0]["attributes"]["document_type"] == "events"
