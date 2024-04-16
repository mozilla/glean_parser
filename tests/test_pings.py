# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from glean_parser import parser, pings

import util


def test_reserved_ping_name():
    """
    Make sure external users can't use a reserved ping name.
    """

    for ping in pings.RESERVED_PING_NAMES:
        content = {ping: {"include_client_id": True}}

        util.add_required_ping(content)
        errors = list(parser._instantiate_pings({}, {}, content, "", {}))
        assert len(errors) == 1, f"Ping '{ping}' should not be allowed"
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


def test_send_if_disabled():
    content = {"disabled-ping": {"include_client_id": True, "enabled": False}}

    util.add_required_ping(content)
    errors = list(parser.parse_objects([content]))
    assert len(errors) == 0


def test_ping_schedule():
    content = {
        "piggyback-ping": {
            "include_client_id": True,
            "metadata": {"ping_schedule": ["trigger-ping"]},
        },
        "trigger-ping": {"include_client_id": True},
    }

    util.add_required_ping(content)
    all_pings = parser.parse_objects([content])
    errors = list(all_pings)
    assert len(errors) == 0
    assert "piggyback-ping" in all_pings.value["pings"]["trigger-ping"].schedules_pings


def test_no_self_ping_schedule():
    content = {
        "my_ping": {
            "include_client_id": True,
            "metadata": {"ping_schedule": ["my_ping"]},
        }
    }

    util.add_required_ping(content)
    errors = list(parser.parse_objects([content]))
    assert "my_ping" in errors[0]
