# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
High-level interface for translating `metrics.yaml` into other formats.
"""

from pathlib import Path
import shutil
import sys
import tempfile

from . import parser
from . import kotlin


OUTPUTTERS = {
    'kotlin': kotlin.output_kotlin
}


def translate(
        input_filepaths,
        output_format,
        output_dir,
        options={},
        parser_config={}
):
    """
    Translate the files in `input_filepaths` to the given `output_format` and
    put the results in `output_dir`.

    :param input_filepaths: list of paths to input metrics.yaml files
    :param output_format: the name of the output formats
    :param output_dir: the path to the output directory
    :param options: dictionary of options. The available options are backend
        format specific.
    :param parser_config: A dictionary of options that change parsing behavior.
        See `parser.parse_metrics` for more info.
    """
    if output_format not in OUTPUTTERS:
        raise ValueError(f"Unknown output format '{output_format}'")

    all_metrics = parser.parse_metrics(input_filepaths, parser_config)
    found_error = False
    for error in all_metrics:
        found_error = True
        print('=' * 78, file=sys.stderr)
        print(error, file=sys.stderr)
    if found_error:
        return 1

    # Write everything out to a temporary directory, and then move it to the
    # real directory, for transactional integrity.
    with tempfile.TemporaryDirectory() as tempdir:
        OUTPUTTERS[output_format](all_metrics.value, Path(tempdir), options)

        if output_dir.is_file():
            output_dir.unlink()
        elif output_dir.is_dir():
            shutil.rmtree(output_dir)

        shutil.copytree(tempdir, output_dir)

    return 0
