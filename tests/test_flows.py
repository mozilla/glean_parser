# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from pathlib import Path
import io

from glean_parser import flows
from glean_parser import lint
from glean_parser import parser
from glean_parser import translate

import util


ROOT = Path(__file__).parent

FLOWS_YAML = ROOT / "data" / "flows.yaml"
FLOWS_METRICS_YAML = ROOT / "data" / "flows_metrics.yaml"


def flow(**overrides):
    """A minimal valid flow definition, with `overrides` applied."""
    definition = {
        "description": "DESCRIPTION...",
        "bugs": ["https://bugzilla.mozilla.org/12345678"],
        "data_reviews": ["https://example.com/review/"],
        "notification_emails": ["nobody@example.com"],
        "starts_on": ["onboarding.started"],
        "ends_on": ["onboarding.finished"],
    }
    definition.update(overrides)
    return definition


def flows_file(**named_flows):
    return {"$schema": parser.FLOWS_ID, **named_flows}


def onboarding_metrics(**overrides):
    """Event metrics for the `onboarding` category, with `overrides` applied."""
    category = {
        "started": {"type": "event"},
        "finished": {"type": "event"},
        "card_shown": {"type": "event"},
    }
    category.update(overrides)
    return util.add_required({"onboarding": category})


def parse(*contents):
    result = parser.parse_objects(list(contents))
    errors = list(result)
    return result.value, errors


def lint_nits(*contents):
    result = parser.parse_objects(list(contents))
    assert list(result) == []
    return lint.lint_metrics(result.value, file=io.StringIO())


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def test_flows_parse_with_their_events_and_settings():
    objs, errors = parse(FLOWS_METRICS_YAML, FLOWS_YAML)
    assert errors == []

    found = flows.flows_in(objs)
    assert set(found) == {"onboarding", "checkout"}

    onboarding = found["onboarding"]
    assert onboarding.events() == {
        "onboarding.started": "starts_on",
        "onboarding.finished": "ends_on",
        "onboarding.dismissed": "ends_on",
        "onboarding.card_shown": "includes",
    }
    assert onboarding.auto_close_timeout_ms == 45 * 60 * 1000
    assert onboarding.disabled is False
    assert onboarding.unresolved == set()

    checkout = found["checkout"]
    assert checkout.auto_close_timeout_ms is None
    assert checkout.disabled is True


def test_auto_close_timeout_units_are_normalized_to_milliseconds():
    for timeout, ms in (
        ("30s", 30_000),
        ("45m", 2_700_000),
        ("2h", 7_200_000),
        ("7d", 604_800_000),
    ):
        objs, errors = parse(
            onboarding_metrics(),
            flows_file(onboarding=flow(auto_close_timeout=timeout)),
        )
        assert errors == []
        assert flows.flows_in(objs)["onboarding"].auto_close_timeout_ms == ms


def test_schema_rejects_malformed_flows():
    for bad in (
        flow(starts_on=[]),
        flow(auto_close_timeout="45 minutes"),
        flow(auto_close_timeout="0m"),
        flow(starts_on=["not_an_identifier"]),
        flow(unknown_field=True),
    ):
        _, errors = parse(onboarding_metrics(), flows_file(onboarding=bad))
        assert len(errors) == 1, bad

    missing_starts_on = flow()
    del missing_starts_on["starts_on"]
    _, errors = parse(onboarding_metrics(), flows_file(onboarding=missing_starts_on))
    assert len(errors) == 1
    assert "starts_on" in errors[0]


def test_schema_rejects_invalid_flow_names():
    for name in ("Onboarding", "1st_run", "with-dash", "x" * 41):
        _, errors = parse(onboarding_metrics(), flows_file(**{name: flow()}))
        assert len(errors) == 1, name


def test_an_event_may_play_only_one_role_in_a_flow():
    for overlapping in (
        flow(ends_on=["onboarding.started"]),
        flow(includes=["onboarding.finished"]),
        flow(includes=["onboarding.started"]),
    ):
        _, errors = parse(onboarding_metrics(), flows_file(onboarding=overlapping))
        assert len(errors) == 1
        assert "at most one of a flow's lists" in errors[0]


def test_the_one_role_rule_applies_to_unresolved_events_too():
    _, errors = parse(
        flows_file(
            onboarding=flow(
                starts_on=["library.started"],
                ends_on=["library.started"],
            )
        )
    )
    assert len(errors) == 1
    assert "at most one of a flow's lists" in errors[0]


