# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from pathlib import Path

from glean_parser import javascript
from glean_parser import metrics
from glean_parser import pings
from glean_parser import translate


ROOT = Path(__file__).parent


def test_parser_js(tmp_path):
    """Test translating metrics to Javascript files."""
    translate.translate(
        ROOT / "data" / "core.yaml",
        "javascript",
        tmp_path,
        None,
        {"allow_reserved": True},
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(
        [
            "corePing.js",
            "telemetry.js",
            "environment.js",
            "dottedCategory.js",
            "gleanInternalMetrics.js",
        ]
    )

    # Make sure descriptions made it in
    with (tmp_path / "corePing.js").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "True if the user has set Firefox as the default browser." in content

    with (tmp_path / "telemetry.js").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "جمع 搜集" in content

    with (tmp_path / "gleanInternalMetrics.js").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert 'category: ""' in content


def test_parser_js_all_metrics(tmp_path):
    """Test translating metrics to Javascript files."""
    translate.translate(
        ROOT / "data" / "all_metrics.yaml",
        "javascript",
        tmp_path,
        None,
        {"allow_reserved": True},
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(["allMetrics.js"])


def test_parser_ts(tmp_path):
    """Test translating metrics to Typescript files."""
    translate.translate(
        ROOT / "data" / "core.yaml",
        "typescript",
        tmp_path,
        None,
        {"allow_reserved": True},
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(
        [
            "corePing.ts",
            "telemetry.ts",
            "environment.ts",
            "dottedCategory.ts",
            "gleanInternalMetrics.ts",
        ]
    )

    # Make sure descriptions made it in
    with (tmp_path / "corePing.ts").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "use strict" not in content
        assert "True if the user has set Firefox as the default browser." in content

    with (tmp_path / "telemetry.ts").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "use strict" not in content
        assert "جمع 搜集" in content

    with (tmp_path / "gleanInternalMetrics.ts").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "use strict" not in content
        assert 'category: ""' in content


def test_ping_parser(tmp_path):
    """Test translating pings to Javascript files."""
    translate.translate(
        ROOT / "data" / "pings.yaml",
        "javascript",
        tmp_path,
        None,
        {"allow_reserved": True},
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(["pings.js"])

    # Make sure descriptions made it in
    with (tmp_path / "pings.js").open("r", encoding="utf-8") as fd:
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
        extra_keys={"my_extra": {"description": "an extra", "type": "string"}},
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
        extra_keys={"my_extra": {"description": "an extra", "type": "string"}},
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


def test_labeled_subtype_is_imported(tmp_path):
    """
    Test that both the LabeledMetricType and its subtype are imported
    """
    translate.translate(
        ROOT / "data" / "single_labeled.yaml", "javascript", tmp_path, None
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(["category.js"])

    with (tmp_path / "category.js").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert (
            content.count(
                'import CounterMetricType from "@mozilla/glean/private/metrics/counter";'  # noqa
            )
            == 1
        )
        assert (
            content.count(
                'import LabeledMetricType from "@mozilla/glean/private/metrics/labeled";'  # noqa
            )
            == 1
        )


def test_duplicate(tmp_path):
    """
    Test that there aren't duplicate imports when using a labeled and
    non-labeled version of the same metric.

    https://github.com/mozilla-mobile/android-components/issues/2793
    """
    translate.translate(
        ROOT / "data" / "duplicate_labeled.yaml", "javascript", tmp_path, None
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(["category.js"])

    with (tmp_path / "category.js").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert (
            content.count(
                'import CounterMetricType from "@mozilla/glean/private/metrics/counter";'  # noqa
            )
            == 1
        )


def test_reasons(tmp_path):
    translate.translate(ROOT / "data" / "pings.yaml", "javascript", tmp_path, None)

    translate.translate(ROOT / "data" / "pings.yaml", "typescript", tmp_path, None)

    assert set(x.name for x in tmp_path.iterdir()) == set(["pings.js", "pings.ts"])

    with (tmp_path / "pings.js").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "export const CustomPingMightBeEmptyReasonCodes" in content
        assert "export const RealPingMightBeEmptyReasonCodes" not in content

    with (tmp_path / "pings.ts").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "export enum CustomPingMightBeEmptyReasonCodes" in content
        assert "export enum RealPingMightBeEmptyReasonCodes" not in content


def test_event_extra_keys_in_correct_order(tmp_path):
    """
    Assert that the extra keys appear in the parameter and the enumeration in
    the same order.

    https://bugzilla.mozilla.org/show_bug.cgi?id=1648768
    """
    translate.translate(
        ROOT / "data" / "event_key_ordering.yaml",
        "javascript",
        tmp_path,
        None,
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(["event.js"])

    with (tmp_path / "event.js").open("r", encoding="utf-8") as fd:
        content = fd.read()
        content = " ".join(content.split())
        assert '["And1WithExtraCasing", "alice", "bob", "charlie"]' in content


def test_arguments_are_generated_in_deterministic_order(tmp_path):
    """
    Assert that arguments on generated code are always in the same order.

    https://bugzilla.mozilla.org/show_bug.cgi?id=1666192
    """
    translate.translate(
        ROOT / "data" / "event_key_ordering.yaml",
        "javascript",
        tmp_path,
        None,
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(["event.js"])

    with (tmp_path / "event.js").open("r", encoding="utf-8") as fd:
        content = fd.read()
        content = " ".join(content.split())
        expected = 'export const example = new EventMetricType({ category: "event", name: "example", sendInPings: ["events"], lifetime: "ping", disabled: false, }, ["And1WithExtraCasing", "alice", "bob", "charlie"]);'  # noqa
        assert expected in content


def test_qt_platform_template_includes_expected_imports(tmp_path):
    """
    Assert that when the platform is Qt, the template does not contain
    import/export statements.
    """
    translate.translate(
        ROOT / "data" / "single_labeled.yaml",
        "javascript",
        tmp_path,
        {"platform": "qt", "version": "0.14"},
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(["category.js", "qmldir"])

    with (tmp_path / "category.js").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert content.count(".import org.mozilla.Glean 0.14") == 1
        assert content.count("export") == 0


def test_qt_platform_generated_correct_qmldir_file(tmp_path):
    """
    Assert that when the platform is Qt, a qmldir is also generated
    with the expected files listed in it.
    """
    translate.translate(
        ROOT / "data" / "core.yaml",
        "javascript",
        tmp_path,
        {"platform": "qt", "version": "0.14"},
        {"allow_reserved": True},
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(
        [
            "corePing.js",
            "telemetry.js",
            "environment.js",
            "dottedCategory.js",
            "gleanInternalMetrics.js",
            "qmldir",
        ]
    )

    with (tmp_path / "qmldir").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert content.count("CorePing 0.14 corePing.js") == 1
        assert content.count("Telemetry 0.14 telemetry.js") == 1
        assert content.count("Environment 0.14 environment.js") == 1
        assert content.count("DottedCategory 0.14 dottedCategory.js") == 1
        assert content.count("GleanInternalMetrics 0.14 gleanInternalMetrics.js") == 1
        assert content.count("depends org.mozilla.Glean 0.14") == 1


def test_event_extra_keys_with_types(tmp_path):
    """
    Assert that the extra keys with types appear with their corresponding types.
    """
    translate.translate(
        ROOT / "data" / "events_with_types.yaml",
        "typescript",
        tmp_path,
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(["core.ts"])

    with (tmp_path / "core.ts").open("r", encoding="utf-8") as fd:
        content = fd.read()
        content = " ".join(content.split())
        assert (
            "new EventMetricType<{ "
            "enabled?: boolean, "
            "preference?: string, "
            "swapped?: number, "
            "}>({" in content
        )
        assert '"enabled", "preference", "swapped"' in content

    # Make sure this only happens for the TypeScript template.
    translate.translate(
        ROOT / "data" / "events_with_types.yaml",
        "javascript",
        tmp_path,
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(["core.js", "core.ts"])

    with (tmp_path / "core.js").open("r", encoding="utf-8") as fd:
        content = fd.read()
        content = " ".join(content.split())
        assert "new EventMetricType({" in content
        assert '"enabled", "preference", "swapped"' in content


def test_build_info_is_generated_when_option_is_present(tmp_path):
    """
    Assert that build info is generated
    """
    translate.translate(
        ROOT / "data" / "single_labeled.yaml",
        "typescript",
        tmp_path,
        {"with_buildinfo": "true"},
    )
    assert set(x.name for x in tmp_path.iterdir()) == set(
        ["gleanBuildInfo.ts", "category.ts"]
    )

    translate.translate(
        ROOT / "data" / "single_labeled.yaml",
        "typescript",
        tmp_path,
        {"with_buildinfo": "true", "build_date": "2022-03-01T14:10+01:00"},
    )
    assert set(x.name for x in tmp_path.iterdir()) == set(
        ["gleanBuildInfo.ts", "category.ts"]
    )
    with (tmp_path / "gleanBuildInfo.ts").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "new Date(2022, 2, 1, 14, 10, 0)" in content
