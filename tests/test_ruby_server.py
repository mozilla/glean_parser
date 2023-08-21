# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from pathlib import Path

import glean_parser
from glean_parser import translate

ROOT = Path(__file__).parent


def test_parser_rb_server_ping_no_metrics(tmpdir):
    """Test that no files are generated if only ping definitions
    are provided without any metrics."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "mastodon_pings.yaml",
        "ruby_server",
        tmpdir,
    )

    assert all(False for _ in tmpdir.iterdir())


def test_parser_rb_server_metrics_no_ping(tmpdir):
    """Test that no files are generated if only metric definitions
    are provided without pings."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "mastodon_metrics.yaml",
        "ruby_server",
        tmpdir,
    )

    assert all(False for _ in tmpdir.iterdir())


def test_parser_rb_server_metrics_unsupported_type(tmpdir, capfd):
    """Test that no files are generated if only metric definitions
    are provided without pings."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        [
            ROOT / "data" / "mastodon_pings.yaml",
            ROOT / "data" / "all_metrics.yaml",
        ],
        "ruby_server",
        tmpdir,
    )
    out, err = capfd.readouterr()
    assert len(out.split("\n")) == 20


def test_parser_rb_server(tmpdir):
    """Test that parser works"""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        [
            ROOT / "data" / "mastodon_pings.yaml",
            ROOT / "data" / "mastodon_metrics.yaml",
        ],
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
