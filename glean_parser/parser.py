# -*- coding: utf-8 -*-

"""
Code for parsing metrics.yaml files.
"""

import functools
from pathlib import Path
import textwrap

import jsonschema
from jsonschema import _utils
from jsonschema.exceptions import ValidationError
import yaml

from .metrics import Metric
from .pings import Ping, RESERVED_PING_NAMES
from . import util


ROOT_DIR = Path(__file__).parent
SCHEMAS_DIR = ROOT_DIR / 'schemas'


_unset = _utils.Unset()


METRICS_ID = 'moz://mozilla.org/schemas/glean/metrics/1-0-0'
PINGS_ID = 'moz://mozilla.org/schemas/glean/pings/1-0-0'


FILE_TYPES = {
    METRICS_ID: 'metrics',
    PINGS_ID: 'pings'
}


def _pprint_validation_error(error):
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


def _format_error(filepath, header, content):
    if isinstance(filepath, Path):
        filepath = filepath.resolve()
    else:
        filepath = '<string>'
    if header:
        return f'{filepath}: {header}:\n{_utils.indent(content)}'
    else:
        return f'{filepath}:\n{_utils.indent(content)}'


def _update_validator(validator):
    """
    Adds some custom validators to the jsonschema validator that produce
    nicer error messages.
    """
    def required(validator, required, instance, schema):
        if not validator.is_type(instance, "object"):
            return
        missing_properties = set(
            property for property in required if property not in instance
        )
        if len(missing_properties):
            missing_properties = sorted(list(missing_properties))
            yield ValidationError(
                f"Missing required properties: {', '.join(missing_properties)}"
            )
    validator.VALIDATORS['required'] = required


def _load_file(filepath):
    """
    Load a metrics.yaml or pings.yaml format file.
    """
    try:
        content = util.load_yaml_or_json(filepath)
    except Exception as e:
        yield _format_error(filepath, '', textwrap.fill(str(e)))
        return {}, None

    if content is None:
        yield _format_error(
            filepath,
            '',
            f"'{filepath}' file can not be empty.",
        )
        return {}, None

    if content == {}:
        return {}, None

    filetype = FILE_TYPES.get(content.get('$schema'))

    for error in validate(content, filepath):
        content = {}
        yield error

    return content, filetype


@functools.lru_cache(maxsize=1)
def _load_schemas():
    """
    Load all of the known schemas from disk, and put them in a map based on the
    schema's $id.
    """
    schemas = {}
    for schema_path in SCHEMAS_DIR.glob('*.yaml'):
        schema = util.load_yaml_or_json(schema_path)
        resolver = util.get_null_resolver(schema)
        validator_class = jsonschema.validators.validator_for(schema)
        _update_validator(validator_class)
        validator_class.check_schema(schema)
        validator = validator_class(schema, resolver=resolver)
        schemas[schema['$id']] = (schema, validator)
    return schemas


def _get_schema(schema_id, filepath="<input>"):
    """
    Get the schema for the given schema $id.
    """
    schemas = _load_schemas()
    if schema_id not in schemas:
        raise ValueError(
            _format_error(
                filepath,
                '',
                f"$schema key must be one of {', '.join(schemas.keys())}"
            )
        )
    return schemas[schema_id]


def _get_schema_for_content(content, filepath):
    """
    Get the appropriate schema for the given JSON content.
    """
    return _get_schema(content.get('$schema'), filepath)


def get_parameter_doc(key):
    """
    Returns documentation about a specific metric parameter.
    """
    schema, _ = _get_schema(METRICS_ID)
    return schema['definitions']['metric']['properties'][key]['description']


def validate(content, filepath='<input>'):
    """
    Validate the given content against the appropriate schema.
    """
    try:
        schema, validator = _get_schema_for_content(content, filepath)
    except ValueError as e:
        yield str(e)
    else:
        yield from (
            _format_error(filepath, '', _pprint_validation_error(e))
            for e in validator.iter_errors(content)
        )


