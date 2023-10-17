# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from pathlib import Path

import glean_parser
from glean_parser import translate

ROOT = Path(__file__).parent


def test_parser_rb_server_ping_file(tmpdir, capsys):
    """Test that no files are generated if ping definition
    is provided."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        [
            ROOT / "data" / "ruby_server_metrics.yaml",
            ROOT / "data" / "ruby_server_pings.yaml",
        ],
        "ruby_server",
        tmpdir,
    )
    captured = capsys.readouterr()
    assert all(False for _ in tmpdir.iterdir())
    assert (
        "Ping definition found. Server-side environment is simplified" in captured.out
    )


def test_parser_rb_server_no_event_metrics(tmpdir, capsys):
    """Test that no files are generated if no event metrics."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        [ROOT / "data" / "ruby_server_no_events.yaml"],
        "ruby_server",
        tmpdir,
    )
    captured = capsys.readouterr()
    assert all(False for _ in tmpdir.iterdir())
    assert (
        "No event metrics found...at least one event metric is required" in captured.out
    )


def test_parser_rb_server_metrics_unsupported_type(tmpdir, capsys):
    """Test that no files are generated with unsupported metric types."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        [
            ROOT / "data" / "ruby_server_metrics_unsupported.yaml",
        ],
        "ruby_server",
        tmpdir,
    )
    captured = capsys.readouterr()
    assert "Ignoring unsupported metric type" in captured.out
    assert "boolean" in captured.out


def test_parser_rb_server_pings_unsupported_type(tmpdir, capsys):
    """Test that no files are generated with ping types that are not `events`."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        [
            ROOT / "data" / "ruby_server_pings_unsupported.yaml",
        ],
        "ruby_server",
        tmpdir,
    )
    captured = capsys.readouterr()
    assert "Non-events ping reference found" in captured.out
    assert "Ignoring the tests ping type" in captured.out


def test_parser_rb_server(tmpdir):
    """Test that parser works"""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        [ROOT / "data" / "ruby_server_metrics.yaml"],
        "ruby_server",
        tmpdir,
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["server_events.rb"])

    # Make sure string metric made it in
    with (tmpdir / "server_events.rb").open("r", encoding="utf-8") as fd:
        content = fd.read()
        with (ROOT / "data" / "server_events_compare.rb").open(
            "r", encoding="utf-8"
        ) as cd:
            compare_raw = cd.read()
    compare = compare_raw.format(
        current_version=f"glean_parser v{glean_parser.__version__}"
    )
    assert content == compare
