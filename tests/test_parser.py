# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from pathlib import Path

from glean_parser import metrics
from glean_parser import parser

import util


ROOT = Path(__file__).parent


def test_parser():
    """Test the basics of parsing a single file."""
    all_metrics = parser.parse_metrics(ROOT / "data" / "core.yaml")
    for err in all_metrics:
        pass
    for category_key, category_val in all_metrics.value.items():
        for metric_key, metric_val in category_val.items():
            assert isinstance(metric_val, metrics.Metric)
            assert isinstance(metric_val.lifetime,
                              metrics.Lifetime)


def test_parser_invalid():
    """Test the basics of parsing a single file."""
    all_metrics = parser.parse_metrics(ROOT / "data" / "invalid.yaml")
    errors = list(all_metrics)
    assert len(errors) == 1
    assert 'could not determine a constructor for the tag' in errors[0]


def test_parser_schema_violation():
    """1507792"""
    all_metrics = parser.parse_metrics(ROOT / "data" / "schema-violation.yaml")
    errors = list(all_metrics)
    print('\n'.join(errors))
    assert len(errors) == 4


def test_parser_empty():
    """1507792: Get a good error message if the metrics.yaml file is empty."""
    all_metrics = parser.parse_metrics(ROOT / "data" / "empty.yaml")
    errors = list(all_metrics)
    assert len(errors) == 1
    assert 'metrics file can not be empty' in errors[0]


def test_invalid_schema():
    all_metrics = parser.parse_metrics([{
        "$schema": "This is wrong"
    }])
    errors = list(all_metrics)
    assert any('key must be set to' in str(e) for e in errors)


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

    all_metrics = parser.parse_metrics(contents)
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

    all_metrics = parser.parse_metrics(contents)
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
        metrics = parser._load_metrics_file(content)
        errors = list(metrics)
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
    metrics = parser.parse_metrics(contents)
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
    all_metrics = parser.parse_metrics(contents)
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
    all_metrics = parser.parse_metrics(contents)
    errors = list(all_metrics)
    assert len(errors) == 1
    assert "On instance['category']['metric']['lifetime']" in errors[0]
