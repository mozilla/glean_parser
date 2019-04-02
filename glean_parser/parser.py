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
from . import util


ROOT_DIR = Path(__file__).parent
SCHEMAS_DIR = ROOT_DIR / 'schemas'


_unset = _utils.Unset()


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


@functools.lru_cache(maxsize=1)
def _get_metrics_schema():
    schema = util.load_yaml_or_json(SCHEMAS_DIR / 'metrics.1-0-0.schema.yaml')
    resolver = util.get_null_resolver(schema)

    validator_class = jsonschema.validators.validator_for(schema)
    _update_validator(validator_class)
    validator_class.check_schema(schema)
    validator = validator_class(schema, resolver=resolver)
    return schema, validator


def get_parameter_doc(key):
    """
    Returns documentation about a specific metric parameter.
    """
    schema, _ = _get_metrics_schema()
    return schema['definitions']['metric']['properties'][key]['description']


def validate(content, filepath='<input>'):
    """
    Validate the given content against the metrics.schema.yaml schema.
    """
    schema, validator = _get_metrics_schema()

    if '$schema' in content and content.get('$schema') != schema.get('$id'):
        yield _format_error(
            filepath,
            '',
            f"$schema key must be set to {schema.get('$id')}'"
        )

    yield from (
        _format_error(filepath, '', _pprint_validation_error(e))
        for e in validator.iter_errors(content)
    )


def _load_metrics_file(filepath):
    """
    Load a metrics.yaml format file.
    """
    try:
        metrics_content = util.load_yaml_or_json(filepath)
    except Exception as e:
        yield _format_error(filepath, '', textwrap.fill(str(e)))
        return {}

    if metrics_content is None:
        yield _format_error(filepath, '', 'metrics file can not be empty.')
        return {}

    has_error = False
    for error in validate(metrics_content, filepath):
        has_error = True
        yield error

    if has_error:
        return {}
    else:
        return metrics_content


def _merge_and_instantiate_metrics(filepaths, config):
    """
    Load a list of metrics.yaml files, convert the JSON information into Metric
    objects, and merge them into a single tree.
    """
    output_metrics = {}
    # Keep track of where each metric came from to provide a better error
    # message
    sources = {}

    for filepath in filepaths:
        metrics_content = yield from _load_metrics_file(filepath)
        for category_key, category_val in metrics_content.items():
            if category_key.startswith('$'):
                continue
            if (not config.get('allow_reserved') and
                    category_key.split('.')[0] == 'glean'):
                yield _format_error(
                    filepath,
                    f"For category '{category_key}'",
                    f"Categories beginning with 'glean' are reserved for "
                    f"glean internal use."
                )
                continue
            output_metrics.setdefault(category_key, {})
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
                    output_metrics[category_key][metric_key] = metric_obj
                    sources[(category_key, metric_key)] = filepath

    return output_metrics


@util.keep_value
def parse_metrics(filepaths, config={}):
    """
    Parse one or more metrics.yaml files, returning a tree of `metrics.Metric`
    instances.

    The result is a generator over any errors.  If there are no errors, the
    actual metrics can be obtained from `result.value`.  For example::

      result = metrics.parse_metrics(filepaths)
      for err in result:
          print(err)
      all_metrics = result.value

    The result value is a dictionary of category names to categories, where
    each category is a dictionary from metric name to `metrics.Metric`
    instances.

    :param filepaths: list of Path objects to metrics.yaml files
    :param config: A dictionary of options that change parsing behavior.
        Supported keys are:
        - `allow_reserved`: Allow values reserved for internal Glean use.
    """
    filepaths = util.ensure_list(filepaths)
    all_metrics = yield from _merge_and_instantiate_metrics(filepaths, config)
    return all_metrics
