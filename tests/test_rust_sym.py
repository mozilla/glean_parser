# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

# Very minimal testing for `rust_sym` support.
# We're reusing most of the `rust` translator work,
# so we're only testing that the generated code is at least still valid Rust.

from pathlib import Path
import shutil
import subprocess

from glean_parser import translate


ROOT = Path(__file__).parent


def run_linters(files):
    # Syntax check on the generated files.
    # Only run this test if cargo is on the path.
    if shutil.which("rustfmt"):
        for filepath in files:
            subprocess.check_call(
                [
                    "rustfmt",
                    "--check",
                    filepath,
                ]
            )
    if shutil.which("cargo"):
        for filepath in files:
            subprocess.check_call(
                [
                    "cargo",
                    "clippy",
                    "--all",
                    "--",
                    "-D",
                    "warnings",
                    filepath,
                ]
            )


def test_parser(tmp_path):
    """Test translating metrics to Rust files."""
    translate.translate(
        ROOT / "data" / "core.yaml", "rust_sym", tmp_path, {}, {"allow_reserved": True}
    )

    assert set(x.name for x in tmp_path.iterdir()) == set(["glean_metrics.rs"])

    # Make sure descriptions made it in
    with (tmp_path / "glean_metrics.rs").open("r", encoding="utf-8") as fd:
        content = fd.read()

        assert "True if the user has set Firefox as the default browser." in content
        assert "جمع 搜集" in content
        assert 'category: "telemetry"' in content
