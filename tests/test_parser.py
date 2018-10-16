# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from pathlib import Path

import jsonschema
import pytest

from glean_parser import parser, metrics


ROOT = Path(__file__).parent


def add_schema(chunk):
    chunk['$schema'] = parser._get_metrics_schema()['$id']
    return chunk


def test_parser():
    """Test the basics of parsing a single file."""
    all_metrics = parser.parse_metrics(ROOT / "data" / "core.yaml")
    for group_key, group_val in all_metrics.items():
        for metric_key, metric_val in group_val.items():
            assert isinstance(metric_val, metrics.Metric)


def test_parser_invalid():
    """Test the basics of parsing a single file."""
    with pytest.raises(ValueError):
        parser.parse_metrics(ROOT / "data" / "invalid.yaml")


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

    with pytest.raises(ValueError) as e:
        parser._load_metrics_file(contents[0])
    assert '$schema key must be set to' in str(e)


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

    all_metrics = parser._merge_metrics(contents)

    assert set(all_metrics['group1'].keys()) == set(['metric1', 'metric2', 'metric4'])
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

    with pytest.raises(ValueError) as e:
        parser._merge_metrics(contents)
    assert 'Duplicate metric name' in str(e)


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
        with pytest.raises(jsonschema.exceptions.ValidationError) as e:
            parser._load_metrics_file(content)
        assert 'definitions/snake_case' in str(e.value)
