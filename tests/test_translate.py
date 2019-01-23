# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

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

    translate.translate(
        ROOT / 'data' / 'core.yaml',
        'kotlin',
        output,
        parser_config={'allow_reserved': True}
    )

    assert len(list(output.iterdir())) == 5


def test_translate_remove_obsolete_files(tmpdir):
    output = Path(tmpdir) / 'foo'

    translate.translate(
        ROOT / 'data' / 'core.yaml',
        'kotlin',
        output,
        parser_config={'allow_reserved': True}
    )

    assert len(list(output.iterdir())) == 5

    translate.translate(ROOT / 'data' / 'smaller.yaml', 'kotlin', output)

    assert len(list(output.iterdir())) == 1
