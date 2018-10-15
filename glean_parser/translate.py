# -*- coding: utf-8 -*-

"""
High-level interface for translating `metrics.yaml` into other formats.
"""

import os

from . import parser
from . import kotlin


OUTPUTTERS = {
    'kotlin': kotlin.output_kotlin
}


def translate(input_filepaths, output_format, output_dir):
    """
    """
    if output_format not in OUTPUTTERS:
        raise ValueError(f"Unknown output format '{output_format}'")

    all_metrics = parser.parse_metrics(input_filepaths)
    if not output_dir.is_dir():
        os.makedirs(output_dir)
    OUTPUTTERS[output_format](all_metrics, output_dir)
