# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from glean_parser import parser


def add_required(chunk):
    DEFAULTS = {
        "type": "string",
        "bugs": ["http://bugzilla.mozilla.org/12345678"],
        "description": "DESCRIPTION...",
        "notification_emails": ["nobody@example.com"],
        "data_reviews": ["https://example.com/review/"],
        "expires": "never",
    }

    for category_key, category_val in chunk.items():
        if category_key in ("$schema", "$tags", "no_lint"):
            continue
        for metric in category_val.values():
            for default_name, default_val in DEFAULTS.items():
                if default_name not in metric:
                    metric[default_name] = default_val

    if "$schema" not in chunk:
        chunk["$schema"] = parser.METRICS_ID

    return chunk


def add_required_ping(chunk):
    DEFAULTS = {
        "bugs": ["http://bugzilla.mozilla.org/12345678"],
        "description": "DESCRIPTION...",
        "notification_emails": ["nobody@nowhere.com"],
        "data_reviews": ["https://nowhere.com/review/"],
        "include_client_id": True,
    }

    for ping_name, ping in chunk.items():
        if ping_name in ("no_lint", "$schema"):
            continue
        for default_name, default_val in DEFAULTS.items():
            if default_name not in ping:
                ping[default_name] = default_val

    if "$schema" not in chunk:
        chunk["$schema"] = parser.PINGS_ID

    return chunk
