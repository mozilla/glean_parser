# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


from pathlib import Path


from glean_parser import lint
from glean_parser import parser


import util


import pytest


ROOT = Path(__file__).parent


def test_common_prefix():
    contents = [
        {
            "telemetry": {
                "network_latency": {
                    "type": "quantity",
                    "gecko_datapoint": "GC_NETWORK_LATENCY",
                    "unit": "ms",
                },
                "network_bandwidth": {
                    "type": "quantity",
                    "gecko_datapoint": "GC_NETWORK_BANDWIDTH",
                    "unit": "kbps",
                },
            }
        }
    ]
    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)

    errs = list(all_metrics)
    assert len(errs) == 0

    nits = lint.lint_metrics(all_metrics.value)

    assert len(nits) == 1
    assert nits[0].check_name == "COMMON_PREFIX"

    # Now make sure the override works
    contents[0]["no_lint"] = ["COMMON_PREFIX"]
    all_metrics = parser.parse_objects(contents)
    errs = list(all_metrics)
    assert len(errs) == 0

    nits = lint.lint_metrics(all_metrics.value)

    assert len(nits) == 0


def test_unit_in_name():
    contents = [
        {
            "telemetry": {
                "network_latency_ms": {"type": "timespan", "time_unit": "millisecond"},
                "memory_usage_mb": {
                    "type": "memory_distribution",
                    "memory_unit": "megabyte",
                },
                "width_pixels": {
                    "type": "quantity",
                    "gecko_datapoint": "WIDTH_PIXELS",
                    "unit": "pixels",
                },
            }
        }
    ]
    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)

    errs = list(all_metrics)
    assert len(errs) == 0

    nits = lint.lint_metrics(all_metrics.value)

    assert len(nits) == 3
    assert all(nit.check_name == "UNIT_IN_NAME" for nit in nits)

    # Now make sure the override works
    contents[0]["telemetry"]["network_latency_ms"]["no_lint"] = ["UNIT_IN_NAME"]
    all_metrics = parser.parse_objects(contents)
    errs = list(all_metrics)
    assert len(errs) == 0

    nits = lint.lint_metrics(all_metrics.value)

    assert len(nits) == 2


def test_category_generic():
    contents = [{"metrics": {"measurement": {"type": "boolean"}}}]
    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)

    errs = list(all_metrics)
    assert len(errs) == 0

    nits = lint.lint_metrics(all_metrics.value)

    assert len(nits) == 1
    assert nits[0].check_name == "CATEGORY_GENERIC"

    contents[0]["no_lint"] = ["CATEGORY_GENERIC"]
    all_metrics = parser.parse_objects(contents)
    errs = list(all_metrics)
    assert len(errs) == 0

    nits = lint.lint_metrics(all_metrics.value)

    assert len(nits) == 0


def test_combined():
    contents = [
        {
            "metrics": {
                "m_network_latency_ms": {
                    "type": "timespan",
                    "time_unit": "millisecond",
                },
                "m_memory_usage_mb": {
                    "type": "memory_distribution",
                    "memory_unit": "megabyte",
                },
                "m_width_pixels": {
                    "type": "quantity",
                    "gecko_datapoint": "WIDTH_PIXELS",
                    "unit": "pixels",
                },
            }
        }
    ]
    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)

    errs = list(all_metrics)
    assert len(errs) == 0

    nits = lint.lint_metrics(all_metrics.value)

    assert len(nits) == 5
    assert set(["COMMON_PREFIX", "CATEGORY_GENERIC", "UNIT_IN_NAME"]) == set(
        v.check_name for v in nits
    )


def test_baseline_restriction():
    contents = [
        {
            "user_data": {
                "counter": {"type": "counter", "send_in_pings": ["baseline"]},
                "string": {"type": "string", "send_in_pings": ["metrics", "baseline"]},
                "string2": {"type": "string", "send_in_pings": ["metrics"]},
            }
        }
    ]
    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)

    errs = list(all_metrics)
    assert len(errs) == 0

    nits = lint.lint_metrics(all_metrics.value)

    assert len(nits) == 2
    assert set(["BASELINE_PING"]) == set(v.check_name for v in nits)


