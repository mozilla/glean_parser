# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from pathlib import Path
import json
import re
import textwrap

import pytest

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

    # `follows_collection_enabled` forces `enabled=false`
    assert pings["nofollows"].follows_collection_enabled is False
    assert pings["nofollows"].enabled is False


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
        ['$schema', '$tags']
        """,
        """
        ```
        gleantest.short.category:very_long_metric_name_this_is_too_long_as_well_since_it_has_sooooo_many_characters
        ```

        'very_long_metric_name_this_is_too_long_as_well_since_it_has_sooooo_many_characters' is not valid under any
        of the given schemas
        'very_long_metric_name_this_is_too_long_as_well_since_it_has_sooooo_many_characters' is too long
        """,  # noqa: E501 #
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
                type: string
                key_2:
                description: Sample extra key
                type: string
                key_3:
                description: Sample extra key
                type: string
                key_4:
                description: Sample extra key
                type: string
                key_5:
                description: Sample extra key
                type: string
                key_6:
                description: Sample extra key
                type: string
                key_7:
                description: Sample extra key
                type: string
                key_8:
                description: Sample extra key
                type: string
                key_9:
                description: Sample extra key
                type: string
                key_10:
                description: Sample extra key
                type: string
                key_11:
                description: Sample extra key
                type: string
                key_12:
                description: Sample extra key
                type: string
                key_13:
                description: Sample extra key
                type: string
                key_14:
                description: Sample extra key
                type: string
                key_15:
                description: Sample extra key
                type: string
                key_16:
                description: Sample extra key
                type: string
                key_17:
                description: Sample extra key
                type: string
                key_18:
                description: Sample extra key
                type: string
                key_19:
                description: Sample extra key
                type: string
                key_20:
                description: Sample extra key
                type: string
                key_21:
                description: Sample extra key
                type: string
                key_22:
                description: Sample extra key
                type: string
                key_23:
                description: Sample extra key
                type: string
                key_24:
                description: Sample extra key
                type: string
                key_25:
                description: Sample extra key
                type: string
                key_26:
                description: Sample extra key
                type: string
                key_27:
                description: Sample extra key
                type: string
                key_28:
                description: Sample extra key
                type: string
                key_29:
                description: Sample extra key
                type: string
                key_30:
                description: Sample extra key
                type: string
                key_31:
                description: Sample extra key
                type: string
                key_32:
                description: Sample extra key
                type: string
                key_33:
                description: Sample extra key
                type: string
                key_34:
                description: Sample extra key
                type: string
                key_35:
                description: Sample extra key
                type: string
                key_36:
                description: Sample extra key
                type: string
                key_37:
                description: Sample extra key
                type: string
                key_38:
                description: Sample extra key
                type: string
                key_39:
                description: Sample extra key
                type: string
                key_40:
                description: Sample extra key
                type: string
                key_41:
                description: Sample extra key
                type: string
                key_42:
                description: Sample extra key
                type: string
                key_43:
                description: Sample extra key
                type: string
                key_44:
                description: Sample extra key
                type: string
                key_45:
                description: Sample extra key
                type: string
                key_46:
                description: Sample extra key
                type: string
                key_47:
                description: Sample extra key
                type: string
                key_48:
                description: Sample extra key
                type: string
                key_49:
                description: Sample extra key
                type: string
                key_50:
                description: Sample extra key
                type: string
                key_51:
                description: Sample extra key
                type: string
        ```
        {'key_1': {'description': 'Sample extra key','type': 'string'},
        'key_2': {'description': 'Sample extra key','type': 'string'},
        'key_3': {'description': 'Sample extra key','type': 'string'},
        'key_4': {'description': 'Sample extra key','type': 'string'},
        'key_5': {'description': 'Sample extra key','type': 'string'},
        'key_6': {'description': 'Sample extra key','type': 'string'},
        'key_7': {'description': 'Sample extra key','type': 'string'},
        'key_8': {'description': 'Sample extra key','type': 'string'},
        'key_9': {'description': 'Sample extra key','type': 'string'},
        'key_10': {'description': 'Sample extra key','type': 'string'},
        'key_11': {'description': 'Sample extra key','type': 'string'},
        'key_12': {'description': 'Sample extra key','type': 'string'},
        'key_13': {'description': 'Sample extra key','type': 'string'},
        'key_14': {'description': 'Sample extra key','type': 'string'},
        'key_15': {'description': 'Sample extra key','type': 'string'},
        'key_16': {'description': 'Sample extra key','type': 'string'},
        'key_17': {'description': 'Sample extra key','type': 'string'},
        'key_18': {'description': 'Sample extra key','type': 'string'},
        'key_19': {'description': 'Sample extra key','type': 'string'},
        'key_20': {'description': 'Sample extra key','type': 'string'},
        'key_21': {'description': 'Sample extra key','type': 'string'},
        'key_22': {'description': 'Sample extra key','type': 'string'},
        'key_23': {'description': 'Sample extra key','type': 'string'},
        'key_24': {'description': 'Sample extra key','type': 'string'},
        'key_25': {'description': 'Sample extra key','type': 'string'},
        'key_26': {'description': 'Sample extra key','type': 'string'},
        'key_27': {'description': 'Sample extra key','type': 'string'},
        'key_28': {'description': 'Sample extra key','type': 'string'},
        'key_29': {'description': 'Sample extra key','type': 'string'},
        'key_30': {'description': 'Sample extra key','type': 'string'},
        'key_31': {'description': 'Sample extra key','type': 'string'},
        'key_32': {'description': 'Sample extra key','type': 'string'},
        'key_33': {'description': 'Sample extra key','type': 'string'},
        'key_34': {'description': 'Sample extra key','type': 'string'},
        'key_35': {'description': 'Sample extra key','type': 'string'},
        'key_36': {'description': 'Sample extra key','type': 'string'},
        'key_37': {'description': 'Sample extra key','type': 'string'},
        'key_38': {'description': 'Sample extra key','type': 'string'},
        'key_39': {'description': 'Sample extra key','type': 'string'},
        'key_40': {'description': 'Sample extra key','type': 'string'},
        'key_41': {'description': 'Sample extra key','type': 'string'},
        'key_42': {'description': 'Sample extra key','type': 'string'},
        'key_43': {'description': 'Sample extra key','type': 'string'},
        'key_44': {'description': 'Sample extra key','type': 'string'},
        'key_45': {'description': 'Sample extra key','type': 'string'},
        'key_46': {'description': 'Sample extra key','type': 'string'},
        'key_47': {'description': 'Sample extra key','type': 'string'},
        'key_48': {'description': 'Sample extra key','type': 'string'},
        'key_49': {'description': 'Sample extra key','type': 'string'},
        'key_50': {'description': 'Sample extra key','type': 'string'},
        'key_51': {'description': 'Sample extra key','type': 'string'}
        } has too many properties
        Documentation for this node:
            The acceptable keys on the "extra" object sent with events. This is an
            object mapping the key to an object containing metadata about the key.
            A maximum of 50 extra keys is allowed.
            This metadata object has the following keys:
                - `description`: **Required.** A description of the key.
            Valid when `type`_ is `event`.
        """,
    ]

    expected_errors = set(
        re.sub(r"\s", "", textwrap.indent(textwrap.dedent(x), "    ").strip())
        for x in expected_errors
    )

    # Compare errors 1-by-1 for better assertion message when it fails.
    found = sorted(list(found_errors))
    expected = sorted(list(expected_errors))

    for found_error, expected_error in zip(found, expected):
        assert found_error == expected_error


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
        "1" * 112,
        "Møøse",
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
    # Test plain custom_distribution, now also allowed generally
    contents = [
        {
            "category": {
                "metric": {
                    "type": "custom_distribution",
                    "range_min": 0,
                    "range_max": 60000,
                    "bucket_count": 200,
                    "histogram_type": "exponential",
                }
            }
        }
    ]

    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)
    errors = list(all_metrics)
    assert len(errors) == 0

    # Test that custom_distribution has required parameters
    contents = [
        {
            "category": {
                "metric": {
                    "type": "custom_distribution",
                }
            }
        }
    ]

    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)
    errors = list(all_metrics)
    assert len(errors) == 1
    assert "`custom_distribution` is missing required parameters" in errors[0]

    # Test that correct usage
    contents = [
        {
            "category": {
                "metric": {
                    "type": "custom_distribution",
                    "range_max": 60000,
                    "bucket_count": 200,
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
    assert distribution.bucket_count == 200
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


def test_interesting_disables_others():
    # Test that if we get an "interesting" config param, only the metrics in
    # the provided config files are enabled.

    # We'll have aall_metrics.yaml available loaded.
    all_metrics = ROOT / "data" / "all_metrics.yaml"
    # But, only the metrics in metric-with-tags.yaml are marked as interesting
    # so every other metric will be marked as disabled.
    metrics_with_tags_yaml = ROOT / "data" / "metric-with-tags.yaml"
    interesting = [Path(path) for path in [metrics_with_tags_yaml]]
    config = {"interesting": interesting}

    all_metrics = parser.parse_objects([all_metrics, metrics_with_tags_yaml], config)
    errors = list(all_metrics)
    assert len(errors) == 0

    interesting_metrics = parser.parse_objects([metrics_with_tags_yaml])
    errors = list(interesting_metrics)
    assert len(errors) == 0

    metrics = all_metrics.value
    for category_key, category_val in metrics.items():
        if category_key == "tags":
            continue

        for metric_key, metric_val in sorted(category_val.items()):
            cat = interesting_metrics.value.get(category_key)
            if cat and cat.get(metric_key):
                disabled = cat.get(metric_key).disabled
            else:
                disabled = True
            assert metrics[category_key][metric_key].disabled is disabled


def test_send_in_pings_restrictions():
    """Test that invalid ping names are disallowed in `send_in_pings`."""
    all_metrics = parser.parse_objects(ROOT / "data" / "invalid-ping-names.yaml")
    errors = list(all_metrics)
    assert len(errors) == 1

    assert "'invalid_ping_name' does not match" in errors[0]


def test_tags():
    """Tests that tags can be specified."""
    all_metrics = parser.parse_objects(ROOT / "data" / "metric-with-tags.yaml")
    errors = list(all_metrics)

    assert errors == []
    assert len(all_metrics.value) == 1
    assert set(all_metrics.value["telemetry"]["client_id"].metadata.keys()) == set(
        ["tags"]
    )
    assert set(all_metrics.value["telemetry"]["client_id"].metadata["tags"]) == set(
        ["banana", "apple", "global_tag"]
    )


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


def test_expire_by_major_version():
    failing_metrics = [
        {
            "category": {
                "metric_fail_date": {
                    "type": "boolean",
                    "expires": "1986-07-03",
                },
            }
        }
    ]
    failing_metrics = [util.add_required(x) for x in failing_metrics]

    with pytest.raises(ValueError):
        # Dates are not allowed if expiration by major version is enabled.
        all_metrics = parser.parse_objects(
            failing_metrics,
            {
                "expire_by_version": 15,
            },
        )
        errors = list(all_metrics)

    contents = [
        {
            "category": {
                "metric_expired_version": {
                    "type": "boolean",
                    "expires": 7,
                },
                "metric_expired_edge": {
                    "type": "boolean",
                    "expires": 15,
                },
                "metric_expired": {
                    "type": "boolean",
                    "expires": "expired",
                },
                "metric": {
                    "type": "boolean",
                    "expires": 18,
                },
            }
        }
    ]
    contents = [util.add_required(x) for x in contents]

    # Double-check that parsing without custom functions breaks
    all_metrics = parser.parse_objects(
        contents,
        {
            "expire_by_version": 15,
        },
    )
    errors = list(all_metrics)
    assert len(errors) == 0
    assert all_metrics.value["category"]["metric_expired_version"].disabled is True
    assert all_metrics.value["category"]["metric_expired_edge"].disabled is True
    assert all_metrics.value["category"]["metric_expired"].disabled is True
    assert all_metrics.value["category"]["metric"].disabled is False


def test_parser_mixed_expirations():
    """Validate that mixing expiration types fail"""
    with pytest.raises(ValueError):
        # Mixing expiration types must fail when expiring by version.
        all_metrics = parser.parse_objects(
            ROOT / "data" / "mixed-expirations.yaml",
            {
                "expire_by_version": 15,
            },
        )
        list(all_metrics)

    with pytest.raises(ValueError):
        # Mixing expiration types must fail when expiring by date.
        all_metrics = parser.parse_objects(ROOT / "data" / "mixed-expirations.yaml")
        list(all_metrics)


def test_expire_by_version_must_fail_if_disabled():
    failing_metrics = [
        {
            "category": {
                "metric_fail_date": {
                    "type": "boolean",
                    "expires": 99,
                },
            }
        }
    ]
    failing_metrics = [util.add_required(x) for x in failing_metrics]

    with pytest.raises(ValueError):
        # Versions are not allowed if expiration by major version is enabled.
        all_metrics = parser.parse_objects(failing_metrics)
        list(all_metrics)


def test_historical_versions():
    """
    Make sure we can load the correct version of the schema and it will
    correctly reject or not reject entries based on that.
    """

    # No issues:
    # * Bugs as numbers
    # * event extra keys don't have a type
    contents = [
        {
            "$schema": "moz://mozilla.org/schemas/glean/metrics/1-0-0",
            "category": {
                "metric": {
                    "type": "event",
                    "extra_keys": {"key_a": {"description": "foo"}},
                    "bugs": [42],
                }
            },
        }
    ]
    contents = [util.add_required(x) for x in contents]

    all_metrics = parser.parse_objects(contents)

    errors = list(all_metrics)
    assert len(errors) == 0

    # 1 issue:
    # * Bugs as numbers are disallowed
    #
    # events: not having a `type` is fine in version 2.
    contents = [
        {
            "$schema": "moz://mozilla.org/schemas/glean/metrics/2-0-0",
            "category": {
                "metric": {
                    "type": "event",
                    "extra_keys": {"key_a": {"description": "foo"}},
                    "bugs": [42],
                }
            },
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


def test_ping_ordering():
    contents = parser.parse_objects(
        [ROOT / "data" / "pings.yaml"],
        config={"allow_reserved": False},
    )

    errs = list(contents)
    assert len(errs) == 0

    pings = list(contents.value["pings"].keys())

    assert pings == sorted(pings)


def test_metric_ordering():
    all_metrics = parser.parse_objects(
        [ROOT / "data" / "ordering.yaml"], config={"allow_reserved": False}
    )

    errs = list(all_metrics)
    assert len(errs) == 0

    category = all_metrics.value["testing.ordering"]

    assert len(category.values()) > 0
    test_metrics = [f"{m.category}.{m.name}" for m in category.values()]

    # Alphabetically ordered
    assert test_metrics == [
        "testing.ordering.a_second_test_metric",
        "testing.ordering.first_test_metric",
        "testing.ordering.third_test_metric",
    ]


def test_tag_ordering():
    all_metrics = parser.parse_objects(ROOT / "data" / "metric-with-tags.yaml")

    errs = list(all_metrics)
    assert len(errs) == 0

    tags = all_metrics.value["telemetry"]["client_id"].metadata["tags"]
    assert tags == sorted(tags)


def test_text_valid():
    """
    Ensure that `text` metrics parse properly.
    """

    all_metrics = parser.parse_objects(
        [ROOT / "data" / "text.yaml"],
        config={"allow_reserved": False},
    )

    errors = list(all_metrics)
    assert len(errors) == 0

    assert all_metrics.value["valid.text"]["lifetime"].lifetime == metrics.Lifetime.ping

    assert all_metrics.value["valid.text"]["sensitivity"].data_sensitivity == [
        metrics.DataSensitivity.stored_content
    ]


def test_text_invalid():
    """
    Ensure that `text` metrics parse properly.
    """

    all_metrics = parser.parse_objects(
        [ROOT / "data" / "text_invalid.yaml"],
        config={"allow_reserved": False},
    )

    errors = list(all_metrics)
    assert len(errors) == 3

    def compare(expected, found):
        return "".join(expected.split()) in "".join(found.split())

    for error in errors:
        if "sensitivity" in error:
            assert compare("'technical' is not one of", error)

        if "lifetime" in error:
            assert compare("'user' is not one of", error)

        if "builtin_pings" in error:
            assert compare("Built-in pings are not allowed", error)


def test_metadata_tags_sorted():
    all_metrics = parser.parse_objects(
        [
            util.add_required(
                {
                    "$tags": ["tag1"],
                    "category": {"metric": {"metadata": {"tags": ["tag2"]}}},
                }
            )
        ]
    )
    errors = list(all_metrics)
    assert len(errors) == 0
    assert all_metrics.value["category"]["metric"].disabled is False
    assert all_metrics.value["category"]["metric"].metadata["tags"] == ["tag1", "tag2"]


def test_no_lint_sorted():
    all_objects = parser.parse_objects(
        [
            util.add_required(
                {
                    "no_lint": ["lint1"],
                    "category": {"metric": {"no_lint": ["lint2"]}},
                }
            ),
            util.add_required_ping(
                {
                    "no_lint": ["lint1"],
                    "ping": {"no_lint": ["lint2"]},
                }
            ),
            {
                "$schema": parser.TAGS_ID,
                # no_lint is only valid at the top level for tags
                "no_lint": ["lint2", "lint1"],
                "tag": {"description": ""},
            },
        ]
    )
    errors = list(all_objects)
    assert len(errors) == 0
    assert all_objects.value["category"]["metric"].no_lint == ["lint1", "lint2"]
    assert all_objects.value["pings"]["ping"].no_lint == ["lint1", "lint2"]
    assert all_objects.value["tags"]["tag"].no_lint == ["lint1", "lint2"]


def test_no_internal_fields_exposed():
    """
    We accidentally exposed fields like `_config` and `_generate_enums` before.
    These ended up in probe-scraper output.

    We replicate the code probe-scraper uses
    and ensure we get the JSON we expect from it.
    """

    results = parser.parse_objects(
        [
            util.add_required(
                {
                    "category": {
                        "metric": {
                            "type": "event",
                            "extra_keys": {
                                "key_a": {"description": "desc-a", "type": "boolean"}
                            },
                        },
                        "metric2": {
                            "type": "dual_labeled_counter",
                            "dual_labels": {
                                "key": { "description": "desc-a" },
                                "category": { "description": "desc-b" },
                            }
                        }
                    },
                }
            ),
        ]
    )
    errs = list(results)
    assert len(errs) == 0

    metrics = {
        metric.identifier(): metric.serialize()
        for category, probes in results.value.items()
        for probe_name, metric in probes.items()
    }

    expected = {
        "category.metric": {
            "bugs": ["http://bugzilla.mozilla.org/12345678"],
            "data_reviews": ["https://example.com/review/"],
            "defined_in": {"line": 3},
            "description": "DESCRIPTION...",
            "disabled": False,
            "expires": "never",
            "extra_keys": {"key_a": {"description": "desc-a", "type": "boolean"}},
            "gecko_datapoint": "",
            "lifetime": "ping",
            "metadata": {},
            "no_lint": [],
            "notification_emails": ["nobody@example.com"],
            "send_in_pings": ["events"],
            "type": "event",
            "version": 0,
        },
        "category.metric2": {
            "bugs": ["http://bugzilla.mozilla.org/12345678"],
            "categories": None,
            "data_reviews": ["https://example.com/review/"],
            "defined_in": {"line": 17},
            "description": "DESCRIPTION...",
            "disabled": False,
            "expires": "never",
            "gecko_datapoint": "",
            "keys": None,
            "lifetime": "ping",
            "metadata": {},
            "no_lint": [],
            "notification_emails": ["nobody@example.com"],
            "send_in_pings": ["metrics"],
            "type": "dual_labeled_counter",
            "version": 0,
        },
    }
    expected_json = json.dumps(expected, sort_keys=True, indent=2)

    out_json = json.dumps(
        metrics,
        sort_keys=True,
        indent=2,
    )
    assert expected_json == out_json


def test_object():
    structure = {"type": "array", "items": {"type": "number"}}
    contents = [{"category": {"metric": {"type": "object", "structure": structure}}}]

    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)
    errors = list(all_metrics)
    assert len(errors) == 0, errors
    assert len(all_metrics.value) == 1
    assert all_metrics.value["category"]["metric"]._generate_structure == structure


def test_object_invalid():
    contents = [{"category": {"metric": {"type": "object"}}}]

    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)
    errors = list(all_metrics)
    assert len(errors) == 1
    assert "`object` is missing required parameter `structure`" in errors[0]

    structure = {"type": "array", "items": {}}
    contents = [{"category": {"metric": {"type": "object", "structure": structure}}}]
    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)
    errors = list(all_metrics)
    assert len(errors) == 1
    assert "missing `type`" in errors[0]
    assert "Allowed: [" in errors[0]

    structure = {"type": "array", "items": {"type": "unknown"}}
    contents = [{"category": {"metric": {"type": "object", "structure": structure}}}]
    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)
    errors = list(all_metrics)
    assert len(errors) == 1
    assert "invalid `type`" in errors[0]
    assert "found: unknown, allowed: [" in errors[0]

    structure = {"type": "array", "properties": {}}
    contents = [{"category": {"metric": {"type": "object", "structure": structure}}}]
    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)
    errors = list(all_metrics)
    assert len(errors) == 1
    assert "`properties` not allowed in array structure" in errors[0]

    structure = {"type": "object", "items": {}}
    contents = [{"category": {"metric": {"type": "object", "structure": structure}}}]
    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)
    errors = list(all_metrics)
    assert len(errors) == 1
    assert "`items` not allowed in object structure" in errors[0]

    structure = {"type": "string"}
    contents = [{"category": {"metric": {"type": "object", "structure": structure}}}]
    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)
    errors = list(all_metrics)
    assert len(errors) == 1
    assert "invalid `type` in object structure." in errors[0]


