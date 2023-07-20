# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from pathlib import Path

from glean_parser import javascript_server
from glean_parser import translate


ROOT = Path(__file__).parent


def test_parser_js_server_ping_no_metrics(tmpdir):
    """Test that no files are generated if only ping definitions
    are provided without any metrics."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "fxa-server-pings.yaml",
        "javascript_server",
        tmpdir,
    )

    assert all(False for _ in tmpdir.iterdir())


def test_parser_js_server_metrics_no_ping(tmpdir):
    """Test that no files are generated if only metric definitions
    are provided without pings."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        ROOT / "data" / "fxa-server-metrics.yaml",
        "javascript_server",
        tmpdir,
    )

    assert all(False for _ in tmpdir.iterdir())


def test_parser_js_server(tmpdir):
    """Test that no files are generated if only metric definitions
    are provided without pings."""
    tmpdir = Path(str(tmpdir))

    translate.translate(
        [
            ROOT / "data" / "fxa-server-pings.yaml",
            ROOT / "data" / "fxa-server-metrics.yaml",
        ],
        "javascript_server",
        tmpdir,
    )

    assert set(x.name for x in tmpdir.iterdir()) == set(["server_events.js"])

    # Make sure string metric made it in
    with (tmpdir / "server_events.js").open("r", encoding="utf-8") as fd:
        content = fd.read()
        assert "'event.name': event_name" in content


def test_generate_ping_factory_method():
    ping = "accounts_events"
    expected_result = "createAccountsEventsEvent"
    result = javascript_server.generate_ping_factory_method(ping)
    assert result == expected_result
