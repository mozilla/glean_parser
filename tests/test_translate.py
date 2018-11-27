# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

import os
from pathlib import Path

import pytest

from glean_parser import translate


ROOT = Path(__file__).parent


def test_translate_unknown_format():
    with pytest.raises(ValueError) as e:
        translate.translate([], 'foo', '.')

    assert 'Unknown output format' in str(e)


def test_translate_missing_directory(tmpdir):
    output = Path(tmpdir) / 'foo'

    translate.translate(ROOT / 'data' / 'core.yaml', 'kotlin', output)

    assert len(os.listdir(output)) == 5
