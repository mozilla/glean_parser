# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Outputter to generate Kotlin code for metrics.
"""

import io
import json

import inflection

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
            else:
                yield from super().iterencode(value)

    fd = io.StringIO()
    encoder = KotlinEncoder()
    for chunk in encoder.iterencode(value):
        fd.write(chunk)
    return fd.getvalue()


def output_kotlin(metrics, output_dir):
    """
    Given a tree of `metrics`, output Kotlin code to `output_dir`.
    """

    template = util.get_jinja2_template(
        'kotlin.jinja2.kt',
        filters=(('kotlin', kotlin_datatypes_filter),)
    )

    # The metric parameters to pass to constructors
    extra_args = [
        'name',
        'category',
        'send_in_pings',
        'user_property',
        'application_property',
        'disabled',
        'values',
        'denominator',
        'time_unit',
        'objects',
        'allowed_extra_keys'
    ]

    for category_key, category_val in metrics.items():
        filename = inflection.camelize(category_key, True) + '.kt'
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
                )
            )