def test_misspelling_pings():
    contents = [
        {
            "user_data": {
                "counter": {"type": "counter", "send_in_pings": ["metric"]},
                "string": {
                    "type": "string",
                    "lifetime": "application",
                    "send_in_pings": ["event"],
                },
                "string2": {
                    "type": "string",
                    "lifetime": "application",
                    "send_in_pings": ["metrics", "events"],
                },
            }
        }
    ]
    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)

    errs = list(all_metrics)
    assert len(errs) == 0

    nits = lint.lint_metrics(all_metrics.value)

    assert len(nits) == 2
    assert set(["MISSPELLED_PING"]) == set(v.check_name for v in nits)


def test_user_lifetime_expiration():
    """Test that expiring 'user' lifetime metrics generate a warning."""
    contents = [
        {
            "user_data": {
                "counter": {
                    "type": "counter",
                    "lifetime": "user",
                    "expires": "2100-01-01",
                    "no_lint": ["EXPIRATION_DATE_TOO_FAR"],
                },
                "string": {"type": "string", "lifetime": "user", "expires": "never"},
                "other": {"type": "string", "lifetime": "application"},
            }
        }
    ]

    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)

    errs = list(all_metrics)
    assert len(errs) == 0

    nits = lint.lint_metrics(all_metrics.value)

    assert len(nits) == 1
    assert set(["USER_LIFETIME_EXPIRATION"]) == set(v.check_name for v in nits)


def test_expired_metric():
    """Test that expiring 'ping' lifetime metrics generate a warning."""
    contents = [
        {
            "user_data": {
                "counter": {
                    "type": "counter",
                    "lifetime": "ping",
                    "expires": "1999-01-01",
                },
            }
        }
    ]

    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)

    errs = list(all_metrics)
    assert len(errs) == 0

    nits = lint.lint_metrics(all_metrics.value)

    assert len(nits) == 1
    assert set(["EXPIRED"]) == set(v.check_name for v in nits)


def test_expires_too_far_in_the_future():
    """Test that a `expires` dates too far in the future generates warnings"""
    contents = [
        {
            "user_data": {
                "too_far": {
                    "type": "counter",
                    "lifetime": "ping",
                    "expires": "2100-01-01",
                }
            }
        }
    ]

    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)

    errs = list(all_metrics)
    assert len(errs) == 0

    nits = lint.lint_metrics(all_metrics.value)

    assert len(nits) == 1
    assert set(["EXPIRATION_DATE_TOO_FAR"]) == set(v.check_name for v in nits)


def test_invalid_lifetime_for_metric_on_events_ping():
    """Test that a `ping` lifetime, non-event metric, fails when sent on the
    Metrics ping"""
    contents = [
        {
            "user_data": {
                "invalid_lifetime": {
                    "type": "counter",
                    "lifetime": "ping",
                    "send_in_pings": "events",
                }
            }
        }
    ]

    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)

    errs = list(all_metrics)
    assert len(errs) == 1


def test_translate_missing_input_files(tmpdir):
    with pytest.raises(FileNotFoundError):
        lint.glinter(
            [ROOT / "data" / "missing.yaml"],
            parser_config={"allow_reserved": True},
        )

    assert 0 == lint.glinter(
        [ROOT / "data" / "missing.yaml"],
        parser_config={"allow_reserved": True, "allow_missing_files": True},
    )


