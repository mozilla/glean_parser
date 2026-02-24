# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Outputter to generate server Go code for collecting events.

This outputter is different from the rest of the outputters in that the code it
generates does not use the Glean SDK. It is meant to be used to collect events
in server-side environments. In these environments SDK assumptions to measurement
window and connectivity don't hold.
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
from typing import Any, Dict, Optional, List

from . import __version__
from . import metrics
from . import util

# Adding a metric here will require updating the `generate_metric_type` function
# and require adjustments to `metrics` variables the the template.
SUPPORTED_METRIC_TYPES = [
    "string",
    "quantity",
    "event",
    "datetime",
    "boolean",
    "string_list",
    "object",
]


def generate_ping_type_name(ping_name: str) -> str:
    return f"{util.Camelize(ping_name)}Ping"


def generate_ping_events_type_name(ping_name: str) -> str:
    return f"{util.Camelize(ping_name)}PingEvent"


def generate_event_type_name(metric: metrics.Metric) -> str:
    return f"{util.Camelize(metric.category)}{util.Camelize(metric.name)}Event"


def generate_metric_name(metric: metrics.Metric) -> str:
    return f"{metric.category}.{metric.name}"


def generate_extra_name(extra: str) -> str:
    return util.Camelize(extra)


def generate_metric_argument_name(metric: metrics.Metric) -> str:
    return f"{util.Camelize(metric.category)}{util.Camelize(metric.name)}"


def generate_metric_type(metric_type: str) -> str:
    if metric_type == "quantity":
        return "int64"
    elif metric_type == "string":
        return "string"
    elif metric_type == "boolean":
        return "bool"
    elif metric_type == "datetime":
        return "time.Time"
    elif metric_type == "string_list":
        return "[]string"
    elif metric_type == "object":
        # Object types are handled specially - the actual type name is generated
        # from the metric name (e.g., ActivityStreamTilesObject)
        return "object"
    else:
        print("❌ Unable to generate Go type from metric type: " + metric_type)
        exit
        return "NONE"


def generate_object_type_name(metric: metrics.Metric) -> str:
    """Generate the Go type name for an object metric."""
    return f"{util.Camelize(metric.category)}{util.Camelize(metric.name)}Object"


def schema_type_to_go_type(schema: Dict[str, Any], indent: int = 0) -> str:
    """
    Convert a JSON schema type definition to a Go type string.

    :param schema: JSON schema definition (e.g., from metric.structure)
    :param indent: Current indentation level for nested structs
    :return: Go type string
    """
    schema_type = schema.get("type")

    if schema_type == "string":
        return "string"
    elif schema_type == "number":
        return "float64"
    elif schema_type == "boolean":
        return "bool"
    elif schema_type == "array":
        items_schema = schema.get("items", {})
        item_type = schema_type_to_go_type(items_schema, indent)
        return f"[]{item_type}"
    elif schema_type == "object":
        properties = schema.get("properties", {})
        if not properties:
            return "map[string]interface{}"

        indent_str = "\t" * (indent + 1)
        fields = []
        for prop_name, prop_schema in properties.items():
            if "oneOf" in prop_schema:
                print(
                    f"⚠️  Warning: oneOf not supported, using interface{{}} for '{prop_name}'"
                )
                field_type = "interface{}"
            else:
                field_type = schema_type_to_go_type(prop_schema, indent + 1)

            field_name = util.Camelize(prop_name)
            json_tag = f'`json:"{prop_name}"`'
            fields.append(f"{indent_str}{field_name} {field_type} {json_tag}")

        fields_str = "\n".join(fields)
        close_indent = "\t" * indent
        return f"struct {{\n{fields_str}\n{close_indent}}}"
    else:
        print(f"⚠️  Warning: Unknown schema type '{schema_type}', using interface{{}}")
        return "interface{}"


