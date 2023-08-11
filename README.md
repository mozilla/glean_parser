# Glean Parser

Parser tools for Mozilla's Glean telemetry.

## Features

Contains various utilities for handling `metrics.yaml` and `pings.yaml` for [the
Glean SDKs](https://mozilla.github.io/glean). This includes producing generated
code for various integrations, linting and coverage testing.

## Documentation

- [How to Contribute](https://github.com/mozilla/glean_parser/blob/main/CONTRIBUTING.md). Please file bugs in [bugzilla](https://bugzilla.mozilla.org/enter_bug.cgi?assigned_to=nobody%40mozilla.org&bug_ignored=0&bug_severity=normal&bug_status=NEW&cf_fission_milestone=---&cf_fx_iteration=---&cf_fx_points=---&cf_status_firefox65=---&cf_status_firefox66=---&cf_status_firefox67=---&cf_status_firefox_esr60=---&cf_status_thunderbird_esr60=---&cf_tracking_firefox65=---&cf_tracking_firefox66=---&cf_tracking_firefox67=---&cf_tracking_firefox_esr60=---&cf_tracking_firefox_relnote=---&cf_tracking_thunderbird_esr60=---&product=Data%20Platform%20and%20Tools&component=Glean%3A%20SDK&contenttypemethod=list&contenttypeselection=text%2Fplain&defined_groups=1&flag_type-203=X&flag_type-37=X&flag_type-41=X&flag_type-607=X&flag_type-721=X&flag_type-737=X&flag_type-787=X&flag_type-799=X&flag_type-800=X&flag_type-803=X&flag_type-835=X&flag_type-846=X&flag_type-855=X&flag_type-864=X&flag_type-916=X&flag_type-929=X&flag_type-930=X&flag_type-935=X&flag_type-936=X&flag_type-937=X&form_name=enter_bug&maketemplate=Remember%20values%20as%20bookmarkable%20template&op_sys=Unspecified&priority=P3&&rep_platform=Unspecified&status_whiteboard=%5Btelemetry%3Aglean-rs%3Am%3F%5D&target_milestone=---&version=unspecified).
- [User documentation for Glean](https://mozilla.github.io/glean/).
- [`glean_parser` developer documentation](https://mozilla.github.io/glean_parser/).

## Requirements

-   Python 3.7 (or later)

The following library requirements are installed automatically when
`glean_parser` is installed by `pip`.

-   appdirs
-   Click
-   diskcache
-   Jinja2
-   jsonschema
-   PyYAML

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