def test_dual_labeled_counter():
    """
    Ensure that `dual_labeled_counter` metrics parse properly.
    """

    all_metrics = parser.parse_objects(
        [ROOT / "data" / "dual_labeled.yaml"],
        config={"allow_reserved": False},
    )

    errors = list(all_metrics)
    assert len(errors) == 0

    assert all_metrics.value["test.dual_labeled"]["static_static"].ordered_keys == [
        "key1",
        "key2",
    ]
    assert all_metrics.value["test.dual_labeled"][
        "static_static"
    ].ordered_categories == ["category1", "category2"]
    assert all_metrics.value["test.dual_labeled"]["static_dynamic"].ordered_keys == [
        "key1",
        "key2",
    ]
    assert (
        all_metrics.value["test.dual_labeled"]["static_dynamic"].ordered_categories
        is None
    )
    assert all_metrics.value["test.dual_labeled"]["dynamic_static"].ordered_keys is None
    assert all_metrics.value["test.dual_labeled"][
        "dynamic_static"
    ].ordered_categories == ["category1", "category2"]
    assert (
        all_metrics.value["test.dual_labeled"]["dynamic_dynamic"].ordered_keys is None
    )
    assert (
        all_metrics.value["test.dual_labeled"]["dynamic_dynamic"].ordered_categories
        is None
    )


