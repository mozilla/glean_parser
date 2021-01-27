# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from glean_parser import parser

import util


def test_reserved_ping_name():
    """
    Make sure external users can't use a reserved ping name.
    """
    content = {"baseline": {"include_client_id": True}}

    util.add_required_ping(content)
    errors = list(parser._instantiate_pings({}, {}, content, "", {}))
    assert len(errors) == 1
    assert "Ping uses a reserved name" in errors[0]

    errors = list(
        parser._instantiate_pings({}, {}, content, "", {"allow_reserved": True})
    )
    assert len(errors) == 0


def test_reserved_metrics_category():
    """
    The category "pings" can't be used by metrics -- it's reserved for pings.
    """
    content = {"pings": {"metric": {"type": "string"}}}

    util.add_required(content)
    errors = list(parser.parse_objects(content))
    assert len(errors) == 1
    assert "reserved" in errors[0]


def test_camel_case_ping_name():
    content = {"camelCasePingName": {"include_client_id": True}}

    util.add_required_ping(content)
    errors = list(parser.parse_objects([content]))
    assert len(errors) == 1
    assert "camelCasePingName" in errors[0]


def test_snake_case_ping_name():
    content = {"snake_case_ping_name": {"include_client_id": True}}

    util.add_required_ping(content)
    errors = list(parser.parse_objects([content]))
    assert len(errors) == 1
    assert "snake_case_ping_name" in errors[0]


def test_legacy_snake_case_ping_name():
    content = {
        "bookmarks_sync": {"include_client_id": True},
        "$schema": "moz://mozilla.org/schemas/glean/pings/1-0-0",
    }

    util.add_required_ping(content)
    errors = list(parser.parse_objects([content]))
    assert len(errors) == 0


def test_send_if_empty():
    content = {"valid-ping": {"include_client_id": True, "send_if_empty": True}}

    util.add_required_ping(content)
    errors = list(parser.parse_objects([content]))
    assert len(errors) == 0
