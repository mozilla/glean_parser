# -*- coding: utf-8 -*-

import os
from pathlib import Path

from glean_parser import parser, kotlin


ROOT = Path(__file__).parent


def test_parser(tmpdir):
    """Test translating metrics to Kotlin files."""
    metrics = parser.parse_metrics(ROOT / "data" / "core.yaml")
    kotlin.output_kotlin(metrics, tmpdir)

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