def test_duplicate_flow_names_across_files_are_an_error():
    _, errors = parse(
        onboarding_metrics(),
        flows_file(onboarding=flow()),
        flows_file(onboarding=flow(description="A library redefining it.")),
    )
    assert len(errors) == 1
    assert "Duplicate flow name 'onboarding'" in errors[0]


def test_flows_may_only_name_event_metrics():
    _, errors = parse(
        onboarding_metrics(card_shown={"type": "counter"}),
        flows_file(onboarding=flow(includes=["onboarding.card_shown"])),
    )
    assert len(errors) == 1
    assert "'onboarding.card_shown' in `includes` is a counter metric" in errors[0]


def test_flows_may_only_name_in_session_events():
    _, errors = parse(
        onboarding_metrics(card_shown={"type": "event", "in_session": False}),
        flows_file(onboarding=flow(includes=["onboarding.card_shown"])),
    )
    assert len(errors) == 1
    assert "is not `in_session`" in errors[0]


def test_events_not_given_to_the_parser_are_unresolved():
    objs, errors = parse(
        onboarding_metrics(),
        flows_file(onboarding=flow(includes=["library.thing_happened"])),
    )
    assert errors == []
    assert flows.flows_in(objs)["onboarding"].unresolved == {"library.thing_happened"}


def test_a_flows_category_without_flows_yaml_is_an_ordinary_category():
    objs, errors = parse(util.add_required({"flows": {"opened": {"type": "event"}}}))
    assert errors == []
    assert flows.flows_in(objs) == {}
    assert "opened" in objs["flows"]


def test_a_flows_category_with_flows_yaml_is_an_error():
    _, errors = parse(
        onboarding_metrics(),
        util.add_required({"flows": {"opened": {"type": "event"}}}),
        flows_file(onboarding=flow()),
    )
    assert len(errors) == 1
    assert "category named 'flows'" in errors[0]


# ---------------------------------------------------------------------------
# Linting
# ---------------------------------------------------------------------------


def test_unresolved_events_are_a_lint_warning():
    nits = lint_nits(
        onboarding_metrics(),
        flows_file(onboarding=flow(includes=["library.thing_happened"])),
    )
    assert [(n.check_name, n.name, n.check_type) for n in nits] == [
        ("UNRESOLVED_FLOW_EVENT", "onboarding", lint.CheckType.warning)
    ]
    assert "'library.thing_happened' in `includes`" in nits[0].msg


def test_empty_ends_on_is_a_lint_warning():
    nits = lint_nits(onboarding_metrics(), flows_file(onboarding=flow(ends_on=[])))
    assert [(n.check_name, n.check_type) for n in nits] == [
        ("EMPTY_ENDS_ON", lint.CheckType.warning)
    ]


def test_flow_lints_can_be_disabled():
    nits = lint_nits(
        onboarding_metrics(),
        flows_file(
            onboarding=flow(
                ends_on=[],
                includes=["library.thing_happened"],
                no_lint=["EMPTY_ENDS_ON", "UNRESOLVED_FLOW_EVENT"],
            )
        ),
    )
    assert nits == []


def test_flow_lint_warnings_do_not_fail_the_glinter():
    assert lint.glinter([FLOWS_METRICS_YAML, FLOWS_YAML], file=io.StringIO()) == 0


# ---------------------------------------------------------------------------
# Registration data and generated code
# ---------------------------------------------------------------------------


def test_registration_data_is_in_name_order_with_roles_and_resolution():
    objs, errors = parse(FLOWS_METRICS_YAML, FLOWS_YAML)
    assert errors == []

    data = flows.registration_data(flows.flows_in(objs))
    assert [f["name"] for f in data] == ["checkout", "onboarding"]
    assert data[0]["events"] == [
        {"identifier": "checkout.paid", "role": "End", "unresolved": False},
        {"identifier": "checkout.started", "role": "Start", "unresolved": False},
        {"identifier": "library.thing_happened", "role": "Member", "unresolved": True},
        {"identifier": "onboarding.card_shown", "role": "Member", "unresolved": False},
    ]
    assert data[0]["auto_close_timeout_ms"] is None
    assert data[0]["disabled"] is True
    assert data[1]["auto_close_timeout_ms"] == 2_700_000


