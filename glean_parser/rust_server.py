# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Outputter to generate server Rust code for collecting events.

This outputter is different from the rest of the outputters in that the code it
generates does not use the Glean SDK. It is meant to be used to collect events
in server-side environments. In these environments, SDK assumptions that define measurement
windows and connectivity don't hold.
Generated code takes care of assembling pings with metrics, and serializing to messages
conforming to Glean schema.

Warning: this outputter supports limited set of metrics,
see `SUPPORTED_METRIC_TYPES` below.

Generated code creates two methods for each ping (`RecordPingX` and `RecordPingXWithoutUserInfo`)
that are used for submitting (logging) them.
If pings have `event` metrics assigned, they can be passed to these methods.
"""

from collections import defaultdict
from pathlib import Path
from typing import Any

# Adding a metric here will require updating the `generate_metric_type` function
# and require adjustments to `metrics` variables the the template.
SUPPORTED_METRIC_TYPES: list[str] = ["string", "quantity", "event", "datetime", "boolean"]