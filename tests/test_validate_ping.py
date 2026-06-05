# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

import io
import json
import pytest
from pytest import raises

from glean_parser import validate_ping


@pytest.mark.web_dependency
def test_validate_ping():
    content = {
        "client_info": {
            "telemetry_sdk_build": "0.32.0",
            "first_run_date": "2018-11-19T16:19-05:00",
            "os": "Android",
            "os_version": "27",
            "architecture": "arm",
            "app_build": "test-placeholder",
            "app_display_version": "1.0.0",
            "client_id": "900b6d8c-34d2-44d4-926d-83bde790474f",
        },
        "metrics": {"string": {"telemetry.string_metric": "foo"}},
        "ping_info": {
            "ping_type": "metrics",
            "seq": 0,
            "start_time": "2018-11-19T16:19-05:00",
            "end_time": "2018-11-19T16:19-05:00",
            "experiments": {
                "experiment2": {"branch": "branch_b", "extra": {"key": "value"}}
            },
        },
    }

    input = io.StringIO(json.dumps(content))
    output = io.StringIO()

    schema_url = (
        "https://raw.githubusercontent.com/mozilla-services/"
        "mozilla-pipeline-schemas/ebe7c6ea843626e57b5219092a57ff55f19b805e/"
        "schemas/glean/glean/glean.1.schema.json"
    )

    assert validate_ping.validate_ping(input, output, schema_url=schema_url) == 0

    with raises(TypeError):
        validate_ping.validate_ping(input, output)
