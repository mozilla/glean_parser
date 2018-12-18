# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Outputter to generate Kotlin code for metrics.
"""

import enum
import io
import json

from . import util


def kotlin_datatypes_filter(value):
    """
    A Jinja2 filter that renders Kotlin literals.

    Based on Python's JSONEncoder, but overrides lists to use listOf, and dicts
    to use mapOf.
    """
    class KotlinEncoder(json.JSONEncoder):
        def iterencode(self, value):
            if isinstance(value, list):
                yield 'listOf('
                first = True
                for subvalue in value:
                    if not first:
                        yield ', '
                    yield from self.iterencode(subvalue)
                    first = False
                yield ')'
            elif isinstance(value, dict):
                yield 'mapOf('
                first = True
                for key, subvalue in value.items():
                    if not first:
                        yield ', '
                    yield from self.iterencode(key)
                    yield ' to '
                    yield from self.iterencode(subvalue)
                    first = False
                yield ')'
            elif isinstance(value, enum.Enum):
                yield (
                    f'{value.__class__.__name__}.'
                    f'{util.Camelize(value.name)}'
                )
            else:
                yield from super().iterencode(value)

    fd = io.StringIO()
    encoder = KotlinEncoder()
    for chunk in encoder.iterencode(value):
        fd.write(chunk)
    return fd.getvalue()


def output_kotlin(metrics, output_dir, options={}):
    """
    Given a tree of `metrics`, output Kotlin code to `output_dir`.

    :param metrics: A tree of metrics, as returns from `parser.parse_metrics`.
    :param output_dir: Path to an output directory to write to.
    :param options: options dictionary, with the following optional keys:

        - `namespace`: The package namespace to declare at the top of the
          generated files. Defaults to `GleanMetrics`.
    """
    template = util.get_jinja2_template(
        'kotlin.jinja2',
        filters=(('kotlin', kotlin_datatypes_filter),)
    )

    # The metric parameters to pass to constructors
    extra_args = [
        'name',
        'category',
        'send_in_pings',
        'lifetime',
        'disabled',
        'values',
        'denominator',
        'time_unit',
        'objects',
        'allowed_extra_keys'
    ]

    namespace = options.get('namespace', 'GleanMetrics')

    for category_key, category_val in metrics.items():
        filename = util.Camelize(category_key) + '.kt'
        filepath = output_dir / filename

        metric_types = sorted(list(set(
            metric.type for metric in category_val.values()
        )))

        with open(filepath, 'w', encoding='utf-8') as fd:
            fd.write(
                template.render(
                    category_name=category_key,
                    metrics=category_val,
                    metric_types=metric_types,
                    extra_args=extra_args,
                    namespace=namespace,
                )
            )
            # Jinja2 squashes the final newline, so we explicitly add it
            fd.write('\n')