@pytest.mark.parametrize(
    "content,num_nits",
    [
        ({"search": {"bugs": [12345]}}, 1),
        ({"search": {"bugs": [12345], "no_lint": ["BUG_NUMBER"]}}, 0),
        ({"search": {"bugs": [12345]}, "no_lint": ["BUG_NUMBER"]}, 0),
    ],
)
def test_bug_number_pings(content, num_nits):
    """
    Test that using bug numbers (rather than URLs) in pings produce linting
    errors.
    """
    content["$schema"] = "moz://mozilla.org/schemas/glean/pings/1-0-0"
    content = util.add_required_ping(content)
    all_pings = parser.parse_objects([content])

    errs = list(all_pings)
    assert len(errs) == 0

    nits = lint.lint_metrics(all_pings.value)

    assert len(nits) == num_nits
    if num_nits > 0:
        assert set(["BUG_NUMBER"]) == set(v.check_name for v in nits)


def test_redundant_pings():
    """
    Test that name contains '-ping' or 'ping-' or 'ping' or 'custom' yields lint errors.
    """
    content = {"ping": {}}

    content = util.add_required_ping(content)
    all_pings = parser.parse_objects([content])
    errs = list(all_pings)
    assert len(errs) == 0

    nits = lint.lint_metrics(all_pings.value)
    assert len(nits) == 1
    assert set(["REDUNDANT_PING"]) == set(v.check_name for v in nits)


@pytest.mark.parametrize(
    "require_tags,expected_nits",
    [
        (False, 0),
        (True, 1),
    ],
)
def test_metric_no_tags(require_tags, expected_nits):
    """Test what happens when a metric has no tags (depends on parser configuration)"""
    metric = {
        "foo": {
            "bar": {
                "type": "boolean",
            },
        },
    }
    objs = parser.parse_objects([util.add_required(metric)])
    errs = list(objs)
    assert len(errs) == 0

    nits = lint.lint_metrics(objs.value, {"require_tags": require_tags})
    assert len(nits) == expected_nits
    if expected_nits:
        assert nits[0].check_name == "TAGS_REQUIRED"
        assert nits[0].name == "foo.bar"
        assert nits[0].msg == "Tags are required but no tags specified"


@pytest.mark.parametrize(
    "require_tags,expected_nits",
    [
        (False, 0),
        (True, 1),
    ],
)
def test_ping_no_tags(require_tags, expected_nits):
    """Test what happens when a metric has no tags (depends on parser configuration)"""
    objs = parser.parse_objects([util.add_required_ping({"search": {}})])
    errs = list(objs)
    assert len(errs) == 0

    nits = lint.lint_metrics(objs.value, {"require_tags": require_tags})
    assert len(nits) == expected_nits
    if expected_nits:
        assert nits[0].check_name == "TAGS_REQUIRED"
        assert nits[0].name == "search"
        assert nits[0].msg == "Tags are required but no tags specified"


@pytest.mark.parametrize(
    "tags,expected_nits",
    [
        (["apple"], 0),
        (["grapefruit"], 1),
    ],
)
def test_check_metric_tag_names(tags, expected_nits):
    """
    Test that specifying an invalid tag name inside a metric produces an error
    """
    metric = {
        "foo": {
            "bar": {
                "type": "boolean",
                "metadata": {"tags": tags},
            },
        },
    }
    defined_tags = {
        "$schema": "moz://mozilla.org/schemas/glean/tags/1-0-0",
        "apple": {"description": "apple is a banana"},
    }

    objs = parser.parse_objects([util.add_required(metric), defined_tags])
    errs = list(objs)
    assert len(errs) == 0

    nits = lint.lint_metrics(objs.value)
    assert len(nits) == expected_nits
    if expected_nits:
        assert nits[0].check_name == "INVALID_TAGS"
        assert nits[0].name == "foo.bar"
        assert nits[0].msg == "Invalid tags specified in metric: grapefruit"


