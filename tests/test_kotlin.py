# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

import os
from pathlib import Path

from glean_parser import kotlin
from glean_parser import translate


ROOT = Path(__file__).parent


def test_parser(tmpdir):
    """Test translating metrics to Kotlin files."""
    translate.translate(ROOT / "data" / "core.yaml", 'kotlin', Path(tmpdir))

    assert (
        set(os.listdir(tmpdir)) ==
        set(['CorePing.kt', 'Telemetry.kt', 'Environment.kt'])
    )

    # Make sure descriptions made it in
    with open(tmpdir / 'CorePing.kt', 'r', encoding='utf-8') as fd:
        content = fd.read()
        assert ('True if the user has set Firefox as the default browser.'
                in content)

    with open(tmpdir / 'Telemetry.kt', 'r', encoding='utf-8') as fd:
        content = fd.read()
        assert 'جمع 搜集' in content


def test_kotlin_generator():
    kdf = kotlin.kotlin_datatypes_filter

    assert kdf("\n") == r'"\n"'
    assert kdf([42, "\n"]) == r'listOf(42, "\n")'
    assert kdf({'key': 'value', 'key2': 'value2'}) == \
        r'mapOf("key" to "value", "key2" to "value2")'
