# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Outputter to generate Kotlin code for metrics.
"""

import inflection

from . import util


def output_kotlin(metrics, output_dir):
    """
    Given a tree of `metrics`, output Kotlin code to `output_dir`.
    """

    template = util.get_jinja2_template('kotlin.jinja2.kt')

    # The metric parameters to pass to constructors
    extra_args = [
        ('user_property', False),
        ('application_property', False),
        ('disabled', False),
        ('max_length', 256),
        ('max_entries', 256),
        ('denominator', 256),
        ('time_unit', 'millisecond')
    ]

    for group_key, group_val in metrics.items():
        filename = inflection.camelize(group_key, True) + '.kt'
        filepath = output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as fd:
            fd.write(
                template.render(
                    group_name=group_key,
                    metrics=group_val,
                    extra_args=extra_args,
                )
            )
