#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `glean_parser` package."""


from click.testing import CliRunner

from glean_parser import cli


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert 'glean_parser.cli.main' in result.output
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help  Show this message and exit.' in help_result.output
