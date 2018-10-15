# -*- coding: utf-8 -*-

import jsonschema
import pytest

from glean_parser import parser
from glean_parser import metrics


def test_metrics_match_schema():
    """
    Make sure the supported set of metric types in the schema matches the set
    in `metrics.py`
    """
    schema = parser._get_metrics_schema()

    assert (set(metrics.Metric.metric_types.keys()) ==
            set(schema['definitions']['metric']['properties']['type']['enum']))


def test_enforcement():
    """
    Test dataclasses enforcement.
    """
    with pytest.raises(TypeError):
        metrics.Boolean()

    # Python dataclasses don't actually validate any types
    with pytest.raises(jsonschema.exceptions.ValidationError):
        metrics.Boolean(
            type='boolean',
            group_name='group',
            name='metric',
            bugs=[42],
            description=42,
        )
