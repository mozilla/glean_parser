# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from pathlib import Path
import re
import textwrap

import pytest
from jsonschema import _utils

from glean_parser import metrics
from glean_parser import parser

import util


ROOT = Path(__file__).parent


def test_parser():
    """Test the basics of parsing a single file."""
    all_metrics = parser.parse_objects(
        [ROOT / "data" / "core.yaml", ROOT / "data" / "pings.yaml"],
        config={"allow_reserved": True},
    )

    errs = list(all_metrics)
    assert len(errs) == 0

    for category_key, category_val in all_metrics.value.items():
        if category_key == "pings":
            continue
        for _metric_key, metric_val in category_val.items():
            assert isinstance(metric_val, metrics.Metric)
            assert isinstance(metric_val.lifetime, metrics.Lifetime)
            if getattr(metric_val, "labels", None) is not None:
                assert isinstance(metric_val.labels, set)

    pings = all_metrics.value["pings"]
    assert pings["custom-ping"].name == "custom-ping"
    assert pings["custom-ping"].include_client_id is False
    assert pings["really-custom-ping"].name == "really-custom-ping"
    assert pings["really-custom-ping"].include_client_id is True


def test_parser_invalid():
    """Test the basics of parsing a single file."""
    all_metrics = parser.parse_objects(ROOT / "data" / "invalid.yamlx")
    errors = list(all_metrics)
    assert len(errors) == 1
    assert "could not determine a constructor for the tag" in errors[0]


def test_parser_schema_violation():
    """1507792"""
    all_metrics = parser.parse_objects(ROOT / "data" / "schema-violation.yaml")
    errors = list(all_metrics)

    found_errors = set(
        re.sub(r"\s", "", str(error).split("\n", 1)[1].strip()) for error in errors
    )

    expected_errors = [
        """
        ```
        gleantest.lifetime:
          test_counter_inv_lt:
            lifetime: user2
        ```

        'user2' is not one of ['ping', 'user', 'application']

        Documentation for this node:
        Definesthelifetimeofthe metric. It must be one of the following values:

        - `ping` (default): The metric is reset each time it is sent in a ping.

        - `user`: The metric contains a property that is part of the user's
          profile and is never reset.

        - `application`: The metric contains a property that is related to the
          application, and is reset only at application restarts.
        """,
        """
        ```
        gleantest.foo:
          a: b
        ```

        'b' is not of type 'object'

        Documentation for this node:
            Describes a single metric.

            See https://mozilla.github.io/glean_parser/metrics-yaml.html
        """,
        """
        ```
        gleantest.with.way.too.long.category.name
        ...
        ```

        'gleantest.with.way.too.long.category.name' is not valid under any of
        the given schemas
        'gleantest.with.way.too.long.category.name' is too long
        'gleantest.with.way.too.long.category.name' is not one of
        ['$schema']
        """,
        """
        ```
        gleantest.short.category:very_long_metric_name_this_is_too_long_s_well
        ```

        'very_long_metric_name_this_is_too_long_s_well' is not valid under any
        of the given schemas
        'very_long_metric_name_this_is_too_long_s_well' is too long
        """,
        """
        ```
        gleantest:
          test_event:
            type: event
        ```

        Missing required properties: bugs, data_reviews, description, expires,
        notification_emails

        Documentation for this node:
            Describes a single metric.

            See https://mozilla.github.io/glean_parser/metrics-yaml.html
        """,
        """
        ```
        gleantest.event:
            event_too_many_extras:
            extra_keys:
                key_1:
                description: Sample extra key
                key_2:
                description: Sample extra key
                key_3:
                description: Sample extra key
                key_4:
                description: Sample extra key
                key_5:
                description: Sample extra key
                key_6:
                description: Sample extra key
                key_7:
                description: Sample extra key
                key_8:
                description: Sample extra key
                key_9:
                description: Sample extra key
                key_10:
                description: Sample extra key
                key_11:
                description: Sample extra key
        ```
        OrderedDict([('key_1', OrderedDict([('description', 'Sample extra
        key')])), ('key_2', OrderedDict([('description', 'Sample extra
        key')])), ('key_3', OrderedDict([('description', 'Sample extra
        key')])), ('key_4', OrderedDict([('description', 'Sample extra
        key')])), ('key_5', OrderedDict([('description', 'Sample extra
        key')])), ('key_6', OrderedDict([('description', 'Sample extra
        key')])), ('key_7', OrderedDict([('description', 'Sample extra
        key')])), ('key_8', OrderedDict([('description', 'Sample extra
        key')])), ('key_9', OrderedDict([('description', 'Sample extra
        key')])), ('key_10', OrderedDict([('description', 'Sample extra
        key')])), ('key_11', OrderedDict([('description', 'Sample extra
        key')]))]) has too many properties
        Documentation for this node:
            The acceptable keys on the "extra" object sent with events. This is an
            object mapping the key to an object containing metadata about the key.
            A maximum of 10 extra keys is allowed.
            This metadata object has the following keys:
                - `description`: **Required.** A description of the key.
            Valid when `type`_ is `event`.
        """,
    ]

    expected_errors = set(
        re.sub(r"\s", "", _utils.indent(textwrap.dedent(x)).strip())
        for x in expected_errors
    )

    assert sorted(list(found_errors)) == sorted(list(expected_errors))


