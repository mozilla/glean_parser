from glean_parser import parser


def test_basic_tags():
    content = {
        "$schema": "moz://mozilla.org/schemas/glean/tags/1-0-0",
        "Tag": {"description": "Normal tag"},
        "Testing :: General": {"description": "Testing / General"},
    }
    objs = parser.parse_objects([content])

    errors = list(objs)
    assert len(errors) == 0

    tags = objs.value["tags"]
    assert set(tags.keys()) == set(["Tag", "Testing :: General"])
    assert tags["Tag"].description == content["Tag"]["description"]


def test_tags_description_required():
    content = {
        "$schema": "moz://mozilla.org/schemas/glean/tags/1-0-0",
        "Tag": {},
    }
    errors = list(parser.parse_objects([content]))
    assert len(errors) == 1
    assert "Missing required properties: description" in errors[0]


def test_tags_extra_keys_not_allowed():
    content = {
        "$schema": "moz://mozilla.org/schemas/glean/tags/1-0-0",
        "Tag": {"description": "Normal tag", "extra": "Extra stuff"},
    }
    errors = list(parser.parse_objects([content]))
    assert len(errors) == 1
    assert "Additional properties are not allowed" in errors[0]


def test_tags_name_too_long():
    content = {
        "$schema": "moz://mozilla.org/schemas/glean/tags/1-0-0",
        "Tag" * 80: {"description": "This name is way too long"},
    }
    errors = list(parser.parse_objects([content]))
    assert len(errors) == 1
    assert "TagTagTag' is too long" in errors[0]
