# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from collections import OrderedDict
import os
from pathlib import Path
import subprocess

from glean_parser import kotlin
from glean_parser import metrics
from glean_parser import pings
from glean_parser import translate


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


def test_parser(tmpdir):
    """Test translating metrics to Kotlin files."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "core.yaml",
        "kotlin",
        tmpdir,
        {"namespace": "Foo"},
        {"allow_reserved": True},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(
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
    with (tmpdir / "CorePing.kt").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "True if the user has set Firefox as the default browser." in content
        # Make sure the namespace option is in effect
        assert "package Foo" in content

    with (tmpdir / "Telemetry.kt").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "جمع 搜集" in content

    with (tmpdir / "GleanInternalMetrics.kt").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert 'category = ""' in content

    run_linters(tmpdir.glob("*.kt"))


def test_ping_parser(tmpdir):
    """Test translating pings to Kotlin files."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "pings.yaml",
        "kotlin",
        tmpdir,
        {"namespace": "Foo"},
        {"allow_reserved": True},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(
        ["Pings.kt", "GleanBuildInfo.kt"]
    )

    # Make sure descriptions made it in
    with (tmpdir / "Pings.kt").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "This is a custom ping" in content
        # Make sure the namespace option is in effect
        assert "package Foo" in content

    run_linters(tmpdir.glob("*.kt"))


def test_kotlin_generator():
    kdf = kotlin.kotlin_datatypes_filter

    assert kdf("\n") == r'"\n"'
    assert kdf([42, "\n"]) == r'listOf(42, "\n")'
    assert (
        kdf(OrderedDict([("key", "value"), ("key2", "value2")]))
        == r'mapOf("key" to "value", "key2" to "value2")'
    )
    assert kdf(metrics.Lifetime.ping) == "Lifetime.Ping"


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

    assert kotlin.type_name(event) == "EventMetricType<metricKeys, NoExtras>"

    event = metrics.Event(
        type="event",
        category="category",
        name="metric",
        bugs=["http://bugzilla.mozilla.com/12345"],
        notification_emails=["nobody@example.com"],
        description="description...",
        expires="never",
    )

    assert kotlin.type_name(event) == "EventMetricType<NoExtraKeys, NoExtras>"

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


def test_duplicate(tmpdir):
    """
    Test that there aren't duplicate imports when using a labeled and
    non-labeled version of the same metric.

    https://github.com/mozilla-mobile/android-components/issues/2793
    """

    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "duplicate_labeled.yaml", "kotlin", tmpdir, {"namespace": "Foo"}
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(
        ["Category.kt", "GleanBuildInfo.kt"]
    )

    with (tmpdir / "Category.kt").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert (
            content.count(
                "import mozilla.components.service.glean.private.CounterMetricType"
            )
            == 1
        )


def test_glean_namespace(tmpdir):
    """
    Test that setting the glean namespace works.
    """
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "duplicate_labeled.yaml",
        "kotlin",
        tmpdir,
        {"namespace": "Foo", "glean_namespace": "Bar"},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(
        ["Category.kt", "GleanBuildInfo.kt"]
    )

    with (tmpdir / "Category.kt").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert content.count("import Bar.private.CounterMetricType") == 1


