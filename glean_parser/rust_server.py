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

from . import __version__
from . import metrics
from . import util

# Adding a metric here will require updating the `generate_metric_type` function
# and require adjustments to `metrics` variables the the template.
SUPPORTED_METRIC_TYPES: list[str] = ["string", "quantity", "event", "datetime", "boolean"]

def generate_ping_type_name(ping_name: str) -> str:
    """Returns camel-case string of ping name."""
    return f"{util.Camelize(ping_name)}Ping"

def generate_ping_events_type_name(ping_name: str) -> str:
    """Returns camel-case event type name."""
    return f"{util.Camelize(ping_name)}PingEvent"

def generate_event_type_name(metric: metrics.Metric) -> str:
    """Returns camel-case string of event type."""
    return f"{util.Camelize(metric.category)}{util.Camelize(metric.name)}Event"

def generate_metric_name(metric: metrics.Metric) -> str:
    """Returns camel-case string of metric name."""
    return f"{metric.category}.{metric.name}"

def generate_extra_name(extra: str) -> str:
    """Returns camel-case string of extra value."""
    return util.Camelize(extra)

def generate_metric_argument_name(metric: metrics.Metric) -> str:
    """Returns camel-case string of metric argument name."""
    return f"{util.Camelize(metric.category)}{util.Camelize(metric.name)}"

def generate_metric_type(metric_type: str) -> str:
    """Return string representation of metric type in Rust."""
    match metric_type:
        case "quantity":
            return "u64"
        case "string": 
            return "String"
        case "boolean": 
            return "bool"
        case "datetime": 
            return "chrono::DateTime"
        case _: 
            print(f"❌ Unable to generate Rust type from metric type: {metric_type}")
            exit()
            return "NONE"

def clean_string(s: str) -> str:
    """Strip strings of any newlines and trailing space."""
    return s.replace("\n", " ").rstrip()

def output_rust(
        objs: metrics.ObjectTree, output_dir: Path, options: dict[str, Any] | None
    ) -> None:
    """
    Given a tree of objects, output Rust code to `output_dir`.

    The output is a single file containing all the code for assembling pings with
    metrics, serializing, and submitting.

    :param objects: A tree of objects (metrics and pings) as returned from
        `parser.parse_objects`.
    :param output_dir: Path to an output directory to write to.
    :param options: Optional dictionary of additional configuration options
    """

    template = util.get_jinja2_template(
        "rust_server.jinja2",
        filters=(
            ("ping_type_name", generate_ping_type_name),
            ("ping_events_type_name", generate_ping_events_type_name),
            ("event_type_name", generate_event_type_name),
            ("event_extra_name", generate_extra_name),
            ("metric_name", generate_metric_name),
            ("metric_argument_name", generate_metric_argument_name),
            ("go_metric_type", generate_metric_type),
            ("clean_string", clean_string),
            ),
        )
    
    # Unique list of event metrics used in any ping.
    event_metrics: list[metrics.Metric] = []

    # Go though all metrics in objs and build a mpa of 
    # ping-> list of metric categories->list of metrics
    # for easier processing in the template.
    ping_to_metrics: dict[str, dict[str, list[metrics.Metric]]] = defaultdict(dict)

    for _category_key, category_val in objs.items():
        for _metric_name, metric in category_val.items():
            if isinstance(metric, metrics.Metric):
                if metric.type not in SUPPORTED_METRIC_TYPES:
                    print(
                        "❌ Ignoring unsupported metric type: "
                        + f"{metric.type}:{metric.name}."
                        + " Reach out to Glean team to add support for this"
                        + " metric type."
                        )
                    continue
                
                for ping in metric.send_in_pings:
                    if metric.type == "event" and metric not in event_metrics:
                        event_metrics.append(metric)
                    