# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from collections import OrderedDict
from pathlib import Path
import shutil
import subprocess
import re

from glean_parser import swift
from glean_parser import metrics
from glean_parser import pings
from glean_parser import translate


ROOT = Path(__file__).parent


def run_linters(files):
    # Syntax check on the generated files.
    # Only run this test if swiftc is on the path.
    if shutil.which("swiftc"):
        for filepath in files:
            subprocess.check_call(["swiftc", "-parse", filepath])

    # Lint check on the generated files.
    # Only run this test if swiftlint is on the path.
    if shutil.which("swiftlint"):
        for filepath in files:
            subprocess.check_call(["swiftlint", "lint", filepath])


def test_parser(tmpdir):
    """Test translating metrics to Swift files."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "core.yaml", "swift", tmpdir, {}, {"allow_reserved": True}
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["Metrics.swift"])

    # Make sure descriptions made it in
    with (tmpdir / "Metrics.swift").open("r", encoding="utf-8") as fd:
        content = fd.read()

        assert "True if the user has set Firefox as the default browser." in content
        assert "جمع 搜集" in content
        assert 'category: ""' in content

    run_linters(tmpdir.glob("*.swift"))


def test_ping_parser(tmpdir):
    """Test translating pings to Swift files."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "pings.yaml",
        "swift",
        tmpdir,
        {"namespace": "Foo"},
        {"allow_reserved": True},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["Metrics.swift"])

    # Make sure descriptions made it in
    with (tmpdir / "Metrics.swift").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "This is a custom ping" in content
        # Make sure the namespace option is in effect
        assert "extension Foo" in content
        assert "customPing = Ping<NoReasonCodes>" in content
        assert (
            "customPingMightBeEmpty = Ping<CustomPingMightBeEmptyReasonCodes>"
            in content
        )

    run_linters(tmpdir.glob("*.swift"))


def test_swift_generator():
    kdf = swift.swift_datatypes_filter

    assert kdf("\n") == r'"\n"'
    assert kdf([42, "\n"]) == r'[42, "\n"]'
    assert (
        kdf(OrderedDict([("key", "value"), ("key2", "value2")]))
        == r'["key": "value", "key2": "value2"]'
    )
    assert kdf(metrics.Lifetime.ping) == ".ping"


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

    assert swift.type_name(event) == "EventMetricType<MetricKeys, NoExtras>"

    event = metrics.Event(
        type="event",
        category="category",
        name="metric",
        bugs=["42"],
        notification_emails=["nobody@example.com"],
        description="description...",
        expires="never",
    )

    assert swift.type_name(event) == "EventMetricType<NoExtraKeys, NoExtras>"

    boolean = metrics.Boolean(
        type="boolean",
        category="category",
        name="metric",
        bugs=["http://bugzilla.mozilla.com/12345"],
        notification_emails=["nobody@example.com"],
        description="description...",
        expires="never",
    )
    assert swift.type_name(boolean) == "BooleanMetricType"

    ping = pings.Ping(
        name="custom",
        description="description...",
        include_client_id=True,
        bugs=["http://bugzilla.mozilla.com/12345"],
        notification_emails=["nobody@nowhere.com"],
    )
    assert swift.type_name(ping) == "Ping<NoReasonCodes>"

    ping = pings.Ping(
        name="custom",
        description="description...",
        include_client_id=True,
        bugs=["http://bugzilla.mozilla.com/12345"],
        notification_emails=["nobody@nowhere.com"],
        reasons={"foo": "foolicious", "bar": "barlicious"},
    )
    assert swift.type_name(ping) == "Ping<CustomReasonCodes>"


def test_order_of_fields(tmpdir):
    """Test that translating metrics to Swift files keeps a stable order of fields."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "core.yaml", "swift", tmpdir, {}, {"allow_reserved": True}
    )

    # Make sure descriptions made it in
    fd = (tmpdir / "Metrics.swift").open("r", encoding="utf-8")
    content = fd.read()
    fd.close()

    lines = content.splitlines()
    first_metric_fields = []
    found_metric = False

    # Get the fields of the first metric
    # Checking only one metric should be good enough for now
    for line in lines:
        if found_metric:
            if re.search("\\)$", line):
                break

            # Collect only the fields
            field = line.strip().split(":")[0]
            first_metric_fields.append(field)
        elif re.search("MetricType", line):
            found_metric = True

    expected_fields = ["category", "name", "sendInPings", "lifetime", "disabled"]

    # We only check the limited list of always available fields.
    size = len(expected_fields)
    assert expected_fields == first_metric_fields[:size]


def test_no_import_glean(tmpdir):
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "core.yaml", "swift", tmpdir, {}, {"allow_reserved": True}
    )

    # Make sure descriptions made it in
    fd = (tmpdir / "Metrics.swift").open("r", encoding="utf-8")
    content = fd.read()
    fd.close()

    assert "import Glean" not in content


def test_import_glean(tmpdir):
    tmpdir = Path(str(tmpdir))

    translate.translate(ROOT / "data" / "smaller.yaml", "swift", tmpdir, {}, {})

    # Make sure descriptions made it in
    fd = (tmpdir / "Metrics.swift").open("r", encoding="utf-8")
    content = fd.read()
    fd.close()

    assert "import Glean" in content


def test_event_extra_keys_in_correct_order(tmpdir):
    """
    Assert that the extra keys appear in the parameter and the enumeration in
    the same order.

    https://bugzilla.mozilla.org/show_bug.cgi?id=1648768
    """

    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "event_key_ordering.yaml",
        "swift",
        tmpdir,
        {"namespace": "Foo"},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["Metrics.swift"])

    with (tmpdir / "Metrics.swift").open("r", encoding="utf-8") as fd:
        content = fd.read()
        content = " ".join(content.split())
        assert (
            "enum ExampleKeys: Int32, ExtraKeys "
            "{ case alice = 0 case bob = 1 case charlie = 2" in content
        )
        assert 'allowedExtraKeys: ["alice", "bob", "charlie"]' in content


def test_event_extra_keys_with_types(tmpdir):
    """
    Assert that the extra keys with types appear with their corresponding types.
    """

    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "events_with_types.yaml",
        "swift",
        tmpdir,
        {"namespace": "Foo"},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["Metrics.swift"])

    with (tmpdir / "Metrics.swift").open("r", encoding="utf-8") as fd:
        content = fd.read()
        content = " ".join(content.split())
        assert (
            "struct PreferenceToggledExtra: EventExtras "
            "{ var enabled: Bool? var preference: String? "
            "var swapped: Int32?" in content
        )
        assert 'allowedExtraKeys: ["enabled", "preference", "swapped"]' in content
