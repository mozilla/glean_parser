# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from pathlib import Path
import textwrap

import pytest
from jsonschema import _utils

from glean_parser import metrics
from glean_parser import parser

import util


ROOT = Path(__file__).parent


def test_parser():
    """Test the basics of parsing a single file."""
    all_metrics = parser.parse_objects([
        ROOT / "data" / "core.yaml",
        ROOT / "data" / "pings.yaml"
    ], config={'allow_reserved': True})

    errs = list(all_metrics)
    assert len(errs) == 0

    for category_key, category_val in all_metrics.value.items():
        if category_key == 'pings':
            continue
        for metric_key, metric_val in category_val.items():
            assert isinstance(metric_val, metrics.Metric)
            assert isinstance(metric_val.lifetime, metrics.Lifetime)
            if getattr(metric_val, 'labels', None) is not None:
                assert isinstance(metric_val.labels, set)

    pings = all_metrics.value['pings']
    assert pings['custom_ping'].name == 'custom_ping'
    assert pings['custom_ping'].include_client_id is False
    assert pings['really_custom_ping'].name == 'really_custom_ping'
    assert pings['really_custom_ping'].include_client_id is True


def test_parser_invalid():
    """Test the basics of parsing a single file."""
    all_metrics = parser.parse_objects(ROOT / "data" / "invalid.yaml")
    errors = list(all_metrics)
    assert len(errors) == 1
    assert 'could not determine a constructor for the tag' in errors[0]


def test_parser_schema_violation():
    """1507792"""
    all_metrics = parser.parse_objects(ROOT / "data" / "schema-violation.yaml")
    errors = list(all_metrics)

    found_errors = set(
        str(error).split('\n', 1)[1].strip().replace(' ', '')
        for error in errors
    )

    expected_errors = [
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
        gleantest.lifetime:
          test_event_inv_lt:
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
        """
    ]

    expected_errors = set(
        _utils.indent(textwrap.dedent(x)).strip().replace(' ', '')
        for x in expected_errors
    )

    assert sorted(list(found_errors)) == sorted(list(expected_errors))


def test_parser_empty():
    """1507792: Get a good error message if the metrics.yaml file is empty."""
    all_metrics = parser.parse_objects(ROOT / "data" / "empty.yaml")
    errors = list(all_metrics)
    assert len(errors) == 1
    assert 'file can not be empty' in errors[0]


def test_invalid_schema():
    all_metrics = parser.parse_objects([{
        "$schema": "This is wrong"
    }])
    errors = list(all_metrics)
    print(errors)
    assert any('key must be one of' in str(e) for e in errors)


def test_merge_metrics():
    """Merge multiple metrics.yaml files"""
    contents = [
        {
            'category1': {
                'metric1': {},
                'metric2': {},
            },
            'category2': {
                'metric3': {},
            },
        },
        {
            'category1': {
                'metric4': {},
            },
            'category3': {
                'metric5': {},
            },
        },
    ]
    contents = [util.add_required(x) for x in contents]

    all_metrics = parser.parse_objects(contents)
    list(all_metrics)
    all_metrics = all_metrics.value

    assert set(all_metrics['category1'].keys()) == set(
        ['metric1', 'metric2', 'metric4']
    )
    assert set(all_metrics['category2'].keys()) == set(['metric3'])
    assert set(all_metrics['category3'].keys()) == set(['metric5'])


def test_merge_metrics_clash():
    """Merge multiple metrics.yaml files with conflicting metric names."""
    contents = [
        {
            'category1': {
                'metric1': {},
            },
        },
        {
            'category1': {
                'metric1': {},
            },
        },
    ]
    contents = [util.add_required(x) for x in contents]

    all_metrics = parser.parse_objects(contents)
    errors = list(all_metrics)
    assert len(errors) == 1
    assert 'Duplicate metric name' in errors[0]


def test_snake_case_enforcement():
    """Expect exception if names aren't in snake case."""
    contents = [
        {
            'categoryWithCamelCase': {
                'metric': {}
            },
        },
        {
            'category': {
                'metricWithCamelCase': {}
            },
        },
    ]

    for content in contents:
        util.add_required(content)
        errors = list(parser._load_file(content))
        assert len(errors) == 1


def test_multiple_errors():
    """Make sure that if there are multiple errors, we get all of them."""
    contents = [
        {
            'camelCaseName': {
                'metric': {
                    'type': 'unknown',
                },
            },
        },
    ]

    contents = [util.add_required(x) for x in contents]
    metrics = parser.parse_objects(contents)
    errors = list(metrics)
    assert len(errors) == 2


def test_required_denominator():
    """denominator is required on use_counter"""
    contents = [
        {
            'category': {
                'metric': {
                    'type': 'use_counter',
                },
            },
        },
    ]

    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)
    errors = list(all_metrics)
    assert len(errors) == 1
    assert 'denominator is required' in errors[0]


def test_event_must_be_ping_lifetime():
    contents = [
        {
            'category': {
                'metric': {
                    'type': 'event',
                    'lifetime': 'user'
                },
            },
        },
    ]

    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)
    errors = list(all_metrics)
    assert len(errors) == 1
    assert "Event metrics must have ping lifetime" in errors[0]


def test_parser_reserved():
    contents = [
        {
            'glean.baseline': {
                'metric': {
                    'type': 'string',
                },
            },
        },
    ]

    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)
    errors = list(all_metrics)
    assert len(errors) == 1
    assert "For category 'glean.baseline'" in errors[0]

    all_metrics = parser.parse_objects(contents, {'allow_reserved': True})
    errors = list(all_metrics)
    assert len(errors) == 0


def invalid_in_category(name):
    return [
        {
            name: {
                'metric': {
                    'type': 'string',
                },
            },
        },
    ]


def invalid_in_name(name):
    return [
        {
            'baseline': {
                name: {
                    'type': 'string',
                },
            },
        },
    ]


def invalid_in_label(name):
    return [
        {
            'baseline': {
                'metric': {
                    'type': 'string',
                    'labels': [name]
                },
            },
        },
    ]


@pytest.mark.parametrize('location', [
    invalid_in_category,
    invalid_in_name,
    invalid_in_label
])
@pytest.mark.parametrize('name', [
    "name/with_slash",
    "name#with_pound",
    "this_name_is_too_long_and_shouldnt_be_used",
    ""
])
def test_invalid_names(location, name):
    contents = location(name)
    contents = [util.add_required(x) for x in contents]
    all_metrics = parser.parse_objects(contents)
    errors = list(all_metrics)
    assert len(errors) == 1
    assert name in errors[0]
