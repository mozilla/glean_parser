#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""The setup script."""

import sys

from setuptools import setup, find_packages


if sys.version_info < (3, 7):
    print(
        "glean_parser requires at least Python 3.7",
        file=sys.stderr
    )
    sys.exit(1)


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'Click>=6.0',
    'PyYAML>=3.13',
    'jsonschema>=3.0.0',
    'inflection>=0.3.1',
    'Jinja2>=2.10',
    'diskcache>=3.1.0',
    'appdirs>=1.4.3'
]

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest', ]

setup(
    author="Michael Droettboom",
    author_email='mdroettboom@mozilla.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
    description="Parser tools for Mozilla's Glean telemetry",
    entry_points={
        'console_scripts': [
            'glean_parser=glean_parser.__main__:main',
        ],
    },
    install_requires=requirements,
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='glean_parser',
    name='glean_parser',
    packages=find_packages(include=['glean_parser']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/mozilla/glean_parser',
    version='0.27.0',
    zip_safe=False,
)
