# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import re
import sys


GLEAN_METRICS_NAMESPACE = "GleanMetrics"


def _get_glean_metrics_category(cls_name, metrics_namespace=GLEAN_METRICS_NAMESPACE):
    """
    Given a Kotlin class name, returns the Glean metric category that it
    represents.

    If this doesn't look like a class containing Glean metrics (i.e. the second
    to last path name is not `metrics_namespace`), then returns None.
    """
    match = re.match(rf"L.*{metrics_namespace}/(?P<category>.*);$", cls_name)
    if match is not None:
        return match["category"]
    return None


def _is_metric_method(desc):
    """
    Returns True if the method descriptor describes a method that returns a
    Glean MetricType.
    """
    # This will need to be updated if the Java namespace that Glean metric
    # types are defined in changes.
    return (
        re.match(r"\(\)Lmozilla/components/service/glean/private/.*MetricType;$", desc)
        is not None
    )


def _format_classes(classes):
    """
    Format the class names that androguard returns into something resembling
    how they appear in Kotlin source code.
    """
    return ", ".join(cls[1:-1].replace("/", ".") for cls in classes)


def check_apk(apk_file):
    """
    Check an .apk file for duplicate metrics.
    """
    # This uses the androguard library [1] under the hood to do the heavy lifting.
    #
    #    [1] https://androguard.readthedocs.io/en/latest/index.html
    #
    # Imported here so that androguard is not a hard requirement for other
    # glean_parser features.
    from androguard.misc import AnalyzeAPK

    print("Analyzing APK (takes a long time)...")
    apk, dvf, analysis = AnalyzeAPK(apk_file)

    metric_sources = {}

    for cls in analysis.get_classes():
        # Does this look like a class containing Glean metrics?
        category = _get_glean_metrics_category(cls.name)
        if category is None:
            continue

        # Iterate over the fields, and find a corresponding method that lazily
        # instantiates the field. This method has the same name as the field
        # with a `get` prefix.
        for field in cls.get_fields():
            method_name = f"get{field.name.capitalize()}"
            for method in cls.get_methods():
                if method.name == method_name:
                    desc = method.descriptor
                    if _is_metric_method(desc):
                        # We found a Glean metric definition. Record it.
                        key = (category, field.name)
                        metric_sources.setdefault(key, []).append(cls.name)

    # Now report if there were any duplicates
    duplicates = dict((k, v) for (k, v) in metric_sources.items() if len(v) > 1)
    if len(duplicates):
        for (category, name), classes in sorted(list(duplicates.items())):
            print(
                f"Metric {category}.{name} defined more than once in "
                f"{_format_classes(classes)}",
                file=sys.stderr,
            )
        return 1

    return 0