def test_parser_empty():
    """1507792: Get a good error message if the metrics.yaml file is empty."""
    all_metrics = parser.parse_objects(ROOT / "data" / "empty.yaml")
    errors = list(all_metrics)
    assert len(errors) == 1
    assert "file can not be empty" in errors[0]


def test_invalid_schema():
    all_metrics = parser.parse_objects([{"$schema": "This is wrong"}])
    errors = list(all_metrics)
    assert any("key must be one of" in str(e) for e in errors)


def test_merge_metrics():
    """Merge multiple metrics.yaml files"""
    contents = [
        {"category1": {"metric1": {}, "metric2": {}}, "category2": {"metric3": {}}},
        {"category1": {"metric4": {}}, "category3": {"metric5": {}}},
    ]
    contents = [util.add_required(x) for x in contents]

    all_metrics = parser.parse_objects(contents)
    list(all_metrics)
    all_metrics = all_metrics.value

    assert set(all_metrics["category1"].keys()) == set(
        ["metric1", "metric2", "metric4"]
    )
    assert set(all_metrics["category2"].keys()) == set(["metric3"])
    assert set(all_metrics["category3"].keys()) == set(["metric5"])


def test_merge_metrics_clash():
    """Merge multiple metrics.yaml files with conflicting metric names."""
    contents = [{"category1": {"metric1": {}}}, {"category1": {"metric1": {}}}]
    contents = [util.add_required(x) for x in contents]

    all_metrics = parser.parse_objects(contents)
    errors = list(all_metrics)
    assert len(errors) == 1
    assert "Duplicate metric name" in errors[0]


def test_snake_case_enforcement():
    """Expect exception if names aren't in snake case."""
    contents = [
        {"categoryWithCamelCase": {"metric": {}}},
        {"category": {"metricWithCamelCase": {}}},
    ]

    for content in contents:
        util.add_required(content)
        errors = list(parser._load_file(content, {}))
        assert len(errors) == 1


def test_multiple_errors():
    """Make sure that if there are multiple errors, we get all of them."""
    contents = [{"camelCaseName": {"metric": {"type": "unknown"}}}]

    contents = [util.add_required(x) for x in contents]
    metrics = parser.parse_objects(contents)
    errors = list(metrics)
    assert len(errors) == 2


def test_event_must_be_ping_lifetime():
    contents = [{"category": {"metric": {"type": "event", "lifetime": "user"}}}]

    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)
    errors = list(all_metrics)
    assert len(errors) == 1
    assert "Event metrics must have ping lifetime" in errors[0]


def test_parser_reserved():
    contents = [{"glean.baseline": {"metric": {"type": "string"}}}]

    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)
    errors = list(all_metrics)
    assert len(errors) == 1
    assert "For category 'glean.baseline'" in errors[0]

    all_metrics = parser.parse_objects(contents, {"allow_reserved": True})
    errors = list(all_metrics)
    assert len(errors) == 0


def invalid_in_category(name):
    return [{name: {"metric": {"type": "string"}}}]


def invalid_in_name(name):
    return [{"baseline": {name: {"type": "string"}}}]


def invalid_in_label(name):
    return [{"baseline": {"metric": {"type": "string", "labels": [name]}}}]


@pytest.mark.parametrize(
    "location", [invalid_in_category, invalid_in_name, invalid_in_label]
)
@pytest.mark.parametrize(
    "name",
    [
        "name/with_slash",
        "name#with_pound",
        "this_name_is_too_long_and_shouldnt_be_used",
        "",
    ],
)
def test_invalid_names(location, name):
    contents = location(name)
    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)
    errors = list(all_metrics)
    assert len(errors) == 1
    assert name in errors[0]


def test_duplicate_send_in_pings():
    """Test the basics of parsing a single file."""
    all_metrics = parser.parse_objects(
        [ROOT / "data" / "duplicate_send_in_ping.yaml"], config={"allow_reserved": True}
    )

    errs = list(all_metrics)
    assert len(errs) == 0

    metric = all_metrics.value["telemetry"]["test"]
    assert metric.send_in_pings == ["core", "metrics"]


