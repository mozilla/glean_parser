# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Classes for each of the high-level metric types.
"""

import dataclasses
from dataclasses import dataclass, field, InitVar
import datetime
from typing import List, Union

import isodate
import jsonschema

from . import parser


@dataclass
class Metric:
    metric_types = {}

    def __init_subclass__(cls, **kwargs):
        # Create a mapping of all of the subclasses of this class
        if cls not in Metric.metric_types and hasattr(cls, 'typename'):
            Metric.metric_types[cls.typename] = cls
        super().__init_subclass__(**kwargs)

    @classmethod
    def make_metric(cls, group_name, name, metric_info, validated=False):
        """
        Given a metric_info dictionary from metrics.yaml, return a metric
        instance.
        """
        metric_type = metric_info['type']
        return cls.metric_types[metric_type](
            group_name=group_name,
            name=name,
            _validated=validated,
            **metric_info
        )

    def serialize(self):
        """
        Serialize the metric back to JSON object model.
        """
        d = dataclasses.asdict(self)
        del d['name']
        del d['group_name']
        return d

    def __post_init__(self, expires_after_build_date, _validated):
        if not _validated:
            schema = parser._get_metrics_schema()
            data = {
                self.group_name: {
                    self.name: self.serialize()
                }
            }
            jsonschema.validate(data, schema)
        if expires_after_build_date is not None:
            self.expires_after_build_date = isodate.parse_date(
                expires_after_build_date
            )

    type: str

    # Metadata
    group_name: str
    name: str
    bugs: List[Union[int, str]]
    description: str = ''
    version: int = 0
    notification_emails: List[str] = field(default_factory=list)
    review: List[str] = field(default_factory=list)

    # Ping-related properties
    user_property: bool = False
    application_property: bool = False
    send_in_pings: List[str] = field(default_factory=lambda: ['default'])

    # Expiry
    disabled: bool = False
    expires_after_build_date: InitVar[datetime.date] = None

    # Labeled metrics
    labeled: bool = False
    labels: List[str] = field(default_factory=list)

    # Implementation detail
    _validated: InitVar[bool] = False


@dataclass
class Boolean(Metric):
    typename = 'boolean'


@dataclass
class String(Metric):
    typename = 'string'
    max_length: int = 256


@dataclass
class StringList(Metric):
    typename = 'string_list'
    max_length: int = 256
    max_entries: int = 256


@dataclass
class Enumeration(Metric):
    typename = 'enumeration'
    values: List[str] = field(default_factory=list)


@dataclass
class Counter(Metric):
    typename = 'counter'


@dataclass
class TimeBase(Metric):
    time_unit: str = 'millisecond'


@dataclass
class Timespan(TimeBase):
    typename = 'timespan'


@dataclass
class TimingDistribution(TimeBase):
    typename = 'timing_distribution'


@dataclass
class Datetime(TimeBase):
    typename = 'datetime'


@dataclass
class UseCounter(Metric):
    typename = 'use_counter'
    denominator: str = ''


@dataclass
class Usage(Metric):
    typename = 'usage'


@dataclass
class Rate(Metric):
    typename = 'rate'


@dataclass
class Event(Metric):
    typename = 'event'
