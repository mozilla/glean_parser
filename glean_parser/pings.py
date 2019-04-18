# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Classes for managing the description of pings.
"""

from dataclasses import dataclass


RESERVED_PING_NAMES = [
    'baseline', 'metrics', 'events'
]


@dataclass
class Ping:
    type = 'ping'
    name: str
    description: str
    include_client_id: bool = False
