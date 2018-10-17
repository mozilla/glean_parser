# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from pathlib import Path

from glean_parser import metrics
from glean_parser import parser


ROOT = Path(__file__).parent


def add_schema(chunk):
    chunk['$schema'] = parser._get_metrics_schema()['$id']
    return chunk


def test_parser():
    """Test the basics of parsing a single file."""
    all_metrics = parser.parse_metrics(ROOT / "data" / "core.yaml")
    for err in all_metrics:
        pass
    for group_key, group_val in all_metrics.value.items():
        for metric_key, metric_val in group_val.items():
            assert isinstance(metric_val, metrics.Metric)


def test_parser_invalid():
    """Test the basics of parsing a single file."""
    all_metrics = parser.parse_metrics(ROOT / "data" / "invalid.yaml")
    errors = list(all_metrics)
    assert len(errors) == 1
    assert 'could not determine a constructor for the tag' in errors[0]


def test_no_schema():
    """Expect error if no $schema specified in the input file."""
    contents = [
        {
            'group1': {
                'metric1': {
                    'type': 'string',
                    'bugs': [0],
                },
            },
        },
    ]

    all_metrics = parser._load_metrics_file(contents[0])
    errors = list(all_metrics)
    assert len(errors) == 1
    assert '$schema key must be set to' in errors[0]


def test_merge_metrics():
    """Merge multiple metrics.yaml files"""
    contents = [
        {
            'group1': {
                'metric1': {
                    'type': 'string',
                    'bugs': [0],
                },
                'metric2': {
                    'type': 'string',
                    'bugs': [1],
                },
            },
            'group2': {
                'metric3': {
                    'type': 'counter',
                    'bugs': [2],
                },
            },
        },
        {
            'group1': {
                'metric4': {
                    'type': 'counter',
                    'bugs': [3],
                },
            },
            'group3': {
                'metric5': {
                    'type': 'counter',
                    'bugs': [4],
                },
            },
        },
    ]
    contents = [add_schema(x) for x in contents]

    all_metrics = parser.parse_metrics(contents)
    list(all_metrics)
    all_metrics = all_metrics.value

    assert set(all_metrics['group1'].keys()) == set(
        ['metric1', 'metric2', 'metric4']
    )
    assert set(all_metrics['group2'].keys()) == set(['metric3'])
    assert set(all_metrics['group3'].keys()) == set(['metric5'])


def test_merge_metrics_clash():
    """Merge multiple metrics.yaml files with conflicting metric names."""
    contents = [
        {
            'group1': {
                'metric1': {
                    'type': 'string',
                    'bugs': [0],
                },
            },
        },
        {
            'group1': {
                'metric1': {
                    'type': 'counter',
                    'bugs': [3]
                },
            },
        },
    ]
    contents = [add_schema(x) for x in contents]

    all_metrics = parser.parse_metrics(contents)
    errors = list(all_metrics)
    assert len(errors) == 1
    assert 'Duplicate metric name' in errors[0]


def test_snake_case_enforcement():
    """Expect exception if names aren't in snake case."""
    contents = [
        {
            'groupWithCamelCase': {
                'metric': {
                    'type': 'string',
                    'bugs': [0],
                },
            },
        },
        {
            'group': {
                'metricWithCamelCase': {
                    'type': 'string',
                    'bugs': [0],
                },
            },
        },
    ]

    for content in contents:
        add_schema(content)
        metrics = parser._load_metrics_file(content)
        errors = list(metrics)
        assert len(errors) == 1
        assert 'definitions/snake_case' in errors[0]


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

    metrics = parser.parse_metrics(contents)
    errors = list(metrics)
    assert len(errors) == 5
