# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from collections import OrderedDict
from pathlib import Path
import shutil
import subprocess

from glean_parser import swift
from glean_parser import metrics
from glean_parser import pings
from glean_parser import translate


ROOT = Path(__file__).parent


def test_parser(tmpdir):
    """Test translating metrics to Swift files."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "core.yaml", "swift", tmpdir, {}, {"allow_reserved": True}
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(
        [
            "CorePing.swift",
            "Telemetry.swift",
            "Environment.swift",
            "DottedCategory.swift",
            "GleanInternalMetrics.swift",
        ]
    )

    # Make sure descriptions made it in
    with (tmpdir / "CorePing.swift").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "True if the user has set Firefox as the default browser." in content

    with (tmpdir / "Telemetry.swift").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "جمع 搜集" in content

    with (tmpdir / "GleanInternalMetrics.swift").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert 'category: ""' in content

    # Syntax check on the generated files.
    # Only run this test if swiftc is on the path.
    if shutil.which("swiftc"):
        for filepath in tmpdir.glob("*.swift"):
            subprocess.check_call(["swiftc", "-dump-parse", filepath])

    # Lint check on the generated files.
    # Only run this test if swiftlint is on the path.
    if shutil.which("swiftlint"):
        for filepath in tmpdir.glob("*.swift"):
            subprocess.check_call(["swiftlint", "lint", filepath])


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
    # TODO: Events are not yet supported.
    # event = metrics.Event(
    #     type="event",
    #     category="category",
    #     name="metric",
    #     bugs=[42],
    #     notification_emails=["nobody@example.com"],
    #     description="description...",
    #     expires="never",
    #     extra_keys={"my_extra": {"description": "an extra"}},
    # )

    # assert swift.type_name(event) == "EventMetricType<metricKeys>"

    # event = metrics.Event(
    #     type="event",
    #     category="category",
    #     name="metric",
    #     bugs=[42],
    #     notification_emails=["nobody@example.com"],
    #     description="description...",
    #     expires="never",
    # )

    # assert swift.type_name(event) == "EventMetricType<noExtraKeys>"

    boolean = metrics.Boolean(
        type="boolean",
        category="category",
        name="metric",
        bugs=[42],
        notification_emails=["nobody@example.com"],
        description="description...",
        expires="never",
    )
    assert swift.type_name(boolean) == "BooleanMetricType"

    ping = pings.Ping(
        name="custom",
        description="description...",
        include_client_id=True,
        bugs=[42],
        notification_emails=["nobody@nowhere.com"],
    )
    assert swift.type_name(ping) == "Ping<NoExtraKeys>"

    ping = pings.Ping(
        name="custom",
        description="description...",
        include_client_id=True,
        bugs=[42],
        notification_emails=["nobody@nowhere.com"],
        reasons={"foo": "foolicious", "bar": "barlicious"}
    )
    assert swift.type_name(ping) == "Ping<customReasonCodes>"
