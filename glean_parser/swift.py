# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Outputter to generate Swift code for metrics.
"""

import enum
import json

from . import metrics
from . import pings
from . import util
from collections import defaultdict


def swift_datatypes_filter(value):
    """
    A Jinja2 filter that renders Swift literals.

    Based on Python's JSONEncoder, but overrides:
      - dicts to use `[key: value]`
      - sets to use `[...]`
      - enums to use the like-named Swift enum
    """

    class SwiftEncoder(json.JSONEncoder):
        def iterencode(self, value):
            if isinstance(value, dict):
                yield "["
                first = True
                for key, subvalue in value.items():
                    if not first:
                        yield ", "
                    yield from self.iterencode(key)
                    yield ": "
                    yield from self.iterencode(subvalue)
                    first = False
                yield "]"
            elif isinstance(value, enum.Enum):
                yield (f".{util.camelize(value.name)}")
            elif isinstance(value, set):
                yield "["
                first = True
                for subvalue in sorted(list(value)):
                    if not first:
                        yield ", "
                    yield from self.iterencode(subvalue)
                    first = False
                yield "]"
            else:
                yield from super().iterencode(value)

    return "".join(SwiftEncoder().iterencode(value))


def type_name(obj):
    """
    Returns the Swift type to use for a given metric or ping object.
    """
    # TODO: Events are not yet supported
    # if isinstance(obj, metrics.Event):
    #     if len(obj.extra_keys):
    #         enumeration = f"{util.camelize(obj.name)}Keys"
    #     else:
    #         enumeration = "noExtraKeys"
    #     return f"EventMetricType<{enumeration}>"
    return class_name(obj.type)


def class_name(obj_type):
    """
    Returns the Swift class name for a given metric or ping type.
    """
    if obj_type == "ping":
        return "Ping"
    if obj_type.startswith("labeled_"):
        obj_type = obj_type[8:]
    return f"{util.Camelize(obj_type)}MetricType"


def output_swift(objs, output_dir, options={}):
    """
    Given a tree of objects, output Swift code to `output_dir`.

    :param objects: A tree of objects (metrics and pings) as returned from
    `parser.parse_objects`.
    :param output_dir: Path to an output directory to write to.
    :param options: options dictionary, with the following optional keys:
    """
    template = util.get_jinja2_template(
        "swift.jinja2",
        filters=(
            ("swift", swift_datatypes_filter),
            ("type_name", type_name),
            ("class_name", class_name),
        ),
    )

    # The object parameters to pass to constructors.
    # Need to be in the order the type constructor expects them.
    extra_args = [
        "category",
        "name",
        "send_in_pings",
        "lifetime",
        "disabled",
        "time_unit",
    ]

    for category_key, category_val in objs.items():
        filename = util.Camelize(category_key) + ".swift"
        filepath = output_dir / filename

        custom_pings = defaultdict()
        for obj in category_val.values():
            if isinstance(obj, pings.Ping):
                custom_pings[obj.name] = obj
            elif isinstance(obj, metrics.Event):
                print(f"WARN: Events are not yet supported: {category_key}.{obj.name}")

            if getattr(obj, "labeled", False):
                print(
                    "WARN: Labeled metrics are not yet supported: {0}.{1}".format(
                        category_key, obj.name
                    )
                )

        has_labeled_metrics = any(
            getattr(metric, "labeled", False) for metric in category_val.values()
        )

        with open(filepath, "w", encoding="utf-8") as fd:
            fd.write(
                template.render(
                    category_name=category_key,
                    objs=category_val,
                    extra_args=extra_args,
                    has_labeled_metrics=has_labeled_metrics,
                    is_ping_type=len(custom_pings) > 0,
                )
            )
            # Jinja2 squashes the final newline, so we explicitly add it
            fd.write("\n")
