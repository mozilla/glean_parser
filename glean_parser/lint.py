# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import sys


from . import parser
from . import util


def check_category_in_name(metric):
    """
    The same word appears in both the category and the name.
    """
    category_words = metric.category.split("_")
    name_words = metric.name.split("_")

    for word in category_words:
        if word in name_words:
            yield f"'{word}' appears in both category and name."


def check_unit_in_name(metric):
    """
    The metric name ends in a unit.
    """
    TIME_UNIT_ABBREV = {
        "nanosecond": "ns",
        "microsecond": "us",
        "millisecond": "ms",
        "second": "s",
        "minute": "m",
        "hour": "h",
        "day": "d",
    }

    MEMORY_UNIT_ABBREV = {
        "byte": "b",
        "kilobyte": "kb",
        "megabyte": "mb",
        "gigabyte": "gb",
    }

    name_words = metric.name.split("_")
    unit_in_name = name_words[-1]

    if hasattr(metric, "time_unit"):
        if (
            unit_in_name == TIME_UNIT_ABBREV.get(metric.time_unit.name)
            or unit_in_name == metric.time_unit.name
        ):
            yield (
                f"Suffix '{unit_in_name}' is redundant with time_unit. "
                "Only include time_unit."
            )
        elif (
            unit_in_name in TIME_UNIT_ABBREV.keys()
            or unit_in_name in TIME_UNIT_ABBREV.values()
        ):
            yield (
                f"Suffix '{unit_in_name}' doesn't match time_unit. "
                "Only include time_unit."
            )

    elif hasattr(metric, "memory_unit"):
        if (
            unit_in_name == MEMORY_UNIT_ABBREV.get(metric.memory_unit.name)
            or unit_in_name == metric.memory_unit.name
        ):
            yield (
                f"Suffix '{unit_in_name}' is redundant with memory_unit. "
                "Only include memory_unit."
            )
        elif (
            unit_in_name in MEMORY_UNIT_ABBREV.keys()
            or unit_in_name in MEMORY_UNIT_ABBREV.values()
        ):
            yield (
                f"Suffix '{unit_in_name}' doesn't match memory_unit. "
                "Only include memory_unit."
            )

    elif hasattr(metric, "unit"):
        if unit_in_name == metric.unit:
            yield (
                f"Suffix '{unit_in_name}' is redundant with unit param."
                "Only include unit."
            )


def check_type_in_name(metric):
    """
    The metric name contains a word relating to its type.
    """
    SYNONYMS = {
        "timing_distribution": [
            "time",
            "timing",
            "histogram",
            "distribution",
            "hist",
            "dist",
        ],
        "timespan": ["time", "duration"],
        "datetime": ["time", "date"],
        "boolean": ["bool"],
        "string": ["str"],
        "string_list": ["string", "str"],
        "counter": ["count"],
        "uuid": ["id"],
        "memory_distribution": [
            "memory",
            "mem",
            "histogram",
            "distribution",
            "hist",
            "dist",
        ],
        "custom_distribution": ["histogram", "distribution", "hist", "dist"],
    }

    name_words = metric.name.split("_")
    disallowed_words = [metric.type] + SYNONYMS.get(metric.type, [])
    if metric.type.startswith("labeled_"):
        prefix_length = len("labeled_")
        base_type = metric.type[prefix_length:]
        disallowed_words += [base_type] + SYNONYMS.get(base_type, [])

    for word in name_words:
        if word in disallowed_words:
            yield (
                f"Name contains word '{word}' which is too "
                f"similar to its type '{metric.type}'"
            )


def check_geckoview_in_name(metric):
    """
    The metric includes 'gv' when it's a GeckoView metric.
    """
    name_words = metric.name.split("_")
    if getattr(metric, "gecko_datapoint", False) and "gv" in name_words:
        yield f"Name contains 'gv' which is redundant with gecko_datapoint param."


_seen_categories = set()


def check_category_generic(metric):
    """
    The category name is too generic.
    """
    GENERIC_CATEGORIES = ["metrics", "events"]

    if (
        metric.category not in _seen_categories
        and metric.category in GENERIC_CATEGORIES
    ):
        _seen_categories.add(metric.category)
        yield f"Category '{metric.category}' is too generic."


CHECKS = {
    "CATEGORY_IN_NAME": check_category_in_name,
    "UNIT_IN_NAME": check_unit_in_name,
    "TYPE_IN_NAME": check_type_in_name,
    "GV_IN_NAME": check_geckoview_in_name,
    "CATEGORY_GENERIC": check_category_generic,
}


def lint_metrics(objs):
    violations = []
    for (category_name, metrics) in sorted(list(objs.items())):
        for (metric_name, metric) in sorted(list(metrics.items())):
            for check_name, check_func in CHECKS.items():
                if check_name in metric.no_lint:
                    continue
                violations.extend(
                    (check_name, metric, msg) for msg in check_func(metric)
                )

    if len(violations):
        print("Sorry, Glean found some glinter nits:", file=sys.stderr)
        for check_name, metric, msg in violations:
            print(
                f"{check_name}: {metric.category}.{metric.name}: {msg}", file=sys.stderr
            )
        print("", file=sys.stderr)
        print("Please fix the above nits to continue.", file=sys.stderr)
        print(
            "To disable a check, add a `no_lint` parameter "
            "with a list of check names to disable.\n"
            "This parameter can appear with each individual metric, or at the "
            "top-level to affect the entire file.",
            file=sys.stderr,
        )
        return True

    return False


def glinter(input_filepaths, parser_config={}):
    objs = parser.parse_objects(input_filepaths, parser_config)

    if util.report_validation_errors(objs):
        return 1

    if lint_metrics(objs.value):
        return 1

    print("✨ Your metrics are Glean! ✨")
    return 0