def generate_object_struct_definition(metric: metrics.Metric) -> str:
    """
    Generate a complete Go struct definition for an object metric.

    :param metric: The object metric
    :return: Go struct definition as a string
    """
    type_name = generate_object_type_name(metric)

    if not hasattr(metric, "structure") or not metric.structure:
        print(f"⚠️  Warning: Object metric {metric.name} has no structure")
        return f"type {type_name} interface{{}}"

    schema_type = metric.structure.get("type")

    if schema_type == "array":
        items_schema = metric.structure.get("items", {})
        item_type = schema_type_to_go_type(items_schema, 0)
        return f"type {type_name} []{item_type}"
    elif schema_type == "object":
        properties = metric.structure.get("properties", {})
        if not properties:
            return f"type {type_name} map[string]interface{{}}"

        fields = []
        for prop_name, prop_schema in properties.items():
            if "oneOf" in prop_schema:
                print(
                    f"⚠️  Warning: oneOf not supported, using interface{{}} for '{prop_name}'"
                )
                field_type = "interface{}"
            else:
                field_type = schema_type_to_go_type(prop_schema, 1)

            field_name = util.Camelize(prop_name)
            json_tag = f'`json:"{prop_name}"`'
            fields.append(f"\t{field_name} {field_type} {json_tag}")

        fields_str = "\n".join(fields)
        return f"type {type_name} struct {{\n{fields_str}\n}}"
    else:
        print(f"⚠️  Warning: Unexpected type '{schema_type}' for object metric")
        return f"type {type_name} interface{{}}"


def clean_string(s: str) -> str:
    return s.replace("\n", " ").rstrip()


def output_go(
    objs: metrics.ObjectTree, output_dir: Path, options: Optional[Dict[str, Any]]
) -> None:
    """
    Given a tree of objects, output Go code to `output_dir`.

    The output is a single file containing all the code for assembling pings with
    metrics, serializing, and submitting.

    :param objects: A tree of objects (metrics and pings) as returned from
        `parser.parse_objects`.
    :param output_dir: Path to an output directory to write to.
    """

    template = util.get_jinja2_template(
        "go_server.jinja2",
        filters=(
            ("ping_type_name", generate_ping_type_name),
            ("ping_events_type_name", generate_ping_events_type_name),
            ("event_type_name", generate_event_type_name),
            ("event_extra_name", generate_extra_name),
            ("metric_name", generate_metric_name),
            ("metric_argument_name", generate_metric_argument_name),
            ("go_metric_type", generate_metric_type),
            ("clean_string", clean_string),
            ("object_type_name", generate_object_type_name),
            ("object_struct_definition", generate_object_struct_definition),
        ),
    )

    # unique list of event metrics used in any ping
    event_metrics: List[metrics.Metric] = []

    # unique list of object metrics used in any ping
    object_metrics: List[metrics.Metric] = []

    # Go through all metrics in objs and build a map of
    # ping->list of metric categories->list of metrics
    # for easier processing in the template.
    ping_to_metrics: Dict[str, Dict[str, List[metrics.Metric]]] = defaultdict(dict)
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

                    if metric.type == "object" and metric not in object_metrics:
                        object_metrics.append(metric)

                    metrics_by_type = ping_to_metrics[ping]
                    metrics_list = metrics_by_type.setdefault(metric.type, [])
                    metrics_list.append(metric)

    PING_METRIC_ERROR_MSG = (
        " Server-side environment is simplified and this"
        + " parser doesn't generate individual metric files. Make sure to pass all"
        + " your ping and metric definitions in a single invocation of the parser."
    )
    if not ping_to_metrics:
        print("❌ No pings with metrics found." + PING_METRIC_ERROR_MSG)
        return

    extension = ".go"
    filepath = output_dir / ("server_events" + extension)
    with filepath.open("w", encoding="utf-8") as fd:
        fd.write(
            template.render(
                parser_version=__version__,
                pings=ping_to_metrics,
                events=event_metrics,
                objects=object_metrics,
            )
        )
