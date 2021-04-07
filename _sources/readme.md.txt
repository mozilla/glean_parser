# Glean Parser

Parser tools for Mozilla's Glean telemetry.

## Features

Contains various utilities for handling `metrics.yaml` and `pings.yaml` for [the
Glean SDK](https://mozilla.github.io/glean). This includes producing generated
code for various integrations, linting and coverage testing.

## Documentation

- [User documentation for Glean](https://mozilla.github.io/glean/).
- [`glean_parser` developer documentation](https://mozilla.github.io/glean_parser/).

## Requirements

-   Python 3.6 (or later)

The following library requirements are installed automatically when
`glean_parser` is installed by `pip`.

-   appdirs
-   Click
-   diskcache
-   Jinja2
-   jsonschema
-   PyYAML

Additionally on Python 3.6:

-   iso8601

## Usage

```sh
$ glean_parser --help
```

Read in `metrics.yaml`, translate to Kotlin format, and
output to `output_dir`:

```sh
$ glean_parser translate -o output_dir -f kotlin metrics.yaml
```

Check a Glean ping against the ping schema:

```sh
$ glean_parser check < ping.json
```
