# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import functools
import json
import sys

import inflection
import jinja2
import yaml


TESTING_MODE = 'pytest' in sys.modules


def load_yaml_or_json(path):
    """
    Load the content from either a .json or .yaml file, based on the filename
    extension.

    Parameters
    ----------
    path : pathlib.Path object

    Returns
    -------
    obj : any
        The tree of objects as a result of parsing the file.

    Exceptions
    ----------
    ValueError: The file is neither a .json, .yml or .yaml file.
    """
    # If in py.test, support bits of literal JSON/YAML content
    if TESTING_MODE and isinstance(path, dict):
        return path

    if path.suffix == '.json':
        with open(path, 'r') as fd:
            return json.load(fd)
    elif path.suffix in ('.yml', '.yaml'):
        with open(path, 'r') as fd:
            return yaml.safe_load(fd)
    else:
        raise ValueError(f'Unknown file extension {path.suffix}')


def ensure_list(value):
    """
    Ensures that the value is a list. If it is anything but a list or tuple, a
    list with a single element containing only value is returned.
    """
    if not isinstance(value, (list, tuple)):
        return [value]
    return value


@functools.lru_cache()
def get_jinja2_template(template_name, filters=()):
    """
    Get a Jinja2 template that ships with glean_parser.

    The template has extra filters for camel-casing identifiers.

    Parameters
    ----------
    template_name : str
        Name of a file in `glean_parser/templates`.

    filters : tuple of 2-tuple
        A tuple of (name, func) pairs defining additional filters.
    """
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('glean_parser', 'templates')
    )

    def camelize(value):
        return inflection.camelize(value, False)

    def Camelize(value):
        return inflection.camelize(value, True)

    env.filters['camelize'] = camelize
    env.filters['Camelize'] = Camelize
    for filter_name, filter_func in filters:
        env.filters[filter_name] = filter_func

    return env.get_template(template_name)


def keep_value(f):
    """
    Wrap a generator so the value it returns (rather than yields), will be
    accessible on the .value attribute when the generator is exhausted.
    """
    class ValueKeepingGenerator(object):
        def __init__(self, g):
            self.g = g
            self.value = None

        def __iter__(self):
            self.value = yield from self.g

    @functools.wraps(f)
    def g(*args, **kwargs):
        return ValueKeepingGenerator(f(*args, **kwargs))

    return g
