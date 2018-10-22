# -*- coding: utf-8 -*-

"""
Code for parsing metrics.yaml files.
"""

import functools
from pathlib import Path

import jsonschema

from .metrics import Metric
from . import util


ROOT_DIR = Path(__file__).parent
SCHEMAS_DIR = ROOT_DIR / 'schemas'


@functools.lru_cache(maxsize=1)
def _get_metrics_schema():
    return util.load_yaml_or_json(SCHEMAS_DIR / 'metrics.schema.yaml')


def _load_metrics_file(filepath):
    """
    Load a metrics.yaml format file.
    """
    schema = _get_metrics_schema()

    try:
        metrics_content = util.load_yaml_or_json(filepath)
    except Exception as e:
        yield f"{filepath}: {str(e)}"
        return {}

    if metrics_content.get('$schema') != schema.get('$id'):
        yield f"{filepath}: $schema key must be set to {schema.get('$id')}'"

    validator_class = jsonschema.validators.validator_for(schema)
    validator = validator_class(schema)
    yield from (
        f"{filepath}: {e}"
        for e in validator.iter_errors(metrics_content)
    )

    return metrics_content


def _merge_and_instantiate_metrics(filepaths):
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
            output_metrics.setdefault(category_key, {})
            for metric_key, metric_val in category_val.items():
                try:
                    metric_obj = Metric.make_metric(
                        category_key, metric_key, metric_val, validated=True
                    )
                except Exception as e:
                    yield f"{filepath}: {category_key}.{metric_key}: {e}"
                    metric_obj = None

                already_seen = sources.get((category_key, metric_key))
                if already_seen is not None:
                    # We've seen this metric name already
                    yield (
                        f"{filepath}: Duplicate metric name "
                        f"'{category_key}.{metric_key}' already defined in "
                        f"'{already_seen}'"
                    )
                else:
                    output_metrics[category_key][metric_key] = metric_obj
                    sources[(category_key, metric_key)] = filepath

    return output_metrics


@util.keep_value
def parse_metrics(filepaths):
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
    """
    filepaths = util.ensure_list(filepaths)
    all_metrics = yield from _merge_and_instantiate_metrics(filepaths)
    return all_metrics
