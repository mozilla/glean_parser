# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from glean_parser.util import to_camel_case, remove_output_params


def test_camel_case_first_lowercase():
    assert "testMe" == to_camel_case("test_me", False)


def test_camel_case_first_uppercase():
    assert "TestMe" == to_camel_case("test_me", True)


def test_camel_case_empty_tokens():
    assert "testMe" == to_camel_case("__test____me", False)


def test_camel_case_dots_sanitized():
    assert "testMeYeah" == to_camel_case("__test..me.yeah", False)


def test_camel_case_numbers():
    assert "g33kS4n1t1z3d" == to_camel_case("g33k_s4n1t1z3d", False)


def test_camel_case_expected():
    assert "easyOne" == to_camel_case("easy_one", False)
    assert "moreInvolved1" == to_camel_case("more_involved_1", False)


def test_removing_output_params():
    d = {"name": "test dict", "defined_in": {"line": "42"}, "abc": "xyz"}

    output_removed = {"name": "test dict", "abc": "xyz"}

    test = remove_output_params(d, "defined_in")

    assert test == output_removed
