# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

import os
from pathlib import Path
import subprocess

from glean_parser import kotlin
from glean_parser import metrics
from glean_parser import pings
from glean_parser import translate
from glean_parser.util import DictWrapper


ROOT = Path(__file__).parent


def run_detekt(files):
    detekt_exec = ROOT.parent / "detekt-cli.jar"
    # We want to make sure this runs on CI, but it's not required
    # for local development
    if detekt_exec.is_file() or "CI" in os.environ:
        subprocess.check_call(
            [
                "java",
                "-jar",
                str(detekt_exec),
                "--build-upon-default-config",
                "--config",
                str(ROOT / "detekt.yml"),
                "-i",
                ",".join(files),
            ]
        )


def run_ktlint(files):
    ktlint_exec = ROOT.parent / "ktlint"
    # We want to make sure this runs on CI, but it's not required
    # for local development
    if ktlint_exec.is_file() or "CI" in os.environ:
        subprocess.check_call([str(ktlint_exec)] + files)


def run_linters(files):
    files = [str(x) for x in files]
    run_ktlint(files)
    run_detekt(files)


def test_parser(tmp_path):
    """Test translating metrics to Kotlin files."""
    translate.translate(
        ROOT / "data" / "core.yaml",
        "kotlin",
        tmp_path,
        {"namespace": "Foo"},
        {"allow_reserved": True},
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(
        [
            "CorePing.kt",
            "Telemetry.kt",
            "Environment.kt",
            "DottedCategory.kt",
            "GleanInternalMetrics.kt",
            "GleanBuildInfo.kt",
        ]
    )

    # Make sure descriptions made it in
    with (tmp_path / "CorePing.kt").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "True if the user has set Firefox as the default browser." in content
        # Make sure the namespace option is in effect
        assert "package Foo" in content

    with (tmp_path / "Telemetry.kt").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "جمع 搜集" in content

    with (tmp_path / "GleanInternalMetrics.kt").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert 'category = ""' in content

    with (tmp_path / "GleanBuildInfo.kt").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "buildDate = Calendar.getInstance" in content

    run_linters(tmp_path.glob("*.kt"))


def test_parser_all_metrics(tmp_path):
    """Test translating ALL metric types to Kotlin files."""
    translate.translate(
        ROOT / "data" / "all_metrics.yaml",
        "kotlin",
        tmp_path,
        {"namespace": "Foo", "with_buildinfo": "false"},
        {"allow_reserved": False},
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(["AllMetrics.kt"])

    run_linters(tmp_path.glob("*.kt"))


def test_ping_parser(tmp_path):
    """Test translating pings to Kotlin files."""
    translate.translate(
        ROOT / "data" / "pings.yaml",
        "kotlin",
        tmp_path,
        {"namespace": "Foo"},
        {"allow_reserved": True},
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(
        ["Pings.kt", "GleanBuildInfo.kt"]
    )

    # Make sure descriptions made it in
    with (tmp_path / "Pings.kt").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "This is a custom ping" in content
        # Make sure the namespace option is in effect
        assert "package Foo" in content

    run_linters(tmp_path.glob("*.kt"))


def test_kotlin_generator():
    kdf = kotlin.kotlin_datatypes_filter

    assert kdf("\n") == r'"\n"'
    assert kdf([42, "\n"]) == r'listOf(42, "\n")'
    assert (
        kdf(DictWrapper([("key", "value"), ("key2", "value2")]))
        == r'mapOf("key" to "value", "key2" to "value2")'
    )
    assert kdf(metrics.Lifetime.ping) == "Lifetime.PING"


def test_metric_type_name():
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

    assert kotlin.type_name(event) == "EventMetricType<MetricExtra>"

    event = metrics.Event(
        type="event",
        category="category",
        name="metric",
        bugs=["http://bugzilla.mozilla.com/12345"],
        notification_emails=["nobody@example.com"],
        description="description...",
        expires="never",
    )

    assert kotlin.type_name(event) == "EventMetricType<NoExtras>"

    boolean = metrics.Boolean(
        type="boolean",
        category="category",
        name="metric",
        bugs=["http://bugzilla.mozilla.com/12345"],
        notification_emails=["nobody@example.com"],
        description="description...",
        expires="never",
    )
    assert kotlin.type_name(boolean) == "BooleanMetricType"

    ping = pings.Ping(
        name="custom",
        description="description...",
        include_client_id=True,
        bugs=["http://bugzilla.mozilla.com/12345"],
        notification_emails=["nobody@nowhere.com"],
    )
    assert kotlin.type_name(ping) == "PingType<NoReasonCodes>"

    ping = pings.Ping(
        name="custom",
        description="description...",
        include_client_id=True,
        bugs=["http://bugzilla.mozilla.com/12345"],
        notification_emails=["nobody@nowhere.com"],
        reasons={"foo": "foolicious", "bar": "barlicious"},
    )
    assert kotlin.type_name(ping) == "PingType<customReasonCodes>"


def test_duplicate(tmp_path):
    """
    Test that there aren't duplicate imports when using a labeled and
    non-labeled version of the same metric.

    https://github.com/mozilla-mobile/android-components/issues/2793
    """
    translate.translate(
        ROOT / "data" / "duplicate_labeled.yaml",
        "kotlin",
        tmp_path,
        {"namespace": "Foo"},
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(
        ["Category.kt", "GleanBuildInfo.kt"]
    )

    with (tmp_path / "Category.kt").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert (
            content.count(
                "import mozilla.components.service.glean.private.CounterMetricType"
            )
            == 1
        )


def test_glean_namespace(tmp_path):
    """
    Test that setting the glean namespace works.
    """
    translate.translate(
        ROOT / "data" / "duplicate_labeled.yaml",
        "kotlin",
        tmp_path,
        {"namespace": "Foo", "glean_namespace": "Bar"},
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(
        ["Category.kt", "GleanBuildInfo.kt"]
    )

    with (tmp_path / "Category.kt").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert content.count("import Bar.private.CounterMetricType") == 1


def test_event_extra_keys_in_correct_order(tmp_path):
    """
    Assert that the extra keys appear in the parameter and the enumeration in
    the same order.

    https://bugzilla.mozilla.org/show_bug.cgi?id=1648768
    """
    translate.translate(
        ROOT / "data" / "event_key_ordering.yaml",
        "kotlin",
        tmp_path,
        {"namespace": "Foo"},
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(
        ["Event.kt", "GleanBuildInfo.kt"]
    )

    with (tmp_path / "Event.kt").open("r", encoding="utf-8") as fd:
        content = fd.read()
        content = " ".join(content.split())
        assert "ExampleExtra(" in content
        assert "and1withextracasing:" in content
        assert "alice:" in content
        assert "bob:" in content
        assert "charlie:" in content
        assert ": EventExtras" in content
        assert 'allowedExtraKeys = listOf("And1WithExtraCasing", "alice", "bob", "charlie")' in content


def test_arguments_are_generated_in_deterministic_order(tmp_path):
    """
    Assert that arguments on generated code are always in the same order.

    https://bugzilla.mozilla.org/show_bug.cgi?id=1666192
    """
    translate.translate(
        ROOT / "data" / "event_key_ordering.yaml",
        "kotlin",
        tmp_path,
        {"namespace": "Foo"},
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(
        ["Event.kt", "GleanBuildInfo.kt"]
    )

    with (tmp_path / "Event.kt").open("r", encoding="utf-8") as fd:
        content = fd.read()
        content = " ".join(content.split())
        expected = 'EventMetricType<ExampleExtra> by lazy { // generated from event.example EventMetricType<ExampleExtra>( CommonMetricData( category = "event", name = "example", sendInPings = listOf("events"), lifetime = Lifetime.PING, disabled = false ), allowedExtraKeys = listOf("And1WithExtraCasing", "alice", "bob", "charlie")) } }'  # noqa
        assert expected in content


def test_event_extra_keys_with_types(tmp_path):
    """
    Assert that the extra keys with types appear with their corresponding types.
    """
    translate.translate(
        ROOT / "data" / "events_with_types.yaml",
        "kotlin",
        tmp_path,
        {"namespace": "Foo"},
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(
        ["Core.kt", "GleanBuildInfo.kt"]
    )

    with (tmp_path / "Core.kt").open("r", encoding="utf-8") as fd:
        content = fd.read()
        content = " ".join(content.split())
        assert (
            "data class PreferenceToggledExtra( "
            "val enabled: Boolean? = null, "
            "val preference: String? = null, "
            "val swapped: Int? = null "
            ") : EventExtras {" in content
        )
        assert (
            'allowedExtraKeys = listOf("enabled", "preference", "swapped")' in content
        )


def test_reasons(tmp_path):
    """
    Assert that we generate the reason codes as a plain enum.

    https://bugzilla.mozilla.org/show_bug.cgi?id=1811888
    """
    translate.translate(
        ROOT / "data" / "pings.yaml",
        "kotlin",
        tmp_path,
        {"namespace": "Foo"},
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(
        ["Pings.kt", "GleanBuildInfo.kt"]
    )

    with (tmp_path / "Pings.kt").open("r", encoding="utf-8") as fd:
        content = fd.read()
        content = " ".join(content.split())

    expected = '@Suppress("ClassNaming", "EnumNaming") enum class customPingMightBeEmptyReasonCodes : ReasonCode { serious { override fun code(): Int = 0 }, silly { override fun code(): Int = 1 }; }'  # noqa
    assert expected in content

    expected = "val customPing: PingType<NoReasonCodes> = // generated from custom-ping"
    assert expected in content

    expected = "val customPingMightBeEmpty: PingType<customPingMightBeEmptyReasonCodes> = // generated from custom-ping-might-be-empty"  # noqa
    assert expected in content


def test_object_metric(tmp_path):
    """
    Assert that an object metric is created.
    """
    translate.translate(
        ROOT / "data" / "object.yaml",
        "kotlin",
        tmp_path,
        {"namespace": "Foo"},
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(
        ["ActivityStream.kt", "ComplexTypes.kt", "CrashStack.kt", "GleanBuildInfo.kt"]
    )

    with (tmp_path / "ComplexTypes.kt").open("r", encoding="utf-8") as fd:
        content = fd.read()
        content = " ".join(content.split())

        assert "typealias ArrayInArrayObjectItemItem = Boolean" in content
        assert "typealias NumberArrayObjectItem = Int" in content

    with (tmp_path / "CrashStack.kt").open("r", encoding="utf-8") as fd:
        content = fd.read()
        content = " ".join(content.split())

        assert "ObjectMetricType<ThreadsObject>" in content
        assert "data class ThreadsObject(" in content
        assert "data class ThreadsObjectItem(" in content
        assert (
            "var frames: ThreadsObjectItemFrames = ThreadsObjectItemFrames"
            in content
        )

        assert "data class ThreadsObjectItemFramesItem(" in content
        assert "var moduleIndex: Int? = null," in content
        assert "var ip: String? = null," in content
        assert "var trust: String? = null," in content
