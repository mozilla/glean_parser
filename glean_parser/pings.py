# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Classes for managing the description of pings.
"""

import dataclasses
from dataclasses import dataclass, field, InitVar
from typing import List, Union

from . import parser


RESERVED_PING_NAMES = [
    'baseline', 'metrics', 'events'
]


@dataclass
class Ping:
    def __post_init__(self, _validated):
        # _validated indicates whether this metric has already been jsonschema
        # validated (but not any of the Python-level validation).
        if not _validated:
            data = {
                '$schema': parser.PINGS_ID,
                self.name: self.serialize()
            }
            for error in parser.validate(data):
                raise ValueError(error)

    type = 'ping'
    name: str
    description: str
    bugs: List[Union[int, str]]
    description: str
    notification_emails: List[str]
    data_reviews: List[str] = field(default_factory=list)
    include_client_id: bool = False

    _validated: InitVar[bool] = False

    def serialize(self):
        """
        Serialize the metric back to JSON object model.
        """
        d = dataclasses.asdict(self)
        del d['name']
        return d