@pytest.mark.parametrize(
    "tags,expected_nits",
    [
        (["apple"], 0),
        (["grapefruit"], 1),
    ],
)
def test_check_ping_tag_names(tags, expected_nits):
    """
    Test that specifying an invalid tag name inside a metric produces an error
    """
    defined_tags = {
        "$schema": "moz://mozilla.org/schemas/glean/tags/1-0-0",
        "apple": {"description": "apple is a banana"},
    }

    objs = parser.parse_objects(
        [util.add_required_ping({"search": {"metadata": {"tags": tags}}}), defined_tags]
    )
    errs = list(objs)
    assert len(errs) == 0

    nits = lint.lint_metrics(objs.value)
    assert len(nits) == expected_nits
    if expected_nits:
        assert nits[0].check_name == "INVALID_TAGS"
        assert nits[0].name == "search"
        assert nits[0].msg == "Invalid tags specified in ping: grapefruit"


def test_old_event_api():
    """Test that the 'glinter' reports issues with the old event API."""
    all_metrics = parser.parse_objects([ROOT / "data" / "old_event_api.yamlx"])
    errs = list(all_metrics)
    assert len(errs) == 0

    nits = lint.lint_metrics(all_metrics.value, parser_config={})
    assert len(nits) == 1
    assert nits[0].check_name == "OLD_EVENT_API"
    assert nits[0].name == "old_event.name"
    assert "Extra keys require a type" in nits[0].msg


def test_unknown_pings_lint():
    """Test that the 'glinter' reports issues with unknown pings in send_in_pings."""
    input = [ROOT / "data" / "unknown_ping_used.yaml", ROOT / "data" / "pings.yaml"]
    all_objects = parser.parse_objects(input)

    errs = list(all_objects)
    assert len(errs) == 0

    nits = lint.lint_metrics(all_objects.value, parser_config={})
    assert len(nits) == 2
    assert nits[0].check_name == "UNKNOWN_PING_REFERENCED"
    assert nits[0].name == "all_metrics.non_existent_ping"
    assert "does-not-exist" in nits[0].msg


@pytest.mark.parametrize(
    "metric, num_nits",
    [
        ({"metric": {"data_reviews": ["12345"]}}, 0),
        ({"metric": {"data_reviews": ["12345", "", "TODO"]}}, 1),
        ({"metric": {"data_reviews": [""]}}, 1),
        ({"metric": {"data_reviews": [""], "no_lint": ["EMPTY_DATAREVIEW"]}}, 0),
        ({"metric": {"data_reviews": ["TODO"]}}, 1),
        ({"metric": {"data_reviews": ["TODO"], "no_lint": ["EMPTY_DATAREVIEW"]}}, 0),
    ],
)
def test_empty_datareviews(metric, num_nits):
    """
    Test that the list of data reviews does not contain empty strings or TODO markers
    """
    content = {"category": metric}
    content = util.add_required(content)
    all_metrics = parser.parse_objects(content)

    errs = list(all_metrics)
    assert len(errs) == 0

    nits = lint.lint_metrics(all_metrics.value)

    assert len(nits) == num_nits
    if num_nits > 0:
        assert set(["EMPTY_DATAREVIEW"]) == set(v.check_name for v in nits)


@pytest.mark.parametrize(
    "metric, num_nits",
    [
        ({"metric": {"type": "quantity", "unit": "sheep"}}, 0),
        (
            {
                "metric": {
                    "type": "custom_distribution",
                    "unit": "quantillions",
                    "range_max": 100,
                    "bucket_count": 100,
                    "histogram_type": "linear",
                }
            },
            0,
        ),
        ({"metric": {"type": "string", "unit": "quantillions"}}, 1),
        ({"metric": {"type": "counter", "unit": "quantillions"}}, 1),
        (
            {
                "metric": {
                    "type": "string",
                    "unit": "quantillions",
                    "no_lint": ["UNEXPECTED_UNIT"],
                }
            },
            0,
        ),
    ],
)
def test_unit_on_metrics(metric, num_nits):
    content = {"category": metric}
    content = util.add_required(content)
    all_metrics = parser.parse_objects(content)

    errs = list(all_metrics)
    assert len(errs) == 0

    nits = lint.lint_metrics(all_metrics.value)

    assert len(nits) == num_nits
    if num_nits > 0:
        assert set(["UNEXPECTED_UNIT"]) == set(v.check_name for v in nits)
