# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from pathlib import Path

from glean_parser import javascript
from glean_parser import metrics
from glean_parser import pings
from glean_parser import translate


ROOT = Path(__file__).parent


def test_parser_js(tmpdir):
    """Test translating metrics to Javascript files."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "core.yaml",
        "javascript",
        tmpdir,
        None,
        {"allow_reserved": True},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(
        [
            "corePing.js",
            "telemetry.js",
            "environment.js",
            "dottedCategory.js",
            "gleanInternalMetrics.js",
        ]
    )

    # Make sure descriptions made it in
    with (tmpdir / "corePing.js").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "True if the user has set Firefox as the default browser." in content

    with (tmpdir / "telemetry.js").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "جمع 搜集" in content

    with (tmpdir / "gleanInternalMetrics.js").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert 'category: ""' in content


def test_parser_ts(tmpdir):
    """Test translating metrics to Typescript files."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "core.yaml",
        "typescript",
        tmpdir,
        None,
        {"allow_reserved": True},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(
        [
            "corePing.ts",
            "telemetry.ts",
            "environment.ts",
            "dottedCategory.ts",
            "gleanInternalMetrics.ts",
        ]
    )

    # Make sure descriptions made it in
    with (tmpdir / "corePing.ts").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "use strict" not in content
        assert "True if the user has set Firefox as the default browser." in content

    with (tmpdir / "telemetry.ts").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "use strict" not in content
        assert "جمع 搜集" in content

    with (tmpdir / "gleanInternalMetrics.ts").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "use strict" not in content
        assert 'category: ""' in content


def test_ping_parser(tmpdir):
    """Test translating pings to Javascript files."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "pings.yaml",
        "javascript",
        tmpdir,
        None,
        {"allow_reserved": True},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["pings.js"])

    # Make sure descriptions made it in
    with (tmpdir / "pings.js").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "This is a custom ping" in content


def test_javascript_generator():
    jdf = javascript.javascript_datatypes_filter
    assert jdf(metrics.Lifetime.ping) == '"ping"'


def test_metric_class_name():
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

    webext_class_name = javascript.class_name_factory("webext")
    qt_class_name = javascript.class_name_factory("qt")

    assert webext_class_name(event.type) == "EventMetricType"
    assert qt_class_name(event.type) == "Glean.Glean._private.EventMetricType"

    boolean = metrics.Boolean(
        type="boolean",
        category="category",
        name="metric",
        bugs=["http://bugzilla.mozilla.com/12345"],
        notification_emails=["nobody@example.com"],
        description="description...",
        expires="never",
    )
    assert webext_class_name(boolean.type) == "BooleanMetricType"
    assert qt_class_name(boolean.type) == "Glean.Glean._private.BooleanMetricType"

    ping = pings.Ping(
        name="custom",
        description="description...",
        include_client_id=True,
        bugs=["http://bugzilla.mozilla.com/12345"],
        notification_emails=["nobody@nowhere.com"],
    )
    assert webext_class_name(ping.type) == "PingType"
    assert qt_class_name(ping.type) == "Glean.Glean._private.PingType"


def test_import_path():
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

    assert javascript.import_path(event.type) == "metrics/event"

    boolean = metrics.Boolean(
        type="boolean",
        category="category",
        name="metric",
        bugs=["http://bugzilla.mozilla.com/12345"],
        notification_emails=["nobody@example.com"],
        description="description...",
        expires="never",
    )
    assert javascript.import_path(boolean.type) == "metrics/boolean"

    ping = pings.Ping(
        name="custom",
        description="description...",
        include_client_id=True,
        bugs=["http://bugzilla.mozilla.com/12345"],
        notification_emails=["nobody@nowhere.com"],
    )
    assert javascript.import_path(ping.type) == "ping"


def test_labeled_subtype_is_imported(tmpdir):
    """
    Test that both the LabeledMetricType and its subtype are imported
    """

    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "single_labeled.yaml", "javascript", tmpdir, None
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["category.js"])

    with (tmpdir / "category.js").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert (
            content.count(
                'import CounterMetricType from "@mozilla/glean/webext/private/metrics/counter";'  # noqa
            )
            == 1
        )
        assert (
            content.count(
                'import LabeledMetricType from "@mozilla/glean/webext/private/metrics/labeled";'  # noqa
            )
            == 1
        )


def test_duplicate(tmpdir):
    """
    Test that there aren't duplicate imports when using a labeled and
    non-labeled version of the same metric.

    https://github.com/mozilla-mobile/android-components/issues/2793
    """

    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "duplicate_labeled.yaml", "javascript", tmpdir, None
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["category.js"])

    with (tmpdir / "category.js").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert (
            content.count(
                'import CounterMetricType from "@mozilla/glean/webext/private/metrics/counter";'  # noqa
            )
            == 1
        )


def test_event_extra_keys_in_correct_order(tmpdir):
    """
    Assert that the extra keys appear in the parameter and the enumeration in
    the same order.

    https://bugzilla.mozilla.org/show_bug.cgi?id=1648768
    """

    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "event_key_ordering.yaml",
        "javascript",
        tmpdir,
        None,
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["event.js"])

    with (tmpdir / "event.js").open("r", encoding="utf-8") as fd:
        content = fd.read()
        content = " ".join(content.split())
        assert '["alice", "bob", "charlie"]' in content


def test_arguments_are_generated_in_deterministic_order(tmpdir):
    """
    Assert that arguments on generated code are always in the same order.

    https://bugzilla.mozilla.org/show_bug.cgi?id=1666192
    """

    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "event_key_ordering.yaml",
        "javascript",
        tmpdir,
        None,
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["event.js"])

    with (tmpdir / "event.js").open("r", encoding="utf-8") as fd:
        content = fd.read()
        content = " ".join(content.split())
        expected = 'export const example = new EventMetricType({ category: "event", name: "example", sendInPings: ["events"], lifetime: "ping", disabled: false, }, ["alice", "bob", "charlie"]);'  # noqa
        assert expected in content


def test_qt_platform_template_includes_expected_imports(tmpdir):
    """
    Assert that when the platform is Qt, the template does not contain
    import/export statements.
    """

    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "single_labeled.yaml",
        "javascript",
        tmpdir,
        {"platform": "qt", "version": "0.14"},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["category.js", "qmldir"])

    with (tmpdir / "category.js").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert content.count(".import org.mozilla.Glean 0.14") == 1
        assert content.count("export") == 0


def test_qt_platform_generated_correct_qmldir_file(tmpdir):
    """
    Assert that when the platform is Qt, a qmldir is also generated
    with the expected files listed in it.
    """

    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "core.yaml",
        "javascript",
        tmpdir,
        {"platform": "qt", "version": "0.14"},
        {"allow_reserved": True},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(
        [
            "corePing.js",
            "telemetry.js",
            "environment.js",
            "dottedCategory.js",
            "gleanInternalMetrics.js",
            "qmldir",
        ]
    )

    with (tmpdir / "qmldir").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert content.count("CorePing 0.14 corePing.js") == 1
        assert content.count("Telemetry 0.14 telemetry.js") == 1
        assert content.count("Environment 0.14 environment.js") == 1
        assert content.count("DottedCategory 0.14 dottedCategory.js") == 1
        assert content.count("GleanInternalMetrics 0.14 gleanInternalMetrics.js") == 1
        assert content.count("depends org.mozilla.Glean 0.14") == 1
