# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from pathlib import Path
import shutil
import subprocess

from glean_parser import kotlin
from glean_parser import metrics
from glean_parser import translate


ROOT = Path(__file__).parent


def test_parser(tmpdir):
    """Test translating metrics to Kotlin files."""
    tmpdir = Path(tmpdir)

    translate.translate(
        ROOT / "data" / "core.yaml",
        'kotlin',
        tmpdir,
        {'namespace': 'Foo'}
    )

    assert (
        set(x.name for x in tmpdir.iterdir()) ==
        set([
            'CorePing.kt',
            'Telemetry.kt',
            'Environment.kt',
            'DottedCategory.kt',
            'GleanInternalMetrics.kt'
        ])
    )

    # Make sure descriptions made it in
    with open(tmpdir / 'CorePing.kt', 'r', encoding='utf-8') as fd:
        content = fd.read()
        assert ('True if the user has set Firefox as the default browser.'
                in content)
        # Make sure the namespace option is in effect
        assert 'package Foo' in content

    with open(tmpdir / 'Telemetry.kt', 'r', encoding='utf-8') as fd:
        content = fd.read()
        assert 'جمع 搜集' in content

    with open(tmpdir / 'GleanInternalMetrics.kt', 'r', encoding='utf-8') as fd:
        content = fd.read()
        assert 'category = ""' in content

    # Only run this test if ktlint is on the path
    if shutil.which('ktlint'):
        for filepath in tmpdir.glob('*.kt'):
            subprocess.check_call(['ktlint', filepath])


def test_kotlin_generator():
    kdf = kotlin.kotlin_datatypes_filter

    assert kdf("\n") == r'"\n"'
    assert kdf([42, "\n"]) == r'listOf(42, "\n")'
    assert kdf({'key': 'value', 'key2': 'value2'}) == \
        r'mapOf("key" to "value", "key2" to "value2")'
    assert kdf(metrics.Lifetime.ping) == 'Lifetime.Ping'