def test_geckoview_only_on_valid_metrics():
    for metric in [
        "timing_distribution",
        "custom_distributiuon",
        "memory_distribution",
    ]:
        contents = [
            {"category1": {"metric1": {"type": metric, "gecko_datapoint": "FOO"}}}
        ]
        contents = [util.add_required(x) for x in contents]

        all_metrics = parser.parse_objects(contents)
        errs = list(all_metrics)

    contents = [{"category1": {"metric1": {"type": "event", "gecko_datapoint": "FOO"}}}]
    contents = [util.add_required(x) for x in contents]

    all_metrics = parser.parse_objects(contents)
    errs = list(all_metrics)
    assert len(errs) == 1
    assert "is only allowed for" in str(errs[0])


def test_timing_distribution_unit_default():
    contents = [{"category1": {"metric1": {"type": "timing_distribution"}}}]
    contents = [util.add_required(x) for x in contents]

    all_metrics = parser.parse_objects(contents)
    errs = list(all_metrics)
    assert len(errs) == 0
    assert (
        all_metrics.value["category1"]["metric1"].time_unit
        == metrics.TimeUnit.nanosecond
    )


def test_all_pings_reserved():
    # send_in_pings: [all-pings] is only allowed for internal metrics
    contents = [
        {"category": {"metric": {"type": "string", "send_in_pings": ["all-pings"]}}}
    ]

    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)
    errors = list(all_metrics)
    assert len(errors) == 1
    assert "On instance category.metric" in errors[0]
    assert "Only internal metrics" in errors[0]

    all_metrics = parser.parse_objects(contents, {"allow_reserved": True})
    errors = list(all_metrics)
    assert len(errors) == 0

    # A custom ping called "all-pings" is not allowed
    contents = [{"all-pings": {"include_client_id": True}}]
    contents = [util.add_required_ping(x) for x in contents]
    all_pings = parser.parse_objects(contents)
    errors = list(all_pings)
    assert len(errors) == 1
    assert "is not allowed for 'all-pings'"


def test_custom_distribution():
    # Test that custom_distribution isn't allowed on non-Gecko metric
    contents = [
        {
            "category": {
                "metric": {
                    "type": "custom_distribution",
                    "range_min": 0,
                    "range_max": 60000,
                    "bucket_count": 100,
                    "histogram_type": "exponential",
                }
            }
        }
    ]

    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)
    errors = list(all_metrics)
    assert len(errors) == 1
    assert "is only allowed for Gecko" in errors[0]

    # Test that custom_distribution has required parameters
    contents = [
        {
            "category": {
                "metric": {
                    "type": "custom_distribution",
                    "gecko_datapoint": "FROM_GECKO",
                }
            }
        }
    ]

    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)
    errors = list(all_metrics)
    assert len(errors) == 1
    assert "`custom_distribution` is missing required parameters" in errors[0]

    # Test maximum bucket_count is enforced
    contents = [
        {
            "category": {
                "metric": {
                    "type": "custom_distribution",
                    "gecko_datapoint": "FROM_GECKO",
                    "range_max": 60000,
                    "bucket_count": 101,
                    "histogram_type": "exponential",
                }
            }
        }
    ]

    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)
    errors = list(all_metrics)
    assert len(errors) == 1
    assert "101 is greater than" in errors[0]

    # Test that correct usage
    contents = [
        {
            "category": {
                "metric": {
                    "type": "custom_distribution",
                    "gecko_datapoint": "FROM_GECKO",
                    "range_max": 60000,
                    "bucket_count": 100,
                    "histogram_type": "exponential",
                }
            }
        }
    ]

    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)
    errors = list(all_metrics)
    assert len(errors) == 0
    distribution = all_metrics.value["category"]["metric"]
    assert distribution.range_min == 1
    assert distribution.range_max == 60000
    assert distribution.bucket_count == 100
    assert distribution.histogram_type == metrics.HistogramType.exponential


def test_memory_distribution():
    # Test that we get an error for a missing unit
    contents = [{"category": {"metric": {"type": "memory_distribution"}}}]

    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)
    errors = list(all_metrics)
    assert len(errors) == 1
    assert (
        "`memory_distribution` is missing required parameter `memory_unit`" in errors[0]
    )

    # Test that memory_distribution works
    contents = [
        {
            "category": {
                "metric": {"type": "memory_distribution", "memory_unit": "megabyte"}
            }
        }
    ]

    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)
    errors = list(all_metrics)
    assert len(errors) == 0
    assert len(all_metrics.value) == 1
    assert (
        all_metrics.value["category"]["metric"].memory_unit
        == metrics.MemoryUnit.megabyte
    )


