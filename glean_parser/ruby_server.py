# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Outputter to generate Ruby code for collecting events using the
"Event Stream" pattern.

This outputter is different from the rest of the outputters in that the code it
generates does not use the Glean SDK. It is meant to be used to collect events
using the "Event Stream" pattern in server-side environments. In these environments
SDK assumptions to measurement window and connectivity don't hold.
Generated code takes care of assembling pings as events, serializing to messages
conforming to Glean schema, and logging with a custom logger. 
Then it's the role of the ingestion
pipeline to pick the messages up and process.

Warning: this outputter only support the event metric type and does not support
the pings.yaml file. See SUPPORTED_METRIC_TYPES
"""
from pathlib import Path
from typing import Any, Dict, Optional

from . import __version__, metrics, util

# As of now we should only support the event metric type
SUPPORTED_METRIC_TYPES = ["event"]


def event_class_name(pingName: str) -> str:
    return util.Camelize(pingName) + "ServerEvent"


def output(
    lang: str,
    objs: metrics.ObjectTree,
    output_dir: Path,
) -> None:
    """
    Given a tree of objects, output Ruby code to `output_dir`.

    The output is a single file containing all the code for assembling pings as events.
    Currently this is written to support only Glean "Event Stream" pattern..

    :param lang: ruby;
    :param objects: A tree of objects (event metrics) as returned from
        `parser.parse_objects`.
    :param output_dir: Path to an output directory to write to.
    """

    template = util.get_jinja2_template(
        "ruby_server.jinja2",
        filters=(("event_class_name", event_class_name),),
    )

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
    filepath = output_dir / ("server_events.rb")
    with filepath.open("w", encoding="utf-8") as fd:
        fd.write(
            template.render(
                parser_version=__version__,
                events=objs,
                lang=lang,
            )
        )


def output_ruby(
    objs: metrics.ObjectTree, output_dir: Path, options: Optional[Dict[str, Any]] = None
) -> None:
    """
    Given a tree of objects, output Ruby code to `output_dir`.

    :param objects: A tree of objects (event metrics) as returned from
        `parser.parse_objects`.
    :param output_dir: Path to an output directory to write to.
    """
    output("ruby", objs, output_dir)
