# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""Tests for the command line interface."""

import os
from pathlib import Path
import re

from click.testing import CliRunner

from glean_parser import __main__


ROOT = Path(__file__).parent


def test_basic_help():
    """Test the CLI."""
    runner = CliRunner()
    help_result = runner.invoke(__main__.main, ["--help"])
    assert help_result.exit_code == 0
    assert "Show this message and exit." in help_result.output


def test_translate(tmpdir):
    """Test the 'translate' command."""
    runner = CliRunner()
    result = runner.invoke(
        __main__.main,
        [
            "translate",
            str(ROOT / "data" / "core.yaml"),
            "-o",
            str(tmpdir),
            "-f",
            "kotlin",
            "-s",
            "namespace=Foo",
            "--allow-reserved",
        ],
    )
    assert result.exit_code == 0
    assert set(os.listdir(str(tmpdir))) == set(
        [
            "CorePing.kt",
            "Telemetry.kt",
            "Environment.kt",
            "DottedCategory.kt",
            "GleanInternalMetrics.kt",
            "GleanBuildInfo.kt",
        ]
    )
    for filename in os.listdir(str(tmpdir)):
        path = Path(str(tmpdir)) / filename
        with path.open(encoding="utf-8") as fd:
            content = fd.read()
        assert "package Foo" in content


def test_translate_no_buildinfo(tmpdir):
    """Test the 'translate' command."""
    runner = CliRunner()
    result = runner.invoke(
        __main__.main,
        [
            "translate",
            str(ROOT / "data" / "core.yaml"),
            "-o",
            str(tmpdir),
            "-f",
            "kotlin",
            "-s",
            "namespace=Foo",
            "-s",
            "with_buildinfo=false",
            "--allow-reserved",
        ],
    )
    assert result.exit_code == 0
    assert set(os.listdir(str(tmpdir))) == set(
        [
            "CorePing.kt",
            "Telemetry.kt",
            "Environment.kt",
            "DottedCategory.kt",
            "GleanInternalMetrics.kt",
        ]
    )
    for filename in os.listdir(str(tmpdir)):
        path = Path(str(tmpdir)) / filename
        with path.open(encoding="utf-8") as fd:
            content = fd.read()
        assert "package Foo" in content


def test_translate_errors(tmpdir):
    """Test the 'translate' command."""
    runner = CliRunner()
    result = runner.invoke(
        __main__.main,
        [
            "translate",
            str(ROOT / "data" / "invalid.yamlx"),
            "-o",
            str(tmpdir),
            "-f",
            "kotlin",
        ],
    )
    assert result.exit_code == 1
    assert len(os.listdir(str(tmpdir))) == 0


def test_translate_invalid_format(tmpdir):
    """Test passing an invalid format to the 'translate' command."""
    runner = CliRunner()
    result = runner.invoke(
        __main__.main,
        ["translate", str(ROOT / "data" / "core.yaml"), "-o", str(tmpdir), "-f", "foo"],
    )
    assert result.exit_code == 2
    assert re.search("Invalid value for ['\"]--format['\"]", result.output)


def test_reject_jwe(tmpdir):
    """Test that the JWE type is rejected"""
    runner = CliRunner()
    result = runner.invoke(
        __main__.main,
        [
            "translate",
            str(ROOT / "data" / "jwe.yaml"),
            "-o",
            str(tmpdir),
            "-f",
            "kotlin",
        ],
    )
    assert result.exit_code == 1
    assert len(os.listdir(str(tmpdir))) == 0
