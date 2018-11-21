# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

import io
import json

from glean_parser import validate_ping


def test_validate_ping():
    content = {
        "experiments": {
            "experiment2": {
                "branch": "branch_b",
                "extra": {
                    "key": "value"
                }
            }
        },
        "metrics": {
            "string": {
                "telemetry.string_metric": "foo"
            }
        },
        "ping_info": {
            "ping_type": "metrics",
            "telemetry_sdk_build": "0.32.0",
            "seq": 0,
            "app_build": "test-placeholder",
            "client_id": "900b6d8c-34d2-44d4-926d-83bde790474f",
            "start_time": "2018-11-19T16:19-05:00",
            "end_time": "2018-11-19T16:19-05:00"
        }
    }

    input = io.StringIO(json.dumps(content))
    output = io.StringIO()

    schema_url = (
        'https://raw.githubusercontent.com/mozilla-services/'
        'mozilla-pipeline-schemas/3a15121c582ef0cffe430da024a5bf11b7c48740/'
        'schemas/glean/baseline/baseline.1.schema.json'
    )

    assert validate_ping.validate_ping(
        input, output, schema_url=schema_url
    ) == 0
