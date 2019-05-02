# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from pathlib import Path

import pytest

from glean_parser import parser
from glean_parser import translate

import util


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


def test_translate_expires():
    contents = [
        {
            'metrics': {
                'a': {
                    'type': 'counter',
                    'expires': 'never'
                },
                'b': {
                    'type': 'counter',
                    'expires': 'expired'
                },
                'c': {
                    'type': 'counter',
                    'expires': '2000-01-01'
                },
                'd': {
                    'type': 'counter',
                    'expires': '2100-01-01'
                }
            }
        }
    ]
    contents = [util.add_required(x) for x in contents]

    objs = parser.parse_objects(contents)
    assert len(list(objs)) == 0
    objs = objs.value

    translate._preprocess_objects(objs)

    assert objs['metrics']['a'].disabled is False
    assert objs['metrics']['b'].disabled is True
    assert objs['metrics']['c'].disabled is True
    assert objs['metrics']['d'].disabled is False


def test_translate_send_in_pings(tmpdir):
    contents = [
        {
            'baseline': {
                'counter': {
                    'type': 'counter'
                },
                'event': {
                    'type': 'event'
                },
                'c': {
                    'type': 'counter',
                    'send_in_pings': ['default', 'custom']
                }
            }
        }
    ]
    contents = [util.add_required(x) for x in contents]

    objs = parser.parse_objects(contents)
    assert len(list(objs)) == 0
    objs = objs.value

    translate._preprocess_objects(objs)

    assert objs['baseline']['counter'].send_in_pings == ['metrics']
    assert objs['baseline']['event'].send_in_pings == ['events']
    assert objs['baseline']['c'].send_in_pings == ['metrics', 'custom']
