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
        raise ValueError(
            f"In file '{filepath}', {str(e)}"
        )

    if metrics_content.get('$schema') != schema.get('$id'):
        raise ValueError(
            f"In file '{filepath}', $schema key must be set to "
            f"'{schema.get('$id')}'"
        )

    jsonschema.validate(metrics_content, schema)

    return metrics_content


def _merge_metrics(filepaths):
    """
    Load a list of metrics.yaml files and merge them into a single tree.
    """
    output_metrics = {}
    # Keep track of where each metric came from to provide a better error
    # message
    sources = {}

    for filepath in filepaths:
        metrics_content = _load_metrics_file(filepath)
        for group_key, group_val in metrics_content.items():
            if group_key.startswith('$'):
                continue
            output_metrics.setdefault(group_key, {})
            for metric_key, metric_val in group_val.items():
                already_seen = sources.get((group_key, metric_key))
                if already_seen is not None:
                    # We've seen this metric name already
                    raise ValueError(
                        f"Duplicate metric name '{group_key}.{metric_key}' "
                        f"in '{filepath}', already defined in '{already_seen}'"
                    )
                output_metrics[group_key][metric_key] = metric_val
                sources[(group_key, metric_key)] = filepath

    return output_metrics


def _instantiate_metrics(all_metrics):
    """
    Instantiate each of the metrics info sections of the metrics.yaml file into
    Metric objects (see metrics.py).
    """
    output_metrics = {}
    for group_key, group_val in all_metrics.items():
        output_metrics[group_key] = {}
        for metric_key, metric_val in group_val.items():
            output_metrics[group_key][metric_key] = Metric.make_metric(
                group_key, metric_key, metric_val
            )
    return output_metrics


def parse_metrics(filepaths):
    """
    Parse one or more metrics.yaml files, returning a tree of `metrics.Metric`
    instances.

    The result is a dictionary of group names to groups, where each group is a
    dictionary from metric name to `metrics.Metric` instances.

    """
    filepaths = util.ensure_list(filepaths)
    all_metrics = _merge_metrics(filepaths)
    return _instantiate_metrics(all_metrics)
