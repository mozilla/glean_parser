# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

import pytest
from collections import OrderedDict
from pathlib import Path

from glean_parser import csharp
from glean_parser import metrics
from glean_parser import pings
from glean_parser import translate


ROOT = Path(__file__).parent


@pytest.mark.skip(
    reason="C# support was dropped. This test was not adopted to new APIs"
)
def test_parser(tmpdir):
    """Test translating metrics to C# files."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "core.yaml",
        "csharp",
        tmpdir,
        {"namespace": "Foo"},
        {"allow_reserved": True},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(
        [
            "CorePing.cs",
            "Telemetry.cs",
            "Environment.cs",
            "DottedCategory.cs",
            "GleanInternalMetrics.cs",
        ]
    )

    # Make sure descriptions made it in
    with (tmpdir / "CorePing.cs").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "True if the user has set Firefox as the default browser." in content
        # Make sure the namespace option is in effect
        assert "namespace Foo" in content

    with (tmpdir / "Telemetry.cs").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "جمع 搜集" in content

    with (tmpdir / "GleanInternalMetrics.cs").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert 'category: ""' in content

    # TODO add linters for C#


def test_ping_parser(tmpdir):
    """Test translating pings to C# files."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "pings.yaml",
        "csharp",
        tmpdir,
        {"namespace": "Foo"},
        {"allow_reserved": True},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["Pings.cs"])

    # Make sure descriptions made it in
    with (tmpdir / "Pings.cs").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "This is a custom ping" in content
        # Make sure the namespace option is in effect
        assert "namespace Foo" in content

    # TODO add linters for C#


def test_csharp_generator():
    cdf = csharp.csharp_datatypes_filter

    assert cdf("\n") == r'"\n"'
    assert cdf(["test", "\n"]) == r'new string[] {"test", "\n"}'
    assert (
        cdf(OrderedDict([("key", "value"), ("key2", "value2")]))
        == r'new Dictionary<string, string> {{"key", "value"}, {"key2", "value2"}}'
    )
    assert cdf(metrics.Lifetime.ping) == "Lifetime.Ping"


def test_metric_type_name():
    event = metrics.Event(
        type="event",
        category="category",
        name="metric",
        bugs=["http://bugzilla.mozilla.com/12345"],
        notification_emails=["nobody@example.com"],
        description="description...",
        expires="never",
        extra_keys={"my_extra": {"description": "an extra"}},
    )

    assert csharp.type_name(event) == "EventMetricType<metricKeys>"

    event = metrics.Event(
        type="event",
        category="category",
        name="metric",
        bugs=["http://bugzilla.mozilla.com/12345"],
        notification_emails=["nobody@example.com"],
        description="description...",
        expires="never",
    )

    assert csharp.type_name(event) == "EventMetricType<NoExtraKeys>"

    boolean = metrics.Boolean(
        type="boolean",
        category="category",
        name="metric",
        bugs=["http://bugzilla.mozilla.com/12345"],
        notification_emails=["nobody@example.com"],
        description="description...",
        expires="never",
    )
    assert csharp.type_name(boolean) == "BooleanMetricType"

    ping = pings.Ping(
        name="custom",
        description="description...",
        include_client_id=True,
        bugs=["http://bugzilla.mozilla.com/12345"],
        notification_emails=["nobody@nowhere.com"],
    )
    assert csharp.type_name(ping) == "PingType<NoReasonCodes>"

    ping = pings.Ping(
        name="custom",
        description="description...",
        include_client_id=True,
        bugs=["http://bugzilla.mozilla.com/12345"],
        notification_emails=["nobody@nowhere.com"],
        reasons={"foo": "foolicious", "bar": "barlicious"},
    )
    assert csharp.type_name(ping) == "PingType<customReasonCodes>"


# Note: the `test_duplicate` test, available for other languages, is not
# useful in C#, since we import the whole `Private` namespace.


def test_glean_namespace(tmpdir):
    """
    Test that setting the glean namespace works.
    """
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "duplicate_labeled.yaml",
        "csharp",
        tmpdir,
        {"namespace": "Foo", "glean_namespace": "Bar"},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["Category.cs"])

    with (tmpdir / "Category.cs").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert content.count("using Bar.Private") == 1


def test_event_extra_keys_in_correct_order(tmpdir):
    """
    Assert that the extra keys appear in the parameter and the enumeration in
    the same order.

    https://bugzilla.mozilla.org/show_bug.cgi?id=1648768
    """

    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "event_key_ordering.yaml",
        "csharp",
        tmpdir,
        {"namespace": "Foo"},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["Event.cs"])

    with (tmpdir / "Event.cs").open("r", encoding="utf-8") as fd:
        content = fd.read()
        content = " ".join(content.split())
        assert "exampleKeys { alice, bob, charlie }" in content
        assert 'allowedExtraKeys: new string[] {"alice", "bob", "charlie"}' in content
