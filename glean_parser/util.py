# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import functools
import json
from pathlib import Path
import sys
import textwrap
import urllib.request

import appdirs
import diskcache
import inflection
import jinja2
import jsonschema
from jsonschema import _utils
import yaml


TESTING_MODE = 'pytest' in sys.modules


# Adapted from
# https://stackoverflow.com/questions/34667108/ignore-dates-and-times-while-parsing-yaml
class _NoDatesSafeLoader(yaml.SafeLoader):
    @classmethod
    def remove_implicit_resolver(cls, tag_to_remove):
        """
        Remove implicit resolvers for a particular tag

        Takes care not to modify resolvers in super classes.

        We want to load datetimes as strings, not dates, because we
        go on to serialise as json which doesn't have the advanced types
        of yaml, and leads to incompatibilities down the track.
        """
        if 'yaml_implicit_resolvers' not in cls.__dict__:
            cls.yaml_implicit_resolvers = cls.yaml_implicit_resolvers.copy()

        for first_letter, mappings in cls.yaml_implicit_resolvers.items():
            cls.yaml_implicit_resolvers[first_letter] = [
                (tag, regexp)
                for tag, regexp in mappings
                if tag != tag_to_remove
            ]


# Since we use JSON schema to validate, and JSON schema doesn't support
# datetimes, we don't want the YAML loader to give us datetimes -- just
# strings.
_NoDatesSafeLoader.remove_implicit_resolver('tag:yaml.org,2002:timestamp')


def load_yaml_or_json(path):
    """
    Load the content from either a .json or .yaml file, based on the filename
    extension.

    :param path: `pathlib.Path` object
    :rtype object: The tree of objects as a result of parsing the file.
    :raises ValueError: The file is neither a .json, .yml or .yaml file.
    """
    # If in py.test, support bits of literal JSON/YAML content
    if TESTING_MODE and isinstance(path, dict):
        return path

    if not path.is_file():
        return {}

    if path.suffix == '.json':
        with open(path, 'r') as fd:
            return json.load(fd)
    elif path.suffix in ('.yml', '.yaml'):
        with open(path, 'r') as fd:
            return yaml.load(fd, Loader=_NoDatesSafeLoader)
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


def camelize(value):
    """
    Convert the value to camelCase (with a lower case first letter).

    This is a thin wrapper around inflection.camelize that handles dots in
    addition to underscores.
    """
    return inflection.camelize(value.replace('.', '_'), False)


def Camelize(value):
    """
    Convert the value to CamelCase (with an upper case first letter).

    This is a thin wrapper around inflection.camelize that handles dots in
    addition to underscores.
    """
    return inflection.camelize(value.replace('.', '_'), True)


@functools.lru_cache()
def get_jinja2_template(template_name, filters=()):
    """
    Get a Jinja2 template that ships with glean_parser.

    The template has extra filters for camel-casing identifiers.

    :param template_name: Name of a file in ``glean_parser/templates``
    :param filters: tuple of 2-tuple. A tuple of (name, func) pairs defining
        additional filters.
    """
    env = jinja2.Environment(
        loader=jinja2.PackageLoader('glean_parser', 'templates'),
        trim_blocks=True,
        lstrip_blocks=True,
    )

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


def get_null_resolver(schema):
    """
    Returns a JSON Pointer resolver that does nothing.

    This lets us handle the moz: URLs in our schemas.
    """
    class NullResolver(jsonschema.RefResolver):
        def resolve_remote(self, uri):
            if uri in self.store:
                return self.store[uri]
            if uri == '':
                return self.referrer

    return NullResolver.from_schema(schema)


def fetch_remote_url(url, cache=True):
    """
    Fetches the contents from an HTTP url or local file path, and optionally
    caches it to disk.
    """
    is_http = url.startswith('http')

    if not is_http:
        with open(url, 'r', encoding='utf-8') as fd:
            contents = fd.read()
        return contents

    if cache:
        cache_dir = appdirs.user_cache_dir('glean_parser', 'mozilla')
        with diskcache.Cache(cache_dir) as dc:
            if url in dc:
                return dc[url]

    contents = urllib.request.urlopen(url).read()

    if cache:
        with diskcache.Cache(cache_dir) as dc:
            dc[url] = contents

    return contents


_unset = _utils.Unset()


def pprint_validation_error(error):
    """
    A version of jsonschema's ValidationError __str__ method that doesn't
    include the schema fragment that failed.  This makes the error messages
    much more succinct.

    It also shows any subschemas of anyOf/allOf that failed, if any (what
    jsonschema calls "context").
    """
    essential_for_verbose = (
        error.validator, error.validator_value, error.instance, error.schema,
    )
    if any(m is _unset for m in essential_for_verbose):
        return textwrap.fill(error.message)

    instance = error.instance
    for path in list(error.relative_path)[::-1]:
        if isinstance(path, str):
            instance = {path: instance}
        else:
            instance = [instance]

    yaml_instance = yaml.dump(instance, width=72, default_flow_style=False)

    parts = [
        '```',
        yaml_instance.rstrip(),
        '```',
        '',
        textwrap.fill(error.message)
    ]
    if error.context:
        parts.extend(
            textwrap.fill(
                x.message,
                initial_indent='    ',
                subsequent_indent='    '
            )
            for x in error.context
        )

    description = error.schema.get('description')
    if description:
        parts.extend([
            "",
            "Documentation for this node:",
            _utils.indent(description)
        ])

    return '\n'.join(parts)


def format_error(filepath, header, content):
    """
    Format a jsonshema validation error.
    """
    if isinstance(filepath, Path):
        filepath = filepath.resolve()
    else:
        filepath = '<string>'
    if header:
        return f'{filepath}: {header}:\n{_utils.indent(content)}'
    else:
        return f'{filepath}:\n{_utils.indent(content)}'


def is_expired(expires):
    """
    Parses the `expires` field in a metric or ping and returns whether
    the object should be considered expired.
    """
    if expires == 'never':
        return False
    elif expires == 'expired':
        return True
    else:
        try:
            date = datetime.date.fromisoformat(expires)
        except ValueError:
            raise ValueError(
                f"Invalid expiration date '{expires}'. "
                "Must be of the form yyyy-mm-dd in UTC."
            )
        return date <= datetime.datetime.utcnow().date()


def validate_expires(expires):
    """
    Raises ValueError if `expires` is not valid.
    """
    if expires in ('never', 'expired'):
        return
    datetime.date.fromisoformat(expires)
