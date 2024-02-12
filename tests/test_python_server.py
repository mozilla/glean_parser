# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from pathlib import Path
import io
import json

import shutil
import subprocess


from glean_parser import translate
from glean_parser import validate_ping


ROOT = Path(__file__).parent


def test_no_event_metrics(tmp_path):
    """If no event metrics are provided parser should fail
    and no files should be generated"""

    translate.translate(
        [],
        "python_server",
        tmp_path,
    )
    assert all(False for _ in tmp_path.iterdir())


def test_logging(tmp_path):
    """Test that generated code can be used to log events in the right format."""

    glean_module_path = tmp_path / "glean"

    # generate logging code
    translate.translate(
        [
            ROOT / "data" / "server_metrics_with_event.yaml",
        ],
        "python_server",
        glean_module_path,
    )

    # copy ROOT / "test-py" / "test.py" to tmpdir
    shutil.copy(ROOT / "test-py" / "test.py", tmp_path)

    # run test script
    logged_output = subprocess.check_output(["python", "test.py"], cwd=tmp_path).decode(
        "utf-8"
    )

    logged_output = json.loads(logged_output)
    fields = logged_output["Fields"]
    payload = fields["payload"]

    # validate that ping envelope contains all the required fields
    assert "glean-server-event" == logged_output["Type"]
    assert "accounts_backend" == fields["document_namespace"]
    assert "events" == fields["document_type"]
    assert "1" == fields["document_version"]
    assert "Mozilla/5.0 ..." == fields["user_agent"]

    schema_url = (
        "https://raw.githubusercontent.com/mozilla-services/"
        "mozilla-pipeline-schemas/main/"
        "schemas/glean/glean/glean.1.schema.json"
    )

    # validate that ping payload is valid against glean schema
    input = io.StringIO(payload)
    output = io.StringIO()
    assert (
        validate_ping.validate_ping(input, output, schema_url=schema_url) == 0
    ), output.getvalue()
