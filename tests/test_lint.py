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
                "string": {"type": "string", "send_in_pings": ["event"]},
                "string2": {"type": "string", "send_in_pings": ["metrics", "events"]},
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


def test_yaml_lint(capsys):
    """Tests yamllint on files with nits."""
    file_paths = [ROOT / "data" / "core.yaml", ROOT / "data" / "yaml_nits.yamlx"]

    nits = lint.lint_yaml_files(file_paths)

    assert len(nits) == 3
    # The second rule is empty because it's a syntax error.
    assert set(["indentation", None, "trailing-spaces"]) == set(v.rule for v in nits)

    captured = capsys.readouterr()
    lines = captured.out.split("\n")
    for line in lines:
        if line.strip() == "":
            continue
        assert "yaml_nits.yamlx" in line
        assert "core.yaml" not in line


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
    """Test that expiring 'user' lifetime metrics generate a warning."""
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
        ({"ping": {"bugs": [12345]}}, 1),
        ({"ping": {"bugs": [12345], "no_lint": ["BUG_NUMBER"]}}, 0),
        ({"ping": {"bugs": [12345]}, "no_lint": ["BUG_NUMBER"]}, 0),
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
