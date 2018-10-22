# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/


from glean_parser import parser


def add_schema(chunk):
    chunk['$schema'] = parser._get_metrics_schema()['$id']
    return chunk
