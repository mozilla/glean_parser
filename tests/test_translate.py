# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from pathlib import Path

import pytest
import shutil

from glean_parser import parser
from glean_parser import translate
from glean_parser.util import load_yaml_or_json

import util


ROOT = Path(__file__).parent


def test_translate_unknown_format():
    with pytest.raises(ValueError) as e:
        translate.translate([], "foo", ".")

    assert "Unknown output format" in str(e)


def test_translate_missing_directory(tmpdir):
    output = Path(str(tmpdir)) / "foo"

    translate.translate(
        ROOT / "data" / "core.yaml",
        "kotlin",
        output,
        parser_config={"allow_reserved": True},
    )

    assert len(list(output.iterdir())) == 6


def test_translate_missing_input_files(tmpdir):
    output = Path(str(tmpdir))

    with pytest.raises(FileNotFoundError):
        translate.translate(
            ROOT / "data" / "missing.yaml",
            "kotlin",
            output,
            parser_config={"allow_reserved": True},
        )

    assert 0 == translate.translate(
        ROOT / "data" / "missing.yaml",
        "kotlin",
        output,
        parser_config={"allow_reserved": True, "allow_missing_files": True},
    )


def test_translate_remove_obsolete_kotlin_files(tmpdir):
    output = Path(str(tmpdir)) / "foo"

    translate.translate(
        ROOT / "data" / "core.yaml",
        "kotlin",
        output,
        parser_config={"allow_reserved": True},
    )

    assert len(list(output.iterdir())) == 6

    translate.translate(ROOT / "data" / "smaller.yaml", "kotlin", output)

    assert len(list(output.iterdir())) == 2


def test_translate_retains_existing_markdown_files(tmpdir):
    output = Path(str(tmpdir)) / "foo"

    translate.translate(
        ROOT / "data" / "core.yaml",
        "markdown",
        output,
        parser_config={"allow_reserved": True},
    )

    # Move the file to a different location, translate always writes to
    # metrics.md.
    shutil.move(str(output / "metrics.md"), str(output / "old.md"))

    assert len(list(output.iterdir())) == 1

    translate.translate(ROOT / "data" / "smaller.yaml", "markdown", output)

    assert len(list(output.iterdir())) == 2


def test_translate_expires():
    contents = [
        {
            "metrics": {
                "a": {"type": "counter", "expires": "never"},
                "b": {"type": "counter", "expires": "expired"},
                "c": {"type": "counter", "expires": "2000-01-01"},
                "d": {"type": "counter", "expires": "2100-01-01"},
            }
        }
    ]
    contents = [util.add_required(x) for x in contents]

    objs = parser.parse_objects(contents)
    assert len(list(objs)) == 0
    objs = objs.value

    assert objs["metrics"]["a"].disabled is False
    assert objs["metrics"]["b"].disabled is True
    assert objs["metrics"]["c"].disabled is True
    assert objs["metrics"]["d"].disabled is False


def test_translate_send_in_pings(tmpdir):
    contents = [
        {
            "baseline": {
                "counter": {"type": "counter"},
                "event": {"type": "event"},
                "c": {"type": "counter", "send_in_pings": ["default", "custom"]},
            }
        }
    ]
    contents = [util.add_required(x) for x in contents]

    objs = parser.parse_objects(contents)
    assert len(list(objs)) == 0
    objs = objs.value

    assert objs["baseline"]["counter"].send_in_pings == ["metrics"]
    assert objs["baseline"]["event"].send_in_pings == ["events"]
    assert objs["baseline"]["c"].send_in_pings == ["custom", "metrics"]


def test_translate_dont_remove_extra_files(tmpdir):
    output = Path(str(tmpdir)) / "foo"
    output.mkdir()

    with (output / "extra.txt").open("w") as fd:
        fd.write("\n")

    translate.translate(
        ROOT / "data" / "core.yaml",
        "kotlin",
        output,
        parser_config={"allow_reserved": True},
    )

    assert len(list(output.iterdir())) == 7
    assert "extra.txt" in [str(x.name) for x in output.iterdir()]


def test_external_translator(tmpdir):
    tmpdir = Path(str(tmpdir))

    def external_translator(all_objects, output_dir, options):
        assert {"foo": "bar", "allow_reserved": True} == options

        for category in all_objects:
            with (tmpdir / category).open("w") as fd:
                for metric in category:
                    fd.write(f"{metric}\n")

    translate.translate_metrics(
        ROOT / "data" / "core.yaml",
        Path(str(tmpdir)),
        external_translator,
        [],
        options={"foo": "bar"},
        parser_config={"allow_reserved": True},
    )

    content = load_yaml_or_json(ROOT / "data" / "core.yaml")

    expected_keys = set(content.keys()) - set(["$schema"])

    assert set(x.name for x in tmpdir.iterdir()) == expected_keys


def test_getting_line_number():
    pings = load_yaml_or_json(ROOT / "data" / "pings.yaml")
    metrics = load_yaml_or_json(ROOT / "data" / "core.yaml")

    assert pings["custom-ping"].defined_in["line"] == 7
    assert metrics["core_ping"]["seq"].defined_in["line"] == 28


def test_rates(tmpdir):
    def external_translator(all_objects, output_dir, options):
        assert (
            all_objects["testing.rates"]["has_external_denominator"].type == "rate"
        )  # Hasn't yet been transformed

        translate.transform_metrics(all_objects)

        category = all_objects["testing.rates"]
        assert category["has_internal_denominator"].type == "rate"
        assert category["has_external_denominator"].type == "numerator"
        assert (
            category["has_external_denominator"].denominator_metric
            == "testing.rates.the_denominator"
        )
        assert category["also_has_external_denominator"].type == "numerator"
        assert (
            category["also_has_external_denominator"].denominator_metric
            == "testing.rates.the_denominator"
        )
        assert category["the_denominator"].type == "denominator"
        assert category["the_denominator"].numerators == [
            "testing.rates.has_external_denominator",
            "testing.rates.also_has_external_denominator",
        ]

    translate.translate_metrics(
        ROOT / "data" / "rate.yaml",
        Path(str(tmpdir)),
        external_translator,
        [],
        options={"foo": "bar"},
        parser_config={"allow_reserved": True},
    )
