# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

import io
import os
import pickle
import sqlite3

import diskcache_community as diskcache

from glean_parser import util
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


def _run_planted(path):
    with open(path, "w") as fd:
        fd.write("ran")
    return "planted"


class _Planted:
    def __init__(self, path):
        self.path = path

    def __reduce__(self):
        return (_run_planted, (self.path,))


def test_fetch_remote_url_cache(tmp_path, monkeypatch):
    cache_dir = tmp_path / "cache"
    monkeypatch.setattr(util.platformdirs, "user_cache_dir", lambda *a: str(cache_dir))
    calls = []

    def urlopen(url):
        calls.append(url)
        return io.BytesIO(b"schema contents")

    monkeypatch.setattr(util.urllib.request, "urlopen", urlopen)
    url = "https://example.com/schema.json"

    assert util.fetch_remote_url(url) == "schema contents"
    assert util.fetch_remote_url(url) == "schema contents"
    assert len(calls) == 1

    # A row rewritten by someone else to hold a pickle is a miss, not code
    # that runs: the contents are fetched again and the pickle never loads.
    marker = tmp_path / "marker"
    con = sqlite3.connect(os.path.join(str(cache_dir), "cache.db"))
    con.execute(
        "UPDATE Cache SET mode = 4, value = ?",
        (pickle.dumps(_Planted(str(marker)), protocol=2),),
    )
    con.commit()
    con.close()

    assert util.fetch_remote_url(url) == "schema contents"
    assert len(calls) == 2
    assert not marker.exists()


def test_fetch_remote_url_reads_existing_jsondisk_cache(tmp_path, monkeypatch):
    cache_dir = tmp_path / "cache"
    monkeypatch.setattr(util.platformdirs, "user_cache_dir", lambda *a: str(cache_dir))
    monkeypatch.setattr(util.urllib.request, "urlopen", None)
    url = "https://example.com/schema.json"

    # Entries written by earlier releases, through JSONDisk, are still read.
    key = (url, str(util.sys.version_info))
    with diskcache.Cache(str(cache_dir), disk=diskcache.JSONDisk) as dc:
        dc[key] = "cached earlier"

    assert util.fetch_remote_url(url) == "cached earlier"