def test_quantity():
    # Test that we get an error for a missing unit
    contents = [{"category": {"metric": {"type": "quantity"}}}]

    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)
    errors = list(all_metrics)
    assert len(errors) == 1
    assert any(
        "`quantity` is missing required parameter `unit`" in err for err in errors
    )

    # Test that quantity works
    contents = [
        {
            "category": {
                "metric": {
                    "type": "quantity",
                    "unit": "pixel",
                    "gecko_datapoint": "FOO",
                }
            }
        }
    ]

    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)
    errors = list(all_metrics)
    assert len(errors) == 0
    assert len(all_metrics.value) == 1
    assert all_metrics.value["category"]["metric"].unit == "pixel"


def test_do_not_disable_expired():
    # Test that we get an error for a missing unit and gecko_datapoint
    contents = [{"category": {"metric": {"type": "boolean", "expires": "1900-01-01"}}}]

    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents, {"do_not_disable_expired": True})
    errors = list(all_metrics)
    assert len(errors) == 0

    metrics = all_metrics.value
    assert metrics["category"]["metric"].disabled is False


def test_send_in_pings_restrictions():
    """Test that invalid ping names are disallowed in `send_in_pings`."""
    all_metrics = parser.parse_objects(ROOT / "data" / "invalid-ping-names.yaml")
    errors = list(all_metrics)
    assert len(errors) == 1
    assert "'invalid_ping_name' does not match" in errors[0]


def test_custom_expires():
    contents = [
        {
            "category": {
                "metric": {
                    "type": "boolean",
                    "expires": "foo",
                },
                "metric2": {
                    "type": "boolean",
                    "expires": "bar",
                },
            }
        }
    ]
    contents = [util.add_required(x) for x in contents]

    all_metrics = parser.parse_objects(
        contents,
        {
            "custom_is_expired": lambda x: x == "foo",
            "custom_validate_expires": lambda x: x in ("foo", "bar"),
        },
    )

    errors = list(all_metrics)
    assert len(errors) == 0
    assert all_metrics.value["category"]["metric"].disabled is True
    assert all_metrics.value["category"]["metric2"].disabled is False

    with pytest.raises(ValueError):
        # Double-check that parsing without custom functions breaks
        all_metrics = parser.parse_objects(contents)
        errors = list(all_metrics)


def test_historical_versions():
    """
    Make sure we can load the correct version of the schema and it will
    correctly reject or not reject entries based on that.
    """
    contents = [
        {
            "$schema": "moz://mozilla.org/schemas/glean/metrics/1-0-0",
            "category": {"metric": {"type": "event", "bugs": [42]}},
        }
    ]
    contents = [util.add_required(x) for x in contents]

    all_metrics = parser.parse_objects(contents)

    errors = list(all_metrics)
    assert len(errors) == 0

    contents = [
        {
            "$schema": "moz://mozilla.org/schemas/glean/metrics/2-0-0",
            "category": {"metric": {"type": "event", "bugs": [42]}},
        }
    ]
    contents = [util.add_required(x) for x in contents]

    all_metrics = parser.parse_objects(contents)

    errors = list(all_metrics)
    assert len(errors) == 1


def test_telemetry_mirror():
    """
    Ensure that telemetry_mirror makes it into the parsed metric definition.
    """

    all_metrics = parser.parse_objects(
        [ROOT / "data" / "telemetry_mirror.yaml"],
        config={"allow_reserved": False},
    )

    errs = list(all_metrics)
    assert len(errs) == 0

    assert (
        all_metrics.value["telemetry.mirrored"]["parses_fine"].telemetry_mirror
        == "telemetry.test.string_kind"
    )


def test_rates():
    """
    Ensure that `rate` metrics parse properly.
    """

    all_metrics = parser.parse_objects(
        [ROOT / "data" / "rate.yaml"],
        config={"allow_reserved": False},
    )

    errs = list(all_metrics)
    assert len(errs) == 0

    category = all_metrics.value["testing.rates"]
    assert category["has_internal_denominator"].type == "rate"
    assert (
        category["has_external_denominator"].type == "rate"
    )  # Hasn't been transformed to "numerator" yet
    assert (
        category["also_has_external_denominator"].type == "rate"
    )  # Hasn't been transformed to "numerator" yet
    assert (
        category["the_denominator"].type == "counter"
    )  # Hasn't been transformed to "denominator" yet
