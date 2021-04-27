# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from pathlib import Path

from glean_parser import markdown
from glean_parser import metrics
from glean_parser import pings
from glean_parser import translate


ROOT = Path(__file__).parent


def test_parser(tmpdir):
    """Test translating metrics to Markdown files."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "core.yaml",
        "markdown",
        tmpdir,
        {"namespace": "Foo", "introduction_extra": "Extra Intro Text Bar"},
        {"allow_reserved": True},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["metrics.md"])

    # Make sure descriptions made it in
    with (tmpdir / "metrics.md").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "is assembled out of the box by the Glean SDK." in content
        # Make sure the table structure is in place
        assert (
            "| Name | Type | Description | Data reviews | Extras | "
            + "Expiration | [Data Sensitivity]"
            in content
        )
        # Make sure non ASCII characters are there
        assert "جمع 搜集" in content
        # test that extra text made it
        assert "Extra Intro Text" in content


def test_extra_info_generator():
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

    assert markdown.extra_info(event) == [("my_extra", "an extra")]

    labeled = metrics.LabeledCounter(
        type="labeled_counter",
        category="category",
        name="metric",
        bugs=["http://bugzilla.mozilla.com/12345"],
        notification_emails=["nobody@example.com"],
        description="description...",
        expires="never",
        labels=["label"],
    )

    assert markdown.extra_info(labeled) == [("label", None)]

    # We currently support extra info only for events and labeled types.
    other = metrics.Timespan(
        type="timespan",
        category="category",
        name="metric",
        bugs=["http://bugzilla.mozilla.com/12345"],
        time_unit="day",
        notification_emails=["nobody@example.com"],
        description="description...",
        expires="never",
    )

    assert len(markdown.extra_info(other)) == 0


def test_ping_desc():
    # Make sure to return something for built-in pings.
    for ping_name in pings.RESERVED_PING_NAMES:
        assert len(markdown.ping_desc(ping_name)) > 0

    # We don't expect nothing for unknown pings.
    assert len(markdown.ping_desc("unknown-ping")) == 0

    # If we have a custom ping cache, try look up the
    # description there.
    cache = {}
    cache["cached-ping"] = pings.Ping(
        name="cached-ping",
        description="the description for the custom ping\n with a surprise",
        bugs=["1234"],
        notification_emails=["email@example.com"],
        data_reviews=["https://www.example.com/review"],
        include_client_id=False,
    )

    assert (
        markdown.ping_desc("cached-ping", cache)
        == "the description for the custom ping\n with a surprise"
    )

    # We don't expect nothing for unknown pings, even with caches.
    assert len(markdown.ping_desc("unknown-ping", cache)) == 0


def test_ping_docs():
    # Make sure to return something for built-in pings.
    for ping_name in pings.RESERVED_PING_NAMES:
        docs = markdown.ping_docs(ping_name)
        assert docs.startswith("https://")
        assert len(docs) > 0

    # We don't expect nothing for unknown pings.
    assert len(markdown.ping_docs("unknown-ping")) == 0


def test_metrics_docs():
    assert (
        markdown.metrics_docs("boolean")
        == "https://mozilla.github.io/glean/book/user/metrics/boolean.html"
    )
    assert (
        markdown.metrics_docs("labeled_counter")
        == "https://mozilla.github.io/glean/book/user/metrics/labeled_counters.html"
    )
    assert (
        markdown.metrics_docs("labeled_string")
        == "https://mozilla.github.io/glean/book/user/metrics/labeled_strings.html"
    )


def test_review_title():
    index = 1

    assert (
        markdown.ping_review_title(
            "https://bugzilla.mozilla.org/show_bug.cgi?id=1581647", index
        )
        == "Bug 1581647"
    )
    assert (
        markdown.ping_review_title(
            "https://github.com/mozilla-mobile/fenix/pull/1707", index
        )
        == "mozilla-mobile/fenix#1707"
    )
    assert markdown.ping_review_title("http://example.com/reviews", index) == "Review 1"


def test_reasons(tmpdir):
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "pings.yaml",
        "markdown",
        tmpdir,
        {"namespace": "Foo"},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["metrics.md"])

    # Make sure descriptions made it in
    with (tmpdir / "metrics.md").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "- `serious`: A serious reason for sending a ping." in content


def test_event_extra_keys_in_correct_order(tmpdir):
    """
    Assert that the extra keys appear in the parameter and the enumeration in
    the same order.

    https://bugzilla.mozilla.org/show_bug.cgi?id=1648768
    """

    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "event_key_ordering.yaml",
        "markdown",
        tmpdir,
        {"namespace": "Foo"},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["metrics.md"])

    with (tmpdir / "metrics.md").open("r", encoding="utf-8") as fd:
        content = fd.read()
        print(content)
        content = " ".join(content.split())
        assert (
            r"<ul><li>alice: two</li>"
            r"<li>bob: three</li>"
            r"<li>charlie: one</li></ul>" in content
        )


def test_send_if_empty_metrics(tmpdir):
    tmpdir = Path(str(tmpdir))

    translate.translate(
        [
            ROOT / "data" / "send_if_empty_with_metrics.yaml",
            ROOT / "data" / "pings.yaml",
        ],
        "markdown",
        tmpdir,
        {"namespace": "Foo"},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["metrics.md"])

    # Make sure descriptions made it in
    with (tmpdir / "metrics.md").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "Lorem ipsum dolor sit amet, consectetur adipiscing elit." in content


def test_data_sensitivity():
    event = metrics.Event(
        type="event",
        category="category",
        name="metric",
        bugs=["http://bugzilla.mozilla.com/12345"],
        notification_emails=["nobody@example.com"],
        description="description...",
        expires="never",
        extra_keys={"my_extra": {"description": "an extra"}},
        data_sensitivity=["technical", "interaction"],
    )

    assert markdown.data_sensitivity_numbers(event.data_sensitivity) == "1, 2"

    assert markdown.data_sensitivity_numbers(None) == "unknown"
