# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Outputter to generate Kotlin code for metrics.
"""

import enum
import json

from . import metrics
from . import util


def kotlin_datatypes_filter(value):
    """
    A Jinja2 filter that renders Kotlin literals.

    Based on Python's JSONEncoder, but overrides:
      - lists to use listOf
      - dicts to use mapOf
      - sets to use setOf
      - enums to use the like-named Kotlin enum
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
            elif isinstance(value, set):
                yield 'setOf('
                first = True
                for subvalue in sorted(list(value)):
                    if not first:
                        yield ', '
                    yield from self.iterencode(subvalue)
                    first = False
                yield ')'
            else:
                yield from super().iterencode(value)

    return ''.join(KotlinEncoder().iterencode(value))


def type_name(obj):
    """
    Returns the Kotlin type to use for a given metric or ping object.
    """
    if isinstance(obj, metrics.Event):
        if len(obj.extra_keys):
            enumeration = f'{util.camelize(obj.name)}Keys'
        else:
            enumeration = 'NoExtraKeys'
        return f'EventMetricType<{enumeration}>'
    return class_name(obj.type)


def class_name(obj_type):
    """
    Returns the Kotlin class name for a given metric or ping type.
    """
    if obj_type == 'ping':
        return 'PingType'
    if obj_type.startswith('labeled_'):
        obj_type = obj_type[8:]
    return f'{util.Camelize(obj_type)}MetricType'


def output_kotlin(objs, output_dir, options={}):
    """
    Given a tree of objects, output Kotlin code to `output_dir`.

    :param objects: A tree of objects (metrics and pings) as returned from
    `parser.parse_objects`.
    :param output_dir: Path to an output directory to write to.
    :param options: options dictionary, with the following optional keys:

        - `namespace`: The package namespace to declare at the top of the
          generated files. Defaults to `GleanMetrics`.
        - `glean_namespace`: The package namespace of the glean library itself.
          This is where glean objects will be imported from in the generated
          code.
    """
    template = util.get_jinja2_template(
        'kotlin.jinja2',
        filters=(
            ('kotlin', kotlin_datatypes_filter),
            ('type_name', type_name),
            ('class_name', class_name)
        )
    )

    # The object parameters to pass to constructors
    extra_args = [
        'name',
        'category',
        'send_in_pings',
        'lifetime',
        'values',
        'denominator',
        'time_unit',
        'allowed_extra_keys',
        'disabled',
        'include_client_id'
    ]

    namespace = options.get('namespace', 'GleanMetrics')
    glean_namespace = options.get(
        'glean_namespace',
        'mozilla.components.service.glean'
    )

    for category_key, category_val in objs.items():
        filename = util.Camelize(category_key) + '.kt'
        filepath = output_dir / filename

        obj_types = sorted(list(set(
            class_name(obj.type) for obj in category_val.values()
        )))
        has_labeled_metrics = any(
            getattr(metric, 'labeled', False)
            for metric in category_val.values()
        )

        with open(filepath, 'w', encoding='utf-8') as fd:
            fd.write(
                template.render(
                    category_name=category_key,
                    objs=category_val,
                    obj_types=obj_types,
                    extra_args=extra_args,
                    namespace=namespace,
                    has_labeled_metrics=has_labeled_metrics,
                    glean_namespace=glean_namespace,
                )
            )
            # Jinja2 squashes the final newline, so we explicitly add it
            fd.write('\n')
