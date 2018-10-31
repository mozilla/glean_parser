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
import enum
from typing import Any, Dict, List, Type, Union

import isodate

from . import parser


class Lifetime(enum.Enum):
    ping = 0
    user = 1
    application = 2


@dataclass
class Metric:
    def __init_subclass__(cls, **kwargs):
        # Create a mapping of all of the subclasses of this class
        if cls not in _metric_types and hasattr(cls, 'typename'):
            _metric_types[cls.typename] = cls
        super().__init_subclass__(**kwargs)

    @classmethod
    def make_metric(
            cls,
            category: str,
            name: str,
            metric_info: Dict[str, Any],
            validated: bool = False
    ):
        """
        Given a metric_info dictionary from metrics.yaml, return a metric
        instance.
        """
        metric_type = metric_info['type']
        return _metric_types[metric_type](
            category=category,
            name=name,
            _validated=validated,
            **metric_info
        )

    def serialize(self):
        """
        Serialize the metric back to JSON object model.
        """
        d = dataclasses.asdict(self)
        # Convert enum fields back to strings
        for key, val in d.items():
            if isinstance(val, enum.Enum):
                d[key] = d[key].name
        del d['name']
        del d['category']
        return d

    def __post_init__(
            self,
            _validated: bool
    ):
        # Convert enum fields to Python enums
        for f in dataclasses.fields(self):
            if isinstance(f.type, type) and issubclass(f.type, enum.Enum):
                setattr(
                    self,
                    f.name,
                    getattr(f.type, getattr(self, f.name))
                )

        if self.expires_after_build_date is not None:
            setattr(
                self,
                'expires_after_build_date',
                isodate.parse_date(self.expires_after_build_date)
            )

        if not _validated:
            data = {
                self.category: {
                    self.name: self.serialize()
                }
            }
            for error in parser.validate(data):
                raise ValueError(error)

    type: str

    # Metadata
    category: str
    name: str
    bugs: List[Union[int, str]]
    description: str
    notification_emails: List[str]
    reviews: List[str] = field(default_factory=list)
    version: int = 0

    # Ping-related properties
    lifetime: Lifetime = Lifetime.ping
    send_in_pings: List[str] = field(default_factory=lambda: ['default'])

    # Expiry
    disabled: bool = False
    expires_after_build_date: Union[datetime.date, None] = None

    # Labeled metrics
    labeled: bool = False
    labels: List[str] = field(default_factory=list)

    # Implementation detail
    _validated: InitVar[bool] = False


_metric_types: Dict[str, Type[Metric]] = {}


@dataclass
class Boolean(Metric):
    typename = 'boolean'


@dataclass
class String(Metric):
    typename = 'string'


@dataclass
class StringList(Metric):
    typename = 'string_list'


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

    def __post_init__(self, *args):
        super().__post_init__(*args)

        if not self.denominator:
            raise ValueError(
                "denominator is required on all use_counter metrics"
            )


@dataclass
class Usage(Metric):
    typename = 'usage'


@dataclass
class Rate(Metric):
    typename = 'rate'


@dataclass
class Event(Metric):
    typename = 'event'

    objects: List[str] = field(default_factory=list)
    extra_keys: Dict[str, str] = field(default_factory=dict)

    @property
    def allowed_extra_keys(self):
        return list(self.extra_keys.keys())


@dataclass
class Uuid(Metric):
    typename = 'uuid'