def _instantiate_metrics(all_objects, sources, content, filepath, config):
    """
    Load a list of metrics.yaml files, convert the JSON information into Metric
    objects, and merge them into a single tree.
    """
    for category_key, category_val in content.items():
        if category_key.startswith('$'):
            continue
        if (not config.get('allow_reserved') and
                category_key.split('.')[0] == 'glean'):
            yield _format_error(
                filepath,
                f"For category '{category_key}'",
                f"Categories beginning with 'glean' are reserved for "
                f"Glean internal use."
            )
            continue
        all_objects.setdefault(category_key, {})
        for metric_key, metric_val in category_val.items():
            try:
                metric_obj = Metric.make_metric(
                    category_key, metric_key, metric_val,
                    validated=True, config=config
                )
            except Exception as e:
                yield _format_error(
                    filepath,
                    f'On instance {category_key}.{metric_key}',
                    str(e)
                )
                metric_obj = None

            already_seen = sources.get((category_key, metric_key))
            if already_seen is not None:
                # We've seen this metric name already
                yield _format_error(
                    filepath,
                    "",
                    f"Duplicate metric name '{category_key}.{metric_key}'"
                    f"already defined in '{already_seen}'"
                )
            else:
                all_objects[category_key][metric_key] = metric_obj
                sources[(category_key, metric_key)] = filepath


def _instantiate_pings(all_objects, sources, content, filepath, config):
    """
    Load a list of pings.yaml files, convert the JSON information into Ping
    objects.
    """
    for ping_key, ping_val in content.items():
        if ping_key.startswith('$'):
            continue
        if not config.get('allow_reserved'):
            if ping_key in RESERVED_PING_NAMES:
                yield _format_error(
                    filepath,
                    f"For ping '{ping_key}'",
                    f"Ping uses a reserved name ({RESERVED_PING_NAMES})"
                )
                continue
        ping_val['name'] = ping_key
        try:
            ping_obj = Ping(**ping_val)
        except Exception as e:
            yield _format_error(
                filepath,
                f'On instance {ping_key}',
                str(e)
            )
            ping_obj = None

        already_seen = sources.get(ping_key)
        if already_seen is not None:
            # We've seen this ping name already
            yield _format_error(
                filepath,
                "",
                f"Duplicate ping name '{ping_key}'"
                f"already defined in '{already_seen}'"
            )
        else:
            all_objects.setdefault('pings', {})[ping_key] = ping_obj
            sources[ping_key] = filepath


@util.keep_value
def parse_objects(filepaths, config={}):
    """
    Parse one or more metrics.yaml and/or pings.yaml files, returning a tree of
    `metrics.Metric` and `pings.Ping` instances.

    The result is a generator over any errors.  If there are no errors, the
    actual metrics can be obtained from `result.value`.  For example::

      result = metrics.parse_metrics(filepaths)
      for err in result:
          print(err)
      all_metrics = result.value

    The result value is a dictionary of category names to categories, where
    each category is a dictionary from metric name to `metrics.Metric`
    instances.  There is also the special category `pings` containing all
    of the `pings.Ping` instances.

    :param filepaths: list of Path objects to metrics.yaml and/or pings.yaml
    files
    :param config: A dictionary of options that change parsing behavior.
        Supported keys are:
        - `allow_reserved`: Allow values reserved for internal Glean use.
    """
    all_objects = {}
    sources = {}
    filepaths = util.ensure_list(filepaths)
    for filepath in filepaths:
        content, filetype = yield from _load_file(filepath)
        if filetype == 'metrics':
            yield from _instantiate_metrics(
                all_objects,
                sources,
                content,
                filepath,
                config
            )
        elif filetype == 'pings':
            yield from _instantiate_pings(
                all_objects,
                sources,
                content,
                filepath,
                config
            )
    return all_objects