def test_gecko_datapoints(tmpdir):
    """Test translating metrics to Kotlin files."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "gecko.yaml",
        "kotlin",
        tmpdir,
        {"glean_namespace": "Bar"},
        {"allow_reserved": True},
    )

    metrics_files = [
        "GfxContentCheckerboard.kt",
        "GfxInfoAdapter.kt",
        "PagePerf.kt",
        "NonGeckoMetrics.kt",
        "GleanBuildInfo.kt",
    ]
    assert set(x.name for x in tmpdir.iterdir()) == set(
        ["GleanGeckoMetricsMapping.kt"] + metrics_files
    )

    # Make sure descriptions made it in
    with (tmpdir / "GleanGeckoMetricsMapping.kt").open("r", encoding="utf-8") as fd:
        content = fd.read()
        # Make sure we're adding the relevant Glean SDK import, once.
        assert content.count("import Bar.private.HistogramMetricBase") == 1

        # Validate the generated Gecko metric mapper Kotlin functions.
        # NOTE: Indentation, whitespaces  and text formatting of the block
        # below are important. Do not change them unless the file format
        # changes, otherwise validation will fail.
        expected_func = """    fun getHistogram(geckoMetricName: String): HistogramMetricBase? {
        return when (geckoMetricName) {
            // From GfxContentCheckerboard.kt
            "CHECKERBOARD_DURATION" -> GfxContentCheckerboard.duration
            // From PagePerf.kt
            "GV_PAGE_LOAD_MS" -> PagePerf.loadTime
            "GV_PAGE_RELOAD_MS" -> PagePerf.reloadTime
            else -> null
        }
    }"""

        assert expected_func in content

        expected_func = """    fun getCategoricalMetric(
        geckoMetricName: String
    ): LabeledMetricType<CounterMetricType>? {
        return when (geckoMetricName) {
            // From PagePerf.kt
            "DOM_SCRIPT_PRELOAD_RESULT" -> PagePerf.domScriptPreload
            else -> null
        }
    }"""

        assert expected_func in content

        expected_func = """    fun getBooleanScalar(geckoMetricName: String): BooleanMetricType? {
        return when (geckoMetricName) {
            // From GfxInfoAdapter.kt
            "gfx_adapter.stand_alone" -> GfxInfoAdapter.standAlone
            else -> null
        }
    }"""

        assert expected_func in content

        expected_func = """    fun getStringScalar(geckoMetricName: String): StringMetricType? {
        return when (geckoMetricName) {
            // From GfxInfoAdapter.kt
            "gfx_adapter.vendor_id" -> GfxInfoAdapter.vendorId
            else -> null
        }
    }"""

        assert expected_func in content

        expected_func = """    fun getQuantityScalar(geckoMetricName: String): QuantityMetricType? {
        return when (geckoMetricName) {
            // From GfxInfoAdapter.kt
            "gfx_adapter.width" -> GfxInfoAdapter.screenWidth
            else -> null
        }
    }"""

        assert expected_func in content

    for file_name in metrics_files:
        with (tmpdir / file_name).open("r", encoding="utf-8") as fd:
            content = fd.read()
            assert "HistogramMetricBase" not in content

    run_linters(tmpdir.glob("*.kt"))


def test_event_extra_keys_in_correct_order(tmpdir):
    """
    Assert that the extra keys appear in the parameter and the enumeration in
    the same order.

    https://bugzilla.mozilla.org/show_bug.cgi?id=1648768
    """

    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "event_key_ordering.yaml",
        "kotlin",
        tmpdir,
        {"namespace": "Foo"},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(
        ["Event.kt", "GleanBuildInfo.kt"]
    )

    with (tmpdir / "Event.kt").open("r", encoding="utf-8") as fd:
        content = fd.read()
        content = " ".join(content.split())
        assert "exampleKeys { alice, bob, charlie }" in content
        assert 'allowedExtraKeys = listOf("alice", "bob", "charlie")' in content


def test_arguments_are_generated_in_deterministic_order(tmpdir):
    """
    Assert that arguments on generated code are always in the same order.

    https://bugzilla.mozilla.org/show_bug.cgi?id=1666192
    """

    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "event_key_ordering.yaml",
        "kotlin",
        tmpdir,
        {"namespace": "Foo"},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(
        ["Event.kt", "GleanBuildInfo.kt"]
    )

    with (tmpdir / "Event.kt").open("r", encoding="utf-8") as fd:
        content = fd.read()
        content = " ".join(content.split())
        expected = 'EventMetricType<exampleKeys, NoExtras> by lazy { // generated from event.example EventMetricType<exampleKeys, NoExtras>( category = "event", name = "example", sendInPings = listOf("events"), lifetime = Lifetime.Ping, disabled = false, allowedExtraKeys = listOf("alice", "bob", "charlie") ) } }'  # noqa
        assert expected in content


def test_event_extra_keys_with_types(tmpdir):
    """
    Assert that the extra keys with types appear with their corresponding types.
    """

    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "events_with_types.yaml",
        "kotlin",
        tmpdir,
        {"namespace": "Foo"},
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(
        ["Core.kt", "GleanBuildInfo.kt"]
    )

    with (tmpdir / "Core.kt").open("r", encoding="utf-8") as fd:
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
