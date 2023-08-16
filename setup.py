#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""The setup script."""

import sys

from setuptools import setup, find_packages


if sys.version_info < (3, 7):
    print("glean_parser requires at least Python 3.7", file=sys.stderr)
    sys.exit(1)


with open("README.md", encoding="utf-8") as readme_file:
    readme = readme_file.read()

with open("CHANGELOG.md", encoding="utf-8") as history_file:
    history = history_file.read()

requirements = [
    "appdirs>=1.4",
    "Click>=7",
    "diskcache>=4",
    "Jinja2>=2.10.1",
    "jsonschema>=3.0.2",
    "PyYAML>=5.3.1",
]

setup_requirements = [
    "pytest-runner",
    "setuptools-scm>=7",
]

test_requirements = [
    "pytest",
]

setup(
    author="The Glean Team",
    author_email="glean-team@mozilla.com",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    description="Parser tools for Mozilla's Glean telemetry",
    entry_points={
        "console_scripts": [
            "glean_parser=glean_parser.__main__:main_wrapper",
        ],
    },
    install_requires=requirements,
    long_description=readme + "\n\n" + history,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords="glean_parser",
    name="glean_parser",
    packages=find_packages(include=["glean_parser"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/mozilla/glean_parser",
    zip_safe=False,
    use_scm_version=True,
)
