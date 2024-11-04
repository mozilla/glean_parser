# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from pathlib import Path
import io
import json
import pytest
import subprocess

import glean_parser
from glean_parser import translate
from glean_parser import validate_ping

ROOT = Path(__file__).parent


def test_parser_rust_server_ping_no_metrics(tmp_path, capsys):
    """Test that no files are generated if only ping definitions
    are provided without any metrics."""
    translate.translate(
        ROOT / "data" / "server_pings.yaml",
        "go_server",
        tmp_path,
    )
    assert all(False for _ in tmp_path.iterdir())
