# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

import datetime

import pytest

from glean_parser import parser
from glean_parser import metrics


def test_metrics_match_schema():
    """
    Make sure the supported set of metric types in the schema matches the set
    in `metrics.py`
    """
    schema, validator = parser._get_schema(parser.METRICS_ID)

    assert (set(metrics.Metric.metric_types.keys()) ==
            set(schema['definitions']['metric']['properties']['type']['enum']))


def test_enforcement():
    """
    Test dataclasses enforcement.
    """
    with pytest.raises(TypeError):
        metrics.Boolean()

    # Python dataclasses don't actually validate any types, so we
    # delegate to jsonschema
    with pytest.raises(ValueError):
        metrics.Boolean(
            type='boolean',
            category='category',
            name='metric',
            bugs=[42],
            description=42,
            notification_emails=['nobody@example.com'],
            expires='never'
        )


def test_expires():
    """
    Test that expires is parsed correctly
    """
    for date, expired in [
            ('2018-06-10', True),
            (datetime.datetime.utcnow().date().isoformat(), True),
            ('3000-01-01', False)
    ]:
        m = metrics.Boolean(
            type='boolean',
            category='category',
            name='metric',
            bugs=[42],
            expires=date,
            notification_emails=['nobody@example.com'],
            description='description...',
        )
        assert m.is_expired() == expired

    with pytest.raises(ValueError):
        m = metrics.Boolean(
            type='boolean',
            category='category',
            name='metric',
            bugs=[42],
            expires='foo',
            notification_emails=['nobody@example.com'],
            description='description...',
        )


def test_timespan_time_unit():
    """
    Test that the timespan's time_unit is coerced to an enum.
    """
    m = metrics.Timespan(
        type='timespan',
        category='category',
        name='metric',
        bugs=[42],
        time_unit='day',
        notification_emails=['nobody@example.com'],
        description='description...',
        expires='never',
    )
    assert isinstance(m.time_unit, metrics.TimeUnit)
    assert m.time_unit == metrics.TimeUnit.day

    with pytest.raises(AttributeError):
        m = metrics.Timespan(
            type='timespan',
            category='category',
            name='metric',
            bugs=[42],
            time_unit='foo',
            notification_emails=['nobody@example.com'],
            description='description...',
            expires='never',
        )


def test_identifier():
    """
    Test that the identifier is created correctly.
    """
    m = metrics.Timespan(
        type='timespan',
        category='category',
        name='metric',
        bugs=[42],
        time_unit='day',
        notification_emails=['nobody@example.com'],
        description='description...',
        expires='never',
    )

    assert m.identifier() == "category.metric"


def test_identifier_glean_category():
    """
    Test that the glean-internal identifier is created correctly.
    """
    m = metrics.Timespan(
        type='timespan',
        category=metrics.Metric.glean_internal_metric_cat,
        name='metric',
        bugs=[42],
        time_unit='day',
        notification_emails=['nobody@example.com'],
        description='description...',
        expires='never',
    )

    assert m.identifier() == "metric"


def test_reserved_extra_keys():
    """
    Test that extra keys starting with 'glean.' are rejected for
    non-internal metrics.
    """
    with pytest.raises(ValueError):
        metrics.Event(
            type='event',
            category='category',
            name='metric',
            bugs=[42],
            notification_emails=['nobody@example.com'],
            description='description...',
            expires='never',
            extra_keys={'glean.internal': {'description': 'foo'}}
        )

    metrics.Event(
        type='event',
        category='category',
        name='metric',
        bugs=[42],
        notification_emails=['nobody@example.com'],
        description='description...',
        expires='never',
        extra_keys={'glean.internal': {'description': 'foo'}},
        _config={'allow_reserved': True}
    )