def test_dual_labeled_counter_invalid():
    """
    Ensure that invalidly-defined `dual_labeled_counter` metrics fail to parse.
    """

    all_metrics = parser.parse_objects(
        [ROOT / "data" / "dual_labeled_invalid.yaml"],
        config={"allow_reserved": False},
    )

    errors = list(all_metrics)
    assert len(errors) == 4

    def compare(expected, found):
        return "".join(expected.split()) in "".join(found.split())

    for error in errors:
        if "`key`" in error:
            assert compare("`dual_labels` is missing required parameter `key`", error)

        if "`category`" in error:
            assert compare(
                "`dual_labels` is missing required parameter `categories`", error
            )

        if "`dual_labels`" in error:
            assert compare(
                "`dual_labeled_counter` is missing required parameter `dual_labels`",
                error,
            )


def test_reserved_category():
    all_metrics = parser.parse_objects(ROOT / "data" / "reserved_categories.yamlx")

    errors = list(all_metrics)
    assert len(errors) == 2
    assert "Categories beginning with 'glean' are reserved" in errors[0]
    assert "Categories beginning with 'glean' are reserved" in errors[1]


def test_attribution_distribution():
    all_metrics = parser.parse_objects(ROOT / "data" / "attribution.yaml")

    errors = list(all_metrics)
    assert len(errors) == 0


def test_forbid_non_ext_non_object_attribution_distribution():
    all_metrics = parser.parse_objects(ROOT / "data" / "bad_attribution.yamlx")

    errors = list(all_metrics)
    assert len(errors) == 2
    assert "May only use semi-reserved category" in errors[0]
    assert (
        "Extended attribution/distribution metrics must be of type 'object'"
        in errors[1]
    )
