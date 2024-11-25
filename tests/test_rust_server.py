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


def test_parser_rust_server_ping_no_metrics(tmp_path, capsys):
    """Test that no files are generated if only ping definitions
    are provided without any metrics."""
    translate.translate(
        ROOT / "data" / "server_pings.yaml",
        "rust_server",
        tmp_path,
    )
    assert all(False for _ in tmp_path.iterdir())


def test_parser_rust_server_metrics_unsupported_type(tmp_path, capsys):
    """Test that no files are generated with unsupported metric types."""
    translate.translate(
        [
            ROOT / "data" / "rust_server_metrics_unsupported.yaml",
        ],
        "rust_server",
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


def test_parser_rust_server_events_only(tmp_path):
    """Test that parser works for definitions that only use events ping"""
    translate.translate(
        ROOT / "data" / "rust_server_events_only_metrics.yaml",
        "rust_server",
        tmp_path,
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(["server_events.rs"])

    # Make sure generated file matches expected
    with (tmp_path / "server_events.rs").open("r", encoding="utf-8") as fd:
        content = fd.read()
        with (ROOT / "data" / "server_events_only_compare.rs").open(
            "r", encoding="utf-8"
        ) as cd:
            compare_raw = cd.read()

    glean_version = f"glean_parser v{glean_parser.__version__}"
    compare = compare_raw.replace("{current_version}", glean_version)
    assert content == compare

def test_parser_rust_server_events_and_custom_ping(tmp_path):
    """Test that parser works for definitions that use events ping and custom pings"""
    translate.translate(
        [
            ROOT / "data" / "rust_server_events_and_custom_ping_metrics.yaml",
            ROOT / "data" / "rust_server_events_and_custom_ping_pings.yaml"
        ],
        "rust_server",
        tmp_path,
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(["server_events.rs"])

    # Make sure generated file matches expected
    with (tmp_path / "server_events.rs").open("r", encoding="utf-8") as fd:
        content = fd.read()
        with (ROOT / "data" / "server_events_and_custom_ping_compare.rs").open(
            "r", encoding="utf-8"
        ) as cd:
            compare_raw = cd.read()

    glean_version = f"glean_parser v{glean_parser.__version__}"
    compare = compare_raw.replace("{current_version}", glean_version)
    assert content == compare

def test_parser_rust_server_custom_ping_only(tmp_path):
    """Test that parser works for definitions that only use custom pings"""
    translate.translate(
        [
            ROOT / "data" / "rust_server_custom_ping_only_metrics.yaml",
            ROOT / "data" / "rust_server_custom_ping_only_pings.yaml"
        ],
        "rust_server",
        tmp_path,
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(["server_events.rs"])

    # Make sure generated file matches expected
    with (tmp_path / "server_events.rs").open("r", encoding="utf-8") as fd:
        content = fd.read()
        with (ROOT / "data" / "server_custom_ping_only_compare.rs").open(
            "r", encoding="utf-8"
        ) as cd:
            compare_raw = cd.read()

    glean_version = f"glean_parser v{glean_parser.__version__}"
    compare = compare_raw.replace("{current_version}", glean_version)
    assert content == compare

def run_rust_logger(code_dir, code):
    """
    Run the Rust logger and capture the output sent to STDOUT.
    """
    # Define paths
    tmpl_code_path = Path("test.rs.tmpl")
    
    # Read and replace placeholder in the template
    tmpl_code = ""
    with open(ROOT / "test-rs" /tmpl_code_path, "r") as fp:
        tmpl_code = fp.read()

    # Replace placeholder with actual code
    tmpl_code = tmpl_code.replace("/* CODE */", code)

    # Write the modified template to main.rs in the Rust project

        # Initialize a Rust project if not already initialized
    if not (code_dir / "Cargo.toml").exists():
        subprocess.call(["cargo", "init", "--bin"], cwd=code_dir)

    # Add each dependency to Cargo.toml
    # Define the dependencies to add with their version and features
    dependencies = [

        ("serde", "1.0", ["derive"]),
        ("serde_json", "1.0", None),
        ("chrono", "0.4", ["serde"]),
        ("uuid", "1.0", ["v4"]),
    ]
    for name, version, features in dependencies:
        # Construct the cargo add command
        command = ["cargo", "add", f"{name}@{version}",]
        if features:
            command.extend(["--features", ",".join(features)])
        subprocess.call(command, cwd=code_dir)
    
    # Run cargo build to ensure dependencies are up-to-date
    subprocess.call(["cargo", "build"], cwd=code_dir)
    with open(code_dir / "src" / "main.rs", "w") as fp:
        fp.write(tmpl_code)

    
    # Run the Rust code and capture output
    result = subprocess.check_output(["cargo", "run"], cwd=code_dir).decode("utf-8")
    return result

@pytest.mark.rust_dependency
def test_run_logging_events_ping(tmp_path):
    glean_module_path = tmp_path / "src" / "glean"

    translate.translate(
        [
            ROOT / "data" / "rust_server_events_only_metrics.yaml",
        ],
        "rust_server",
        glean_module_path,
    )

    code = """
    // Creating a `RequestInfo` instance
    let request_info = RequestInfo {
        user_agent: "glean-test/1.0".to_string(),
        ip_address: "127.0.0.1".to_string(),
    };

    // Creating the event that implements `EventsPingEvent`
    let event = BackendTestEventEvent {
        event_field_string: "event extra string value".to_string(),
        event_field_quantity: 100,
        event_field_bool: false,
    };

    // Creating an `EventsPing` instance
    let params = EventsPing {
        metric_name: "string value".to_string(),
        metric_request_bool: true,
        metric_request_count: 10,
        metric_request_datetime: Utc::now(),
        event: Some(Box::new(event)),
    };

    // Calling the `record_events_ping` function on `logger`
    logger.record_events_ping(&request_info, &params);
    """

    logged_output = run_rust_logger(tmp_path, code)
    logged_output = json.loads(logged_output)
    fields = logged_output["Fields"]

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

    payload = fields["payload"]
    input = io.StringIO(payload)
    output = io.StringIO()
    assert (
        validate_ping.validate_ping(input, output, schema_url=schema_url) == 0
    ), output.getvalue()

@pytest.mark.rust_dependency
def test_run_logging_custom_ping_without_event(tmp_path):
    glean_module_path = tmp_path / "src" / "glean"

    translate.translate(
        [
            ROOT / "data" / "rust_server_custom_ping_only_metrics.yaml",
            ROOT / "data" / "rust_server_custom_ping_only_pings.yaml"
        ],
        "rust_server",
        glean_module_path,
    )

    code = """
    // Creating a `RequestInfo` instance
    let request_info = RequestInfo {
        user_agent: "glean-test/1.0".to_string(),
        ip_address: "127.0.0.1".to_string(),
    };

    // Creating a `ServerTelemetryScenarioOnePing` instance
    let params = ServerTelemetryScenarioOnePing {
        metric_name: "string value".to_string(),
        metric_request_bool: true,
        metric_request_count: 20,
        metric_request_datetime: Utc::now(),
        event: None,
    };

    // Calling the `record_events_ping` function on `logger`
    logger.record_server_telemetry_scenario_one_ping(&request_info, &params);
    """    

    logged_output = run_rust_logger(tmp_path, code)
    logged_output = json.loads(logged_output)
    fields = logged_output["Fields"]

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

    payload = fields["payload"]
    input = io.StringIO(payload)
    output = io.StringIO()
    assert (
        validate_ping.validate_ping(input, output, schema_url=schema_url) == 0
    ), output.getvalue()

@pytest.mark.rust_dependency
def test_run_logging_custom_ping_with_event(tmp_path):
    glean_module_path = tmp_path / "src" / "glean"

    translate.translate(
        [
            ROOT / "data" / "rust_server_custom_ping_only_metrics.yaml",
            ROOT / "data" / "rust_server_custom_ping_only_pings.yaml"
        ],
        "rust_server",
        glean_module_path,
    )

    code = """
    // Creating a `RequestInfo` instance
    let request_info = RequestInfo {
        user_agent: "glean-test/1.0".to_string(),
        ip_address: "127.0.0.1".to_string(),
    };

    // Creating a `BackendSpecialEventEvent` instance
    let event = BackendSpecialEventEvent {
        event_field_string: "extra value string".to_string(),
        event_field_quantity: 30,
        event_field_bool: true,
    };

    // Creating a `ServerTelemetryScenarioOnePing` instance
    let params = ServerTelemetryScenarioOnePing {
        metric_name: "string value".to_string(),
        metric_request_bool: true,
        metric_request_count: 20,
        metric_request_datetime: Utc::now(),
        event: Some(Box::new(event)),
    };

    // Calling the `record_events_ping` function on `logger`
    logger.record_server_telemetry_scenario_one_ping(&request_info, &params);
    """

    logged_output = run_rust_logger(tmp_path, code)
    logged_output = json.loads(logged_output)
    fields = logged_output["Fields"]


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

    payload = fields["payload"]
    input = io.StringIO(payload)
    output = io.StringIO()

    assert (
        validate_ping.validate_ping(input, output, schema_url=schema_url) == 0
    ), output.getvalue()
