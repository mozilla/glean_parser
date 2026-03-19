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
        "labeled_string",
        "timespan",
        "uuid",
        "url",
    ]
    for t in unsupported_types:
        assert t in captured.out


def test_parser_go_server_labeled_boolean_without_labels(tmp_path, capsys):
    """Test that labeled_boolean without static labels is rejected."""
    translate.translate(
        [
            ROOT / "data" / "go_server_metrics_unsupported.yaml",
        ],
        "go_server",
        tmp_path,
    )
    captured = capsys.readouterr()
    assert "Ignoring labeled_boolean metric without static labels" in captured.out


def test_parser_go_server_labeled_boolean(tmp_path):
    """Test that labeled_boolean metrics generate proper struct types."""
    translate.translate(
        ROOT / "data" / "go_server_labeled_boolean_metrics.yaml",
        "go_server",
        tmp_path,
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(["server_events.go"])

    # Read generated file and verify struct is created
    with (tmp_path / "server_events.go").open("r", encoding="utf-8") as fd:
        content = fd.read()

        # Check that the labeled_boolean struct type was generated
        assert "type TelemetryFeatureFlags struct {" in content
        assert "FeatureOne *bool" in content
        assert "FeatureTwo *bool" in content
        assert "FeatureThree *bool" in content

        # Check that it's used in the ping struct
        assert "TelemetryFeatureFlags TelemetryFeatureFlags" in content


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
            ROOT / "data" / "go_server_events_and_custom_ping_pings.yaml",
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


def test_parser_go_server_custom_ping_only(tmp_path):
    """Test that parser works for definitions that only use custom pings"""
    translate.translate(
        [
            ROOT / "data" / "go_server_custom_ping_only_metrics.yaml",
            ROOT / "data" / "go_server_custom_ping_only_pings.yaml",
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


def run_logger(code_dir, code, imports=""):
    """
    Run the Go logger and capture the output sent to STDOUT.
    """

    tmpl_code = ""
    with open(ROOT / "test-go" / "test.go.tmpl", "r") as fp:
        tmpl_code = fp.read()

    tmpl_code = tmpl_code.replace("/* CODE */", code).replace("/* IMPORTS */", imports)

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
    logger.RecordEventsPing(
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
                EventFieldString:      "event extra string value",
                EventFieldQuantity:    100,
                EventFieldBool:        false,
            },
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
    assert validate_ping.validate_ping(input, output, schema_url=schema_url) == 0, (
        output.getvalue()
    )


@pytest.mark.go_dependency
def test_run_logging_custom_ping_without_event(tmp_path):
    glean_module_path = tmp_path / "glean"

    translate.translate(
        [
            ROOT / "data" / "go_server_custom_ping_only_metrics.yaml",
            ROOT / "data" / "go_server_custom_ping_only_pings.yaml",
        ],
        "go_server",
        glean_module_path,
    )

    code = """
    logger.RecordServerTelemetryScenarioOnePing(
        glean.RequestInfo{
            UserAgent: "glean-test/1.0",
            IpAddress: "127.0.0.1",
        },
        glean.ServerTelemetryScenarioOnePing{
            MetricName:             "string value",
            MetricRequestBool:       true,
            MetricRequestCount:      20,
            MetricRequestDatetime:   time.Now(),
            MetricRequestStringList: []string{"list", "of", "strings"},
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
    assert validate_ping.validate_ping(input, output, schema_url=schema_url) == 0, (
        output.getvalue()
    )


@pytest.mark.go_dependency
def test_run_logging_discard_writer(tmp_path):
    glean_module_path = tmp_path / "glean"

    translate.translate(
        [
            ROOT / "data" / "go_server_custom_ping_only_metrics.yaml",
            ROOT / "data" / "go_server_custom_ping_only_pings.yaml",
        ],
        "go_server",
        glean_module_path,
    )

    imports = """
    "io"
    "fmt"
    """

    code = """
    logger.Writer = io.Discard
    err := logger.RecordServerTelemetryScenarioOnePing(
        glean.RequestInfo{
            UserAgent: "glean-test/1.0",
            IpAddress: "127.0.0.1",
        },
        glean.ServerTelemetryScenarioOnePing{
            MetricName:             "string value",
            MetricRequestBool:       true,
            MetricRequestCount:      20,
            MetricRequestDatetime:   time.Now(),
            MetricRequestStringList: []string{"list", "of", "strings"},
        },
    )
    if err != nil {
        fmt.Println(err)
    }
    """

    # validate the code ran successfully and produced no output
    logged_output = run_logger(tmp_path, code, imports=imports)
    assert logged_output == ""


@pytest.mark.go_dependency
def test_run_logging_nil_writer(tmp_path):
    glean_module_path = tmp_path / "glean"

    translate.translate(
        [
            ROOT / "data" / "go_server_custom_ping_only_metrics.yaml",
            ROOT / "data" / "go_server_custom_ping_only_pings.yaml",
        ],
        "go_server",
        glean_module_path,
    )

    imports = """
    "fmt"
    """

    code = """
    logger.Writer = nil
    err := logger.RecordServerTelemetryScenarioOnePing(
        glean.RequestInfo{
            UserAgent: "glean-test/1.0",
            IpAddress: "127.0.0.1",
        },
        glean.ServerTelemetryScenarioOnePing{
            MetricName:            "string value",
            MetricRequestBool:     true,
            MetricRequestCount:    20,
            MetricRequestDatetime: time.Now(),
        },
    )
    if err != nil {
        fmt.Println(err)
    }
    """

    # validate only output produced is the printing of the returned error
    logged_output = run_logger(tmp_path, code, imports=imports)
    assert logged_output == "writer not specified\n"


@pytest.mark.go_dependency
def test_run_logging_labeled_boolean(tmp_path):
    glean_module_path = tmp_path / "glean"

    translate.translate(
        [
            ROOT / "data" / "go_server_labeled_boolean_metrics.yaml",
        ],
        "go_server",
        glean_module_path,
    )

    code = """
    _ = time.Now() // satisfy Go's unused import check for "time"
    t := true
    f := false
    logger.RecordEventsPing(
        glean.RequestInfo{
            UserAgent: "glean-test/1.0",
            IpAddress: "127.0.0.1",
        },
        glean.EventsPing{
            TelemetryFeatureFlags: glean.TelemetryFeatureFlags{
                FeatureOne:   &t,
                FeatureTwo:   &f,
                FeatureThree: nil, // valid label on metric but this request had no value for it
                // FeatureFour omitted to illustrate zero value behavior
            },
        },
    )
    """

    logged_output = run_logger(tmp_path, code)
    logged_output = json.loads(logged_output)
    fields = logged_output["Fields"]
    payload_str = fields["payload"]
    payload = json.loads(payload_str)

    assert "glean-server-event" == logged_output["Type"]
    assert "glean.test" == fields["document_namespace"]
    assert "events" == fields["document_type"]

    # Validate payload against Glean schema
    schema_url = (
        "https://raw.githubusercontent.com/mozilla-services/"
        "mozilla-pipeline-schemas/main/"
        "schemas/glean/glean/glean.1.schema.json"
    )

    input = io.StringIO(payload_str)
    output = io.StringIO()
    assert validate_ping.validate_ping(input, output, schema_url=schema_url) == 0, (
        output.getvalue()
    )

    # Check that labeled_boolean is properly serialized
    labeled_boolean_metrics = payload["metrics"]["labeled_boolean"]
    assert "telemetry.feature_flags" in labeled_boolean_metrics
    feature_flags = labeled_boolean_metrics["telemetry.feature_flags"]
    assert feature_flags["feature_one"] is True
    assert feature_flags["feature_two"] is False
    assert feature_flags.get("feature_three") is None
    assert feature_flags.get("feature_four") is None


@pytest.mark.go_dependency
def test_run_logging_labeled_boolean_omitted(tmp_path):
    """Test that completely omitted labeled_boolean metrics serialize correctly."""
    glean_module_path = tmp_path / "glean"

    translate.translate(
        [
            ROOT / "data" / "go_server_labeled_boolean_metrics.yaml",
        ],
        "go_server",
        glean_module_path,
    )

    # This code logs an events ping without setting the labeled_boolean metric at all, not even to nil.
    code = """
    _ = time.Now() // satisfy Go's unused import check for "time"
    logger.RecordEventsPing(
        glean.RequestInfo{
            UserAgent: "glean-test/1.0",
            IpAddress: "127.0.0.1",
        },
        glean.EventsPing{
            // TelemetryFeatureFlags completely omitted (zero value)
        },
    )
    """

    logged_output = run_logger(tmp_path, code)
    logged_output = json.loads(logged_output)
    fields = logged_output["Fields"]
    payload_str = fields["payload"]
    payload = json.loads(payload_str)

    assert "glean-server-event" == logged_output["Type"]
    assert "glean.test" == fields["document_namespace"]
    assert "events" == fields["document_type"]

    # Validate payload against Glean schema
    schema_url = (
        "https://raw.githubusercontent.com/mozilla-services/"
        "mozilla-pipeline-schemas/main/"
        "schemas/glean/glean/glean.1.schema.json"
    )

    input = io.StringIO(payload_str)
    output = io.StringIO()
    validation_result = validate_ping.validate_ping(
        input, output, schema_url=schema_url
    )

    assert validation_result == 0, f"Validation failed. Output: {output.getvalue()}"

    # Check how labeled_boolean is serialized when omitted
    labeled_boolean_metrics = payload["metrics"]["labeled_boolean"]
    assert "telemetry.feature_flags" in labeled_boolean_metrics
    feature_flags = labeled_boolean_metrics["telemetry.feature_flags"]
    # Verify it's an empty dict {}, not null
    assert feature_flags == {} or feature_flags is None


@pytest.mark.go_dependency
def test_run_logging_nil_string_list(tmp_path):
    """Test that nil string_list metrics serialize as empty arrays, not null."""
    glean_module_path = tmp_path / "glean"

    translate.translate(
        [
            ROOT / "data" / "go_server_events_and_custom_ping_metrics.yaml",
            ROOT / "data" / "go_server_events_and_custom_ping_pings.yaml",
        ],
        "go_server",
        glean_module_path,
    )

    code = """
    logger.RecordEventsPing(
        glean.RequestInfo{
            UserAgent: "glean-test/1.0",
            IpAddress: "127.0.0.1",
        },
        glean.EventsPing{
            MetricName:              "string value",
            MetricRequestBool:       true,
            MetricRequestCount:      10,
            MetricRequestDatetime:   time.Now(),
            // MetricRequestStringList intentionally omitted (nil)
            Event: glean.BackendTestEventEvent{
                EventFieldString:      "event extra string value",
                EventFieldQuantity:    100,
                EventFieldBool:        false,
            },
        },
    )
    """

    logged_output = run_logger(tmp_path, code)
    logged_output = json.loads(logged_output)
    fields = logged_output["Fields"]
    payload_str = fields["payload"]
    payload = json.loads(payload_str)

    # Verify string_list is an empty array, not null
    string_list_value = payload["metrics"]["string_list"]["metric.request_string_list"]
    assert string_list_value == [], (
        f"Expected empty array for nil string_list, got: {string_list_value}"
    )

    # Validate payload against Glean schema
    schema_url = (
        "https://raw.githubusercontent.com/mozilla-services/"
        "mozilla-pipeline-schemas/main/"
        "schemas/glean/glean/glean.1.schema.json"
    )

    input = io.StringIO(payload_str)
    output = io.StringIO()
    assert validate_ping.validate_ping(input, output, schema_url=schema_url) == 0, (
        output.getvalue()
    )


@pytest.mark.go_dependency
def test_run_logging_custom_ping_with_event(tmp_path):
    glean_module_path = tmp_path / "glean"

    translate.translate(
        [
            ROOT / "data" / "go_server_custom_ping_only_metrics.yaml",
            ROOT / "data" / "go_server_custom_ping_only_pings.yaml",
        ],
        "go_server",
        glean_module_path,
    )

    code = """
    logger.RecordServerTelemetryScenarioOnePing(
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
                EventFieldString: "exta value string",
                EventFieldQuantity: 30,
                EventFieldBool: true,
            },
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
    assert validate_ping.validate_ping(input, output, schema_url=schema_url) == 0, (
        output.getvalue()
    )
