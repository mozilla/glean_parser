# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from pathlib import Path
import shutil
import subprocess
import re

from glean_parser import rust
from glean_parser import metrics
from glean_parser import pings
from glean_parser import translate


ROOT = Path(__file__).parent


def run_linters(files):
    # Syntax check on the generated files.
    # Only run this test if cargo is on the path.
    if shutil.which("rustfmt"):
        for filepath in files:
            subprocess.check_call(
                [
                    "rustfmt",
                    "--check",
                    filepath,
                ]
            )
    if shutil.which("cargo"):
        for filepath in files:
            subprocess.check_call(
                [
                    "cargo",
                    "clippy",
                    "--all",
                    "--",
                    "-D",
                    "warnings",
                    filepath,
                ]
            )


def test_parser(tmp_path):
    """Test translating metrics to Rust files."""
    translate.translate(
        ROOT / "data" / "core.yaml", "rust", tmp_path, {}, {"allow_reserved": True}
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(["glean_metrics.rs"])

    # Make sure descriptions made it in
    with (tmp_path / "glean_metrics.rs").open("r", encoding="utf-8") as fd:
        content = fd.read()

        assert "True if the user has set Firefox as the default browser." in content
        assert "جمع 搜集" in content
        assert 'category: "telemetry"' in content

    # We don't have a cargo.toml, not sure what to do here aside from creating a fake
    # one for the purpose of running cargo fmt and cargo clippy
    # run_linters(tmp_path.glob("*.rs"))


def test_ping_parser(tmp_path):
    """Test translating pings to Rust files."""
    translate.translate(
        ROOT / "data" / "pings.yaml",
        "rust",
        tmp_path,
        {"namespace": "Foo"},
        {"allow_reserved": True},
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(["glean_metrics.rs"])

    # Make sure descriptions made it in
    with (tmp_path / "glean_metrics.rs").open("r", encoding="utf-8") as fd:
        content = fd.read()

        assert "This is a custom ping" in content
        assert (
            "custom_ping: ::glean::private::__export::Lazy<::glean::private::"
            + "PingType> =\n    ::glean::private::__export::Lazy::new"
            in content
        )
        assert (
            "custom_ping_might_be_empty: ::glean::private::__export::Lazy<"
            + "::glean::private::PingType> =\n    ::glean::private::__export::Lazy::new"
            in content
        )

    # TODO we need a cargo.toml to run `cargo fmt` and `cargo clippy`
    # and I'm not quite sure how to do that in a non-Rust project for
    # the purpose of testing
    run_linters(tmp_path.glob("*.rs"))


def test_rust_generator():
    kdf = rust.rust_datatypes_filter

    # The Rust datatypes filter encodes strings using JSON-escaping
    assert kdf("\n") == '"\\n".into()'
    assert kdf([42, "\n"]) == 'vec![42, "\\n".into()]'
    assert kdf(metrics.Lifetime.ping) == "Lifetime::Ping"


def test_metric_type_name():
    event = metrics.Event(
        type="event",
        category="category",
        name="metric",
        bugs=["42"],
        notification_emails=["nobody@example.com"],
        description="description...",
        expires="never",
        extra_keys={"my_extra": {"description": "an extra", "type": "string"}},
    )

    assert rust.type_name(event) == "EventMetric<MetricExtra>"

    event = metrics.Event(
        type="event",
        category="category",
        name="metric",
        bugs=["42"],
        notification_emails=["nobody@example.com"],
        description="description...",
        expires="never",
    )

    assert rust.type_name(event) == "EventMetric<NoExtra>"

    boolean = metrics.Boolean(
        type="boolean",
        category="category",
        name="metric",
        bugs=["http://bugzilla.mozilla.com/12345"],
        notification_emails=["nobody@example.com"],
        description="description...",
        expires="never",
    )
    assert rust.type_name(boolean) == "BooleanMetric"

    ping = pings.Ping(
        name="custom",
        description="description...",
        include_client_id=True,
        bugs=["http://bugzilla.mozilla.com/12345"],
        notification_emails=["nobody@nowhere.com"],
    )
    assert rust.type_name(ping) == "Ping<NoReasonCodes>"

    ping = pings.Ping(
        name="custom",
        description="description...",
        include_client_id=True,
        bugs=["http://bugzilla.mozilla.com/12345"],
        notification_emails=["nobody@nowhere.com"],
        reasons={"foo": "foolicious", "bar": "barlicious"},
    )
    assert rust.type_name(ping) == "Ping<CustomReasonCodes>"


def test_order_of_fields(tmp_path):
    """Test that translating metrics to Rust files keeps a stable order of fields."""
    translate.translate(
        ROOT / "data" / "core.yaml", "rust", tmp_path, {}, {"allow_reserved": True}
    )

    # Make sure descriptions made it in
    fd = (tmp_path / "glean_metrics.rs").open("r", encoding="utf-8")
    content = fd.read()
    fd.close()

    lines = content.splitlines()
    first_metric_fields = []
    found_metric = False

    # Get the fields of the first metric
    # Checking only one metric should be good enough for now
    for line in lines:
        if found_metric:
            if re.search("..Default::default()$", line):
                break

            # Collect only the fields
            field = line.strip().split(":")[0]
            first_metric_fields.append(field)
        elif re.search("CommonMetricData {", line):
            found_metric = True

    expected_fields = ["category", "name", "send_in_pings", "lifetime", "disabled"]

    # We only check the limited list of always available fields.
    size = len(expected_fields)
    assert expected_fields == first_metric_fields[:size]


def test_event_extra_keys_in_correct_order(tmp_path):
    """
    Assert that the extra keys appear in the parameter and the enumeration in
    the same order.

    https://bugzilla.mozilla.org/show_bug.cgi?id=1648768
    """
    translate.translate(
        ROOT / "data" / "events_with_types.yaml",
        "rust",
        tmp_path,
        {"namespace": "Foo"},
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(["glean_metrics.rs"])

    with (tmp_path / "glean_metrics.rs").open("r", encoding="utf-8") as fd:
        content = fd.read()
        content = " ".join(content.split())
        assert (
            "pub struct PreferenceToggledExtra { "
            "pub enabled: Option<bool>, pub preference: "
            "Option<String>, pub swapped: Option<u32>, }" in content
        )
        assert (
            "const ALLOWED_KEYS: &'static [&'static str] = "
            '&["enabled", "preference", "swapped"];' in content
        )


def test_event_extra_keys_with_types(tmp_path):
    """
    Assert that the extra keys with types appear with their corresponding types.
    """
    translate.translate(
        ROOT / "data" / "events_with_types.yaml",
        "rust",
        tmp_path,
        {"namespace": "Foo"},
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(["glean_metrics.rs"])

    with (tmp_path / "glean_metrics.rs").open("r", encoding="utf-8") as fd:
        content = fd.read()
        content = " ".join(content.split())
        assert (
            "impl ExtraKeys for PreferenceToggledExtra { "
            "const ALLOWED_KEYS: &'static [&'static str] = "
            '&["enabled", "preference", "swapped"];' in content
        )
        assert (
            "const ALLOWED_KEYS: &'static [&'static str] = "
            '&["enabled", "preference", "swapped"];' in content
        )


def test_object_metric(tmp_path):
    """
    Assert that an object metric is created.
    """
    translate.translate(
        ROOT / "data" / "object.yaml",
        "rust",
        tmp_path,
        {"namespace": "Foo"},
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(["glean_metrics.rs"])

    with (tmp_path / "glean_metrics.rs").open("r", encoding="utf-8") as fd:
        content = fd.read()
        content = " ".join(content.split())

        assert "ObjectMetric<ThreadsObject>" in content
        assert "pub struct ThreadsObjectItem { " in content
        assert "frames: ThreadsObjectItemFrames, }" in content
        assert (
            "pub type ThreadsObjectItemFrames = "
            "Vec<ThreadsObjectItemFramesItem>;" in content
        )

        assert "pub struct ThreadsObjectItemFramesItem { " in content
        assert "module_index: Option<i64>, " in content
        assert "ip: Option<String>, " in content
        assert "trust: Option<String>, " in content
        assert "}" in content