def test_kotlin_generates_glean_flows(tmp_path):
    translate.translate(
        [FLOWS_METRICS_YAML, FLOWS_YAML], "kotlin", tmp_path, {"namespace": "Foo"}
    )

    content = (tmp_path / "GleanFlows.kt").read_text()
    assert "package Foo" in content
    assert "import mozilla.components.service.glean.private.FlowDefinition" in content
    assert "internal object GleanFlows {" in content
    assert "val definitions: List<FlowDefinition> = listOf(" in content
    assert '"onboarding.started" to FlowRole.START,' in content
    assert '"onboarding.finished" to FlowRole.END,' in content
    assert '"onboarding.card_shown" to FlowRole.MEMBER,' in content
    assert (
        '"library.thing_happened" to FlowRole.MEMBER, '
        "// Unresolved: assumed to be defined elsewhere." in content
    )
    assert "autoCloseTimeoutMs = 2700000UL," in content
    assert "autoCloseTimeoutMs = null," in content
    assert "disabled = true," in content


def test_kotlin_generates_no_glean_flows_without_flows(tmp_path):
    translate.translate(FLOWS_METRICS_YAML, "kotlin", tmp_path, {"namespace": "Foo"})
    assert not (tmp_path / "GleanFlows.kt").exists()


def test_swift_generates_glean_flows(tmp_path):
    translate.translate([FLOWS_METRICS_YAML, FLOWS_YAML], "swift", tmp_path)

    content = (tmp_path / "Metrics.swift").read_text()
    assert "enum GleanFlows {" in content
    assert "static let definitions: [FlowDefinition] = [" in content
    assert '"onboarding.started": .start' in content
    assert "autoCloseTimeoutMs: 2700000," in content
    assert "autoCloseTimeoutMs: nil," in content


def test_swift_generates_no_glean_flows_without_flows(tmp_path):
    translate.translate(FLOWS_METRICS_YAML, "swift", tmp_path)
    assert "GleanFlows" not in (tmp_path / "Metrics.swift").read_text()


def test_rust_generates_glean_flows(tmp_path):
    translate.translate([FLOWS_METRICS_YAML, FLOWS_YAML], "rust", tmp_path)

    content = (tmp_path / "glean_metrics.rs").read_text()
    assert "pub mod glean_flows {" in content
    assert "pub fn definitions() -> Vec<FlowDefinition> {" in content
    assert '("onboarding.started", FlowRole::Start),' in content
    assert "auto_close_timeout_ms: Some(2700000)," in content
    assert "auto_close_timeout_ms: None," in content


def test_rust_generates_no_glean_flows_without_flows(tmp_path):
    translate.translate(FLOWS_METRICS_YAML, "rust", tmp_path)
    assert "glean_flows" not in (tmp_path / "glean_metrics.rs").read_text()


def test_markdown_documents_flows_and_each_events_flows(tmp_path):
    translate.translate([FLOWS_METRICS_YAML, FLOWS_YAML], "markdown", tmp_path)

    content = (tmp_path / "metrics.md").read_text()
    assert "# Flows" in content
    assert "## onboarding flow" in content
    assert "| onboarding.started | entry |" in content
    assert (
        "| library.thing_happened (unresolved: assumed to be defined elsewhere) | member |"
        in content
    )
    assert "**Automatic close timeout:** 45 minutes" in content
    assert "This flow ships disabled." in content
    # The event's row links to every flow it belongs to.
    assert (
        "Part of [checkout](#checkout-flow) (member), "
        "[onboarding](#onboarding-flow) (member)." in content
    )


def test_markdown_is_unchanged_without_flows(tmp_path):
    translate.translate(FLOWS_METRICS_YAML, "markdown", tmp_path)

    content = (tmp_path / "metrics.md").read_text()
    assert "# Flows" not in content
    assert "Part of" not in content


def test_external_translators_receive_flows_as_an_option(tmp_path):
    received = {}

    def external_translator(all_objects, output_dir, options):
        received["categories"] = set(all_objects)
        received["options"] = options

    translate.translate_metrics(
        [FLOWS_METRICS_YAML, FLOWS_YAML], tmp_path, external_translator
    )
    assert "flows" not in received["categories"]
    assert set(received["options"]["flows"]) == {"onboarding", "checkout"}

    translate.translate_metrics(FLOWS_METRICS_YAML, tmp_path, external_translator)
    assert "flows" not in received["options"]
