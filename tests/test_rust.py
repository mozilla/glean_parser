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


def test_parser(tmpdir):
    """Test translating metrics to Rust files."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "core.yaml", "rust", tmpdir, {}, {"allow_reserved": True}
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["glean_metrics.rs"])

    # Make sure descriptions made it in
    with (tmpdir / "glean_metrics.rs").open("r", encoding="utf-8") as fd:
        content = fd.read()

        assert "True if the user has set Firefox as the default browser." in content
        assert "جمع 搜集" in content
        assert 'category: "telemetry"' in content

    # We don't have a cargo.toml, not sure what to do here aside from creating a fake
    # one for the purpose of running cargo fmt and cargo clippy
    # run_linters(tmpdir.glob("*.rs"))


def test_ping_parser(tmpdir):
    """Test translating pings to Rust files."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "pings.yaml",
        "rust",
        tmpdir,
        {"namespace": "Foo"},
        {"allow_reserved": True},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["glean_metrics.rs"])

    # Make sure descriptions made it in
    with (tmpdir / "glean_metrics.rs").open("r", encoding="utf-8") as fd:
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
    run_linters(tmpdir.glob("*.rs"))


def test_rust_generator():
    kdf = rust.rust_datatypes_filter

    assert kdf("\n") == '"\n".into()'
    assert kdf([42, "\n"]) == 'vec![42, "\n".into()]'
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
        extra_keys={"my_extra": {"description": "an extra"}},
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

    assert rust.type_name(event) == "EventMetric<NoExtraKeys>"

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
    assert rust.type_name(ping) == "Ping<CustomExtra>"

    ping = pings.Ping(
        name="custom",
        description="description...",
        include_client_id=True,
        bugs=["http://bugzilla.mozilla.com/12345"],
        notification_emails=["nobody@nowhere.com"],
        reasons={"foo": "foolicious", "bar": "barlicious"},
    )
    assert rust.type_name(ping) == "Ping<CustomExtra>"


def test_order_of_fields(tmpdir):
    """Test that translating metrics to Rust files keeps a stable order of fields."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "core.yaml", "rust", tmpdir, {}, {"allow_reserved": True}
    )

    # Make sure descriptions made it in
    fd = (tmpdir / "glean_metrics.rs").open("r", encoding="utf-8")
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


def test_event_extra_keys_in_correct_order(tmpdir):
    """
    Assert that the extra keys appear in the parameter and the enumeration in
    the same order.

    https://bugzilla.mozilla.org/show_bug.cgi?id=1648768
    """

    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "events_with_types.yaml",
        "rust",
        tmpdir,
        {"namespace": "Foo"},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["glean_metrics.rs"])

    with (tmpdir / "glean_metrics.rs").open("r", encoding="utf-8") as fd:
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


def test_event_extra_keys_with_types(tmpdir):
    """
    Assert that the extra keys with types appear with their corresponding types.
    """

    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "events_with_types.yaml",
        "rust",
        tmpdir,
        {"namespace": "Foo"},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["glean_metrics.rs"])

    with (tmpdir / "glean_metrics.rs").open("r", encoding="utf-8") as fd:
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
