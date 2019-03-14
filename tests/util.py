# -*- coding: utf-8 -*-

# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from glean_parser import parser


def add_required(chunk):
    DEFAULTS = {
        'type': 'string',
        'bugs': [0],
        'description': 'DESCRIPTION...',
        'notification_emails': ['nobody@nowhere.com'],
        'data_reviews': ['https://nowhere.com/review/'],
        'expires': 'never',
    }

    for category_key, category_val in chunk.items():
        for metric in category_val.values():
            for default_name, default_val in DEFAULTS.items():
                if default_name not in metric:
                    metric[default_name] = default_val

    chunk['$schema'] = parser._get_metrics_schema()[0]['$id']

    return chunk
