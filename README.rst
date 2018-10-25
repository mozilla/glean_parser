============
Glean Parser
============

Parser tools for Mozilla's glean telemetry.

Features
--------

Parses the metrics.yaml files for the glean telemetry SDK and produces output
for various integrations.

Requirements
------------

- Python 3.7 (or later)

The following library requirements are installed automatically when glean_parser
is installed by `pip`.

- Click
- PyYAML
- jsonschema
- inflection
- Jinja2

Usage
-----

.. code-block:: console

  $ glean_parser --help

Read in `metrics.yaml`, translate to kotlin format, and output to `output_dir`:

.. code-block:: console

  $ glean_parser translate -o output_dir -f kotlin metrics.yaml

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
