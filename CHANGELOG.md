# Changelog

## Unreleased

- BREAKING CHANGE: Dropped support for Python 3.8 ([#800](https://github.com/mozilla/glean_parser/pull/800))

## 17.3.0

- New lint: `HIGHER_DATA_SENSITIVITY_REQUIRED` for when an event extra key could potentially contain sensitive data ([bug 1973017](https://bugzilla.mozilla.org/show_bug.cgi?id=1973017))
- BUGFIX: Don't try to remove non-existent key on dual labeled metrics ([#801](https://github.com/mozilla/glean_parser/pull/801))

## 17.2.0

- Forbid redefinition of metrics, categories, or pings within the same YAML document ([bug 1921089](https://bugzilla.mozilla.org/show_bug.cgi?id=1921089))
- Increase the maximum label length to 111 ([#796](https://github.com/mozilla/glean_parser/pull/796))
- Switch to pyproject.toml and uv ([#783](https://github.com/mozilla/glean_parser/pull/783))
- Add new metric type: `DualLabeledCounter` ([#797](https://github.com/mozilla/glean_parser/pull/797))

## 17.1.0

- Permit object metrics named 'glean.attribution.ext' or 'glean.distribution.ext' even if allow_reserved is false ([bug 1955428](https://bugzilla.mozilla.org/show_bug.cgi?id=1955428))

## 17.0.1

- BUGFIX: Fix missing `ping_arg` "`uploader_capabilities`" in util.py ([#786](https://github.com/mozilla/glean_parser/pull/786))

## 17.0.0

- BREAKING CHANGE: Support `uploader_capabilities` for pings ([bug 1920732](https://bugzilla.mozilla.org/show_bug.cgi?id=1920732))

## 16.2.0

- New lint: error when there are metrics whose names are too similar ([bug 1934099](https://bugzilla.mozilla.org/show_bug.cgi?id=1934099))
- Require `array` or `object` as the root type in object metrics ([#780](https://github.com/mozilla/glean_parser/pull/780))
- Remove 100-bucket limit for `custom_distribution` metrics ([bug 1940967](https://bugzilla.mozilla.org/show_bug.cgi?id=1940967))

## 16.1.0

- Allow specifying a subset of interesting metrics to actually collect. Other metrics will be built, but marked as disabled ([bug 1931277](https://bugzilla.mozilla.org/show_bug.cgi?id=1911165)).

## 16.0.0

- BREAKING CHANGE: Support `follows_collection_enabled` for pings ([#776](https://github.com/mozilla/glean_parser/pull/776))
- Add rust_server feature to glean_parser to allow Rust server-side metrics ([#772](https://github.com/mozilla/glean_parser/pull/772))
- Replace `panic`s with returned errors (`go_server`) ([#777](https://github.com/mozilla/glean_parser/pull/777))
- Enable configurable Writer for log output (`go_server`) ([#775](https://github.com/mozilla/glean_parser/pull/775))

## 15.2.1

- Allow earlier versions of platformdirs ([#769](https://github.com/mozilla/glean_parser/pull/769))

## 15.2.0

- New Metric Type: `labeled_quantity` ([bug 1925346](https://bugzilla.mozilla.org/show_bug.cgi?id=1925346))

## 15.1.0

- Bugfix: Remove unused keyword argument from exception ([#755](https://github.com/mozilla/glean_parser/pull/755))
- Add Go log outputter support for custom pings (`go_server`) ([#758](https://github.com/mozilla/glean_parser/pull/758))

## 15.0.1

- Rust codegen: use correctly named parameter for events without extras ([#750](https://github.com/mozilla/glean_parser/pull/750))

## 15.0.0

- **Breaking change:** Updating Kotlin template import statement as part of removing `service-glean` from Android Components. ([bug 1906941](https://bugzilla.mozilla.org/show_bug.cgi?id=1906941))
- **Breaking change:** Do not generate Geckoview Streaming helper code ([#743](https://github.com/mozilla/glean_parser/pull/743))

## 14.5.2

- Revert updating Kotlin template import statement as part of removing `service-glean` from Android Components.
  This change was BREAKING. It will be reintroduced in a major release afterwards ([#744](https://github.com/mozilla/glean_parser/pull/744))

## 14.5.1

- BUGFIX: Rust object metrics: Accept `null` in place of empty arrays

## 14.5.0

- BUGFIX: Fix Rust codegen to properly handle events with multiple types of extras ([bug 1911165](https://bugzilla.mozilla.org/show_bug.cgi?id=1911165))
- Updating Kotlin template import statement as part of removing `service-glean` from Android Components. ([bug 1906941](https://bugzilla.mozilla.org/show_bug.cgi?id=1906941))

## 14.4.0

- Fix JS and Ruby server templates to correctly send event extra values as strings ([DENG-4405](https://mozilla-hub.atlassian.net/browse/DENG-4405))
- ENHANCEMENT: Extra keys in `extra_keys:` fields may now contain any printable ASCII characters ([bug 1910976](https://bugzilla.mozilla.org/show_bug.cgi?id=1910976))

## 14.3.0

- Add the `module_spec` option to the javascript_server outputter ([#726](https://github.com/mozilla/glean_parser/pull/726))
- BUGFIX: Fix the Rust codegen for changes to how `labeled_*` metrics are constructed ([bug 1909244](https://bugzilla.mozilla.org/show_bug.cgi?id=1909244))
- Generate a serializer for array wrappers ([bug 1908157](https://bugzilla.mozilla.org/show_bug.cgi?id=1908157))

## 14.2.0

- New Metric Types: `labeled_{custom|memory|timing}_distribution` ([bug 1657947](https://bugzilla.mozilla.org/show_bug.cgi?id=1657947))

## 14.1.3

- Fix Kotlin/Swift code generation for object metrics, now generating top-level typealiases where needed ([#722](https://github.com/mozilla/glean_parser/pull/722))

## 14.1.2

- ping schedule: Gracefully handle missing ping ([#705](https://github.com/mozilla/glean_parser/pull/705))

## 14.1.1

- Replace deprecated methods and package ([#699](https://github.com/mozilla/glean_parser/pull/699))

## 14.1.0

- Add Go log outputter support for datetime (`go_server`) ([#693](https://github.com/mozilla/glean_parser/pull/693))

## 14.0.1

- BUGFIX: Fix missing `ping_arg` in util.py ([#687](https://github.com/mozilla/glean_parser/pull/687))

## 14.0.0

- BREAKING CHANGE: Expose the optional `enabled` property on pings, defaulting to `enabled: true` ([#681](https://github.com/mozilla/glean_parser/pull/681))
- BREAKING CHANGE: Support metadata field `ping_schedule` for pings ([bug 1804711](https://bugzilla.mozilla.org/show_bug.cgi?id=1804711))
- Add support for event metric type in server JavaScript outputter ([DENG-2407](https://mozilla-hub.atlassian.net/browse/DENG-2407))
- Add Swift and Kotlin codegen support for the object metric type object ([#685](https://github.com/mozilla/glean_parser/pull/685))

## 13.0.1

- Use faster C yaml parser if available ([#677](https://github.com/mozilla/glean_parser/pull/677))

## 13.0.0

- BREAKING CHANGE: Support metadata field `include_info_sections` ([bug 1866559](https://bugzilla.mozilla.org/show_bug.cgi?id=1866559))

## 12.0.1

- Fix Rust codegen for object metric type ([#662](https://github.com/mozilla/glean_parser/pull/662))

## 12.0.0

- Add new metric type object (only Rust codegen support right now) ([#587](https://github.com/mozilla/glean_parser/pull/587))

## 11.1.0

- Add Go log outputter (`go_server`) ([#645](https://github.com/mozilla/glean_parser/pull/645))
- Add Python log outputter (`python_server`) ([MPP-3642](https://mozilla-hub.atlassian.net/browse/MPP-3642))

## 11.0.1

- Fix javascript_server template to include non-event metric parameters in #record call for event metrics ([#643](https://github.com/mozilla/glean_parser/pull/643))
- events: Increase extra key limit to 50 ([Bug 1869429](https://bugzilla.mozilla.org/show_bug.cgi?id=1869429))

## 11.0.0

- Add updated logging logic for Ruby Server ([#642](https://github.com/mozilla/glean_parser/pull/642))
- Add support for event metric type in server-side JavaScript outputter ([DENG-1736](https://mozilla-hub.atlassian.net/browse/DENG-1736))
- BREAKING CHANGE: Dropped support for Python 3.7 ([#638](https://github.com/mozilla/glean_parser/pull/638))
- Add official support for Python 3.11+ ([#638](https://github.com/mozilla/glean_parser/pull/638))

## 10.0.3

- Warn about empty or TODO-tagged data reviews in the list ([#634](https://github.com/mozilla/glean_parser/pull/634))
- Allow `unit` field on all metrics, but warn for all but quantity and custom distribution ([#636](https://github.com/mozilla/glean_parser/pull/636))

## 10.0.2

- Allow `unit` field for string again, but warn about it in the linter ([#634](https://github.com/mozilla/glean_parser/pull/634))

## 10.0.1

- Allow `unit` field for custom distribution again ([#633](https://github.com/mozilla/glean_parser/pull/633))

## 10.0.0

- Add Ruby log outputter (`ruby_server`) ([#620](https://github.com/mozilla/glean_parser/pull/620))
- BREAKING CHANE: `ping` lifetime metrics on the events ping are now disallowed ([#625](https://github.com/mozilla/glean_parser/pull/625))
- Disallow `unit` field for anything but quantity ([#630](https://github.com/mozilla/glean_parser/pull/630)).
  Note that this was already considered the case, now the code enforces it.

## 9.0.0

- BREAKING CHANGE: Dropped support for Python 3.6 ([#615](https://github.com/mozilla/glean_parser/issues/615))
- Allow metadata to configure precise timestamps in pings ([#592](https://github.com/mozilla/glean_parser/pull/592))

## 8.1.1

- Small updates to the `javascript_server` tempalte to address lint warnings ([#598](https://github.com/mozilla/glean_parser/pull/598))

## 8.1.0

- Increased the maximum metric name length in version 2.0.0 schema ([#596](https://github.com/mozilla/glean_parser/pull/596))

## 8.0.0

- BREAKING CHANGE: Remove exposed `lint_yaml_files` function ([#580](https://github.com/mozilla/glean_parser/pull/580))
- Rust: Removed `__glean_metric_maps` from the Rust Jinja template. This functionality is better placed downstream ([Bug 1816526](https://bugzilla.mozilla.org/show_bug.cgi?id=1816526))
- New lint: check that all referenced pings are known ([#584](https://github.com/mozilla/glean_parser/pull/584))
- Add experimental server-side JavaScript outputter ([FXA-7922](https://mozilla-hub.atlassian.net/browse/FXA-7922))

## 7.2.1

- Unbreak last minor release ([#579](https://github.com/mozilla/glean_parser/pull/579))

## 7.2.0

- Remove yamllint integration ([#578](https://github.com/mozilla/glean_parser/pull/578))

## 7.1.0

- ENHANCEMENT: Labels in `labels:` fields may now contain any printable ASCII characters ([bug 1672273](https://bugzilla.mozilla.org/show_bug.cgi?id=1672273))
- BUGFIX: Enforce ordering of generation of Pings, Metrics and Tags such that order is deterministic ([bug 1820334](https://bugzilla.mozilla.org/show_bug.cgi?id=1820334))

## 7.0.0

- BUGFIX: Remove internal-only fields from serialized metrics data ([#550](https://github.com/mozilla/glean_parser/pull/550))
- FEATURE: New subcommand: `dump` to dump the metrics data as JSON ([#550](https://github.com/mozilla/glean_parser/pull/550))
- BUGFIX: Kotlin: Generate enums with the right generic bound for ping reason codes ([#551](https://github.com/mozilla/glean_parser/pull/551)).
- **BREAKING CHANGE:** Fully remove support for the old events API ([#549](https://github.com/mozilla/glean_parser/pull/549))
  Adds a new lint `OLD_EVENT_API` to warn about missing `type` attributes on event extra keys.
  Note that the Glean SDK already dropped support for the old events API.

## 6.4.0

- BUGFIX: Correct code generation for labeled metrics in Rust ([#533](https://github.com/mozilla/glean_parser/pull/533))
- BUGFIX: Correctly serialize `Rates` for Rust code ([#530](https://github.com/mozilla/glean_parser/pull/530))
- Feature: Wrap labeled metric's static labels list as CoW strings (requires updated Glean support) ([#534](https://github.com/mozilla/glean_parser/pull/534))

## 6.3.0

- events: Increase extras limit to 15 ([bug 1798713](https://bugzilla.mozilla.org/show_bug.cgi?id=1798713))

## 6.2.1

- Add support for Rate, Denominator and Numerator metrics for JavaScript. ([bug 1793777](https://bugzilla.mozilla.org/show_bug.cgi?id=1793777))

## 6.2.0

- [data-review] Use a template to generate the Data Review Request template ([bug 1772605](https://bugzilla.mozilla.org/show_bug.cgi?id=1772605))
- Make tag and no\_lint order deterministic ([#518](https://github.com/mozilla/glean_parser/pull/518))

## 6.1.2

- Swift: Add a conditional `import Foundation` to support generating metrics when Glean is delivered via the AppServices iOS megazord

## 6.1.1

- Rust: Use correct name for a ping in generated code.

## 6.1.0

- [data-review] Include extra keys' names and descriptions in data review template ([bug 1767027](https://bugzilla.mozilla.org/show_bug.cgi?id=1767027))
- Raise limit on number of statically-defined labels to 4096. ([bug 1772163](https://bugzilla.mozilla.org/show_bug.cgi?id=1772163))
- Fix Rust code generation for new UniFFI interface ([#491](https://github.com/mozilla/glean_parser/pull/491), [#494](https://github.com/mozilla/glean_parser/pull/494), [#495](https://github.com/mozilla/glean_parser/pull/495))

## 6.0.1

- Relax version requirement for MarkupSafe.
  Now works with MarkupSafe v1.1.1 to v2.0.1 inclusive again.

## 6.0.0

- BUGFIX: Add missing `extra_args` to Rust constructor generation ([bug 1765855](https://bugzilla.mozilla.org/show_bug.cgi?id=1765855))
- **Breaking change:** `glean_parser` now generates metrics compatible with the UniFFI-powered Glean SDK.
  This is not backwards-compatible with previous versions.
- Generate Rate, Denominator and Numerator metrics for Kotlin and Swift
- Explicitly skip Rate, Denominator and Numerator metrics for JavaScript.
  These will cause a build failure by default, but can be turned into warnings on request.
  Use `-s fail_rates=false` to enable warning-only mode.

## 5.1.2

- BUGFIX: Revert changes made on v5.1.1.
    - The issues addressed by those changes, were non-issues and result of misuse of the APIs.

## 5.1.1

- BUGFIX: Fix issues with Swift templates ([bug 1749494](https://bugzilla.mozilla.org/show_bug.cgi?id=1749494))
    - Make metrics and pings all `public`
    - Make pings `static`

## 5.1.0

- Add support for build info generation for JavaScript and Typescript targets ([bug 1749494](https://bugzilla.mozilla.org/show_bug.cgi?id=1749494))

## 5.0.1

- Fix the logic for the metric expiration by version ([bug 1753194](https://bugzilla.mozilla.org/show_bug.cgi?id=1753194))

## 5.0.0

- Remove C# support ([#436](https://github.com/mozilla/glean_parser/pull/436)).
- Add support for Rust code generation ([bug 1677434](https://bugzilla.mozilla.org/show_bug.cgi?id=1677434))
- Report an error if no files are passed ([bug 1751730](https://bugzilla.mozilla.org/show_bug.cgi?id=1751730))
- [data-review] Report an error if no metrics match provided bug number ([bug 1752576](https://bugzilla.mozilla.org/show_bug.cgi?id=1752576))
- [data-review] Include notification_emails in list of those responsible ([bug 1752576](https://bugzilla.mozilla.org/show_bug.cgi?id=1752576))
- Add support for expiring metrics by the provided major version ([bug 1753194](https://bugzilla.mozilla.org/show_bug.cgi?id=1753194))

## 4.4.0

- Support global file-level tags in metrics.yaml ([bug 1745283](https://bugzilla.mozilla.org/show_bug.cgi?id=1745283))
- Glinter: Reject metric files if they use `unit` by mistake. It should be `time_unit` ([#432](https://github.com/mozilla/glean_parser/pull/432)).
- Automatically generate a build date when generating build info ([#431](https://github.com/mozilla/glean_parser/pull/431)).
  Enabled for Kotlin and Swift.
  This can be changed with the `build_date` command line option.
  `build_date=0` will use a static unix epoch time.
  `build_date=2022-01-03T17:30:00` will parse the ISO8601 string to use (as a UTC timestamp).
  Other values will throw an error.

  Example:

    glean_parser translate --format kotlin --option build_date=2021-11-01T01:00:00 path/to/metrics.yaml

## 4.3.1

- BUGFIX: Skip tags for code generation ([#409](https://github.com/mozilla/glean_parser/pull/409))

## 4.3.0

- Support tags in glean parser ([bug 1734011](https://bugzilla.mozilla.org/show_bug.cgi?id=1734011))

## 4.2.0

- Improve the schema validation error messages. They will no longer include `OrderedDict(...)` on Python 3.7 and later ([bug 1733395](https://bugzilla.mozilla.org/show_bug.cgi?id=1733395))
- Officially support Python 3.10

## 4.1.1 (2021-09-28)

- Update private import paths on Javascript / Typescript templates. ([bug 1702468](https://bugzilla.mozilla.org/show_bug.cgi?id=1702468))

## 4.1.0 (2021-09-16)

- Add support for Node.js platform on Javascript / Typescript templates. ([bug 1728982](https://bugzilla.mozilla.org/show_bug.cgi?id=1728982))

## 4.0.0 (2021-08-20)

- Add support for Text metric type ([#374](https://github.com/mozilla/glean_parser/pull/374))
- Reserve the `default` ping name. It can't be used as a ping name, but it can be used in `send_in_pings` ([#376](https://github.com/mozilla/glean_parser/pull/376))

## 3.8.0 (2021-08-18)

- Expose ping reasons enum on JavaScript / TypeScript templates. ([bug 1719136](https://bugzilla.mozilla.org/show_bug.cgi?id=1719136))
- Define an interface with the allowed extras for each event on the TypeScript template. ([bug 1693487](https://bugzilla.mozilla.org/show_bug.cgi?id=1693487))

## 3.7.0 (2021-07-13)

- New lint: Check for redundant words in ping names ([#355](https://github.com/mozilla/glean_parser/pull/355))
- Add support for URL metric type ([#361](https://github.com/mozilla/glean_parser/pull/361))

## 3.6.0 (2021-06-11)

- Add a command `data-review` to generate a skeleton Data Review Request for all metrics matching a supplied bug number. ([bug 1704541](https://bugzilla.mozilla.org/show_bug.cgi?id=1704541))
- Enable custom distribution outside of GeckoView (`gecko_datapoint` becomes optional)

## 3.5.0 (2021-06-03)

- Transform generated folder into QML Module when building Javascript templates for the Qt platform. ([bug 1707896](https://bugzilla.mozilla.org/show_bug.cgi?id=1707896)
    - Import the Glean QML module from inside each generated file, removing the requirement to import Glean before importing any of the generated files;
    - Prodive a `qmldir` file exposing all generated files;
    - Drop the `namespace` option for Javascript templates;
    - Add a new `version` option for Javascript templates, required when building for Qt, which expected the Glean QML module version.

## 3.4.0 (2021-05-28)

- Add missing import for Kotlin code ([#339](https://github.com/mozilla/glean_parser/pull/339))
- Use a plain Kotlin type in the generated interface implementation ([#339](https://github.com/mozilla/glean_parser/pull/339))
- Generate additional generics for event metrics ([#339](https://github.com/mozilla/glean_parser/pull/339))
- For Kotlin skip generating `GleanBuildInfo.kt` when requested (with `with_buildinfo=false`) ([#341](https://github.com/mozilla/glean_parser/pull/341))

## 3.3.2 (2021-05-18)

- Fix another bug in the Swift code generation when generating extra keys ([#334](https://github.com/mozilla/glean_parser/pull/334))

## 3.3.1 (2021-05-18)

- Fix Swift code generation bug for pings ([#333](https://github.com/mozilla/glean_parser/pull/333))

## 3.3.0 (2021-05-18)

- Generate new event API construct ([#321](https://github.com/mozilla/glean_parser/pull/321))

## 3.2.0 (2021-04-28)

- Add option to add extra introductory text to generated markdown ([#298](https://github.com/mozilla/glean_parser/pull/298))
- Add support for Qt in Javascript templates ([bug 1706252](https://bugzilla.mozilla.org/show_bug.cgi?id=1706252))
  - Javascript templates will now accept the `platform` option. If this option is set to `qt`
  the generated templates will be Qt compatible. Default value is `webext`.

## 3.1.2 (2021-04-21)

- BUGFIX: Remove the "DO NOT COMMIT" notice from the documentation.

## 3.1.1 (2021-04-19)

- Recommend to not commit as well as to not edit the generated files. ([bug 1706042](https://bugzilla.mozilla.org/show_bug.cgi?id=1706042))
- BUGFIX: Include import statement for labeled metric subtypes in Javascript and Typescript templates.

## 3.1.0 (2021-04-16)

- Add support for labeled metric types in Javascript and Typescript templates.

## 3.0.0 (2021-04-13)

- Raise limit on number of statically-defined lables to 100. ([bug 1702263](https://bugzilla.mozilla.org/show_bug.cgi?id=1702263))
- BUGFIX: Version 2.0.0 of the schema now allows the "special" `glean_.*` ping names for Glean-internal use again.
- Remove support for JWE metric types.

## 2.5.0 (2021-02-23)

- Add parser and object model support for `rate` metric type. ([bug 1645166](https://bugzilla.mozilla.org/show_bug.cgi?id=1645166))
- Add parser and object model support for telemetry_mirror property. ([bug 1685406](https://bugzilla.mozilla.org/show_bug.cgi?id=1685406))
- Update the Javascript template to match Glean.js expectations. ([bug 1693516](https://bugzilla.mozilla.org/show_bug.cgi?id=1693516))
  - Glean.js has updated it's export strategy. It will now export each metric type as an independent module;
  - Glean.js has dropped support for non ES6 modules.
- Add support for generating Typescript code. ([bug 1692157](https://bugzilla.mozilla.org/show_bug.cgi?id=1692157))
  - The templates added generate metrics and pings code for Glean.js.

## 2.4.0 (2021-02-18)

- **Experimental:** `glean_parser` has a new subcommand `coverage` to convert raw coverage reports
  into something consumable by coverage tools, such as codecov.io
- The path to the file that each metric is defined in is now stored on the
  `Metric` object in `defined_in["filepath"]`.

## 2.3.0 (2021-02-17)

- Leverage the `glean_namespace` to provide correct import when building for Javascript.

## 2.2.0 (2021-02-11)

- The Kotlin generator now generates static build information that can be passed
  into `Glean.initialize` to avoid calling the package manager at runtime.

## 2.1.0 (2021-02-10)

- Add support for generating Javascript code.
  - The templates added generate metrics and pings code for Glean.js.

## 2.0.0 (2021-02-05)

- New versions 2.0.0 of the `metrics.yaml` and `pings.yaml` schemas now ship
  with `glean_parser`. These schemas are different from version 1.0.0 in the
  following ways:

  - Bugs must be specified as URLs. Bug numbers are disallowed.
  - The legacy ping names containing underscores are no longer allowed. These
    included `deletion_request`, `bookmarks_sync`, `history_sync`,
    `session_end`, `all_pings`, `glean_*`). In these cases, the `_` should be
    replaced with `-`.

  To upgrade your app or library to use the new schema, replace the version in
  the `$schema` value with `2-0-0`.

- **Breaking change:** It is now an error to use bug numbers (rather than URLs)
  in ping definitions.

- Add the line number that metrics and pings were originally defined in the yaml
  files.

## 1.29.1 (2020-12-17)

- BUGFIX: Linter output can now be redirected correctly (1675771).

## 1.29.0 (2020-10-07)

- **Breaking change:** `glean_parser` will now return an error code when any of
  the input files do not exist (unless the `--allow-missing-files` flag is
  passed).
- Generated code now includes a comment next to each metric containing the name
  of the metric in its original `snake_case` form.
- When metrics don't provide a `unit` parameter, it is not included in the
  output (as provided by probe-scraper).

## 1.28.6 (2020-09-24)

- BUGFIX: Ensure Kotlin arguments are deterministically ordered

## 1.28.5 (2020-09-14)

- Fix deploy step to update pip before deploying to pypi.

## 1.28.4 (2020-09-14)

- The `SUPERFLUOUS_NO_LINT` warning has been removed from the glinter.
  It likely did more harm than good, and makes it hard to make
  `metrics.yaml` files that pass across different versions of
  `glean_parser`.
- Expired metrics will now produce a linter warning, `EXPIRED_METRIC`.
- Expiry dates that are more than 730 days (\~2 years) in the future
  will produce a linter warning, `EXPIRATION_DATE_TOO_FAR`.
- Allow using the Quantity metric type outside of Gecko.
- New parser configs `custom_is_expired` and `custom_validate_expires`
  added. These are both functions that take the `expires` value of the
  metric and return a bool. (See `Metric.is_expired` and
  `Metric.validate_expires`). These will allow FOG to provide custom
  validation for its version-based `expires` values.

## 1.28.3 (2020-07-28)

- BUGFIX: Support HashSet and Dictionary in the C\## generated code.

## 1.28.2 (2020-07-28)

- BUGFIX: Generate valid C\## code when using Labeled metric types.

## 1.28.1 (2020-07-24)

- BUGFIX: Add missing column to correctly render markdown tables in generated
  documentation.

## 1.28.0 (2020-07-23)

- **Breaking change:** The internal ping `deletion-request` was misnamed in
  pings.py causing the linter to not allow use of the correctly named ping for
  adding legacy ids to. Consuming apps will need to update their metrics.yaml if
  they are using `deletion_request` in any `send_in_pings` to `deletion-request`
  after updating.

## 1.27.0 (2020-07-21)

- Rename the `data_category` field to `data_sensitivity` to be clearer.

## 1.26.0 (2020-07-21)

- Add support for JWE metric types.
- Add a `data_sensitivity` field to all metrics for specifying the type of data
  collected in the field.

## 1.25.0 (2020-07-17)

- Add support for generating C\## code.
- BUGFIX: The memory unit is now correctly passed to the MemoryDistribution
  metric type in Swift.

## 1.24.0 (2020-06-30)

- BUGFIX: look for metrics in send\_if\_empty pings. Metrics for these kinds of
  pings were being ignored.

## 1.23.0 (2020-06-27)

- Support for Python 3.5 has been dropped.
- BUGFIX: The ordering of event extra keys will now match with their enum,
  fixing a serious bug where keys of extras may not match the correct values in
  the data payload. See <https://bugzilla.mozilla.org/show_bug.cgi?id=1648768>.

## 1.22.0 (2020-05-28)

- **Breaking change:** (Swift only) Combine all metrics and pings into a single
  generated file `Metrics.swift`.

## 1.21.0 (2020-05-25)

- `glinter` messages have been improved with more details and to be more
  actionable.
- A maximum of 10 `extra_keys` is now enforced for `event` metric types.
- BUGFIX: the `Lifetime` enum values now match the values of the implementation
  in mozilla/glean.

## 1.20.4 (2020-05-07)

- BUGFIX: yamllint errors are now reported using the correct file name.

## 1.20.3 (2020-05-06)

- Support for using `timing_distribution`'s `time_unit` parameter to control
  the range of acceptable values is documented. The default unit for this use
  case is `nanosecond` to avoid creating a breaking change. See [bug
  1630997](https://bugzilla.mozilla.org/show_bug.cgi?id=1630997) for more
  information.

## 1.20.2 (2020-04-24)

- Dependencies that depend on the version of Python being used are now specified
  using the [Declaring platform specific dependencies syntax in
  setuptools](https://setuptools.readthedocs.io/en/latest/setuptools.html##declaring-platform-specific-dependencies).
  This means that more recent versions of dependencies are likely to be
  installed on Python 3.6 and later, and unnecessary backport libraries won't
  be installed on more recent Python versions.

## 1.20.1 (2020-04-21)

- The minimum version of the runtime dependencies has been lowered to increase
  compatibility with other tools. These minimum versions are now tested in CI,
  in addition to testing the latest versions of the dependencies that was
  already happening in CI.

## 1.20.0 (2020-04-15)

- **Breaking change:** glinter errors found during the `translate` command will
  now return an error code. glinter warnings will be displayed, but not return
  an error code.
- `glean_parser` now produces a linter warning when `user` lifetime metrics are
  set to expire. See [bug
  1604854](https://bugzilla.mozilla.org/show_bug.cgi?id=1604854) for additional
  context.

## 1.19.0 (2020-03-18)

- **Breaking change:** The regular expression used to validate labels is
  stricter and more correct.
- Add more information about pings to markdown documentation:
  - State whether the ping includes client id;
  - Add list of data review links;
  - Add list of related bugs links.
- `glean_parser` now makes it easier to write external translation
  functions for different language targets.
- BUGFIX: `glean_parser` now works on 32-bit Windows.

## 1.18.3 (2020-02-24)

- Dropped the `inflection` dependency.
- Constrained the `zipp` and `MarkupSafe` transitive dependencies to versions
  that support Python 3.5.

## 1.18.2 (2020-02-14)

- BUGFIX: Fix rendering of first element of reason list.

## 1.18.1 (2020-02-14)

- BUGFIX: Reason codes are displayed in markdown output for built-in
  pings as well.
- BUGFIX: Reason descriptions are indented correctly in markdown
  output.
- BUGFIX: To avoid a compiler error, the `@JvmName` annotation isn't
  added to private members.

## 1.18.0 (2020-02-13)

- **Breaking Change (Java API)** Have the metrics names in Java match the names
  in Kotlin. See [Bug
  1588060](https://bugzilla.mozilla.org/show_bug.cgi?id=1588060).
- The reasons a ping are sent are now included in the generated markdown
  documentation.

## 1.17.3 (2020-02-05)

- BUGFIX: The version of Jinja2 now specifies < 3.0, since that version no
  longer supports Python 3.5.

## 1.17.2 (2020-02-05)

- BUGFIX: Fixes an import error in generated Kotlin code.

## 1.17.1 (2020-02-05)

- BUGFIX: Generated Swift code now includes `import Glean`, unless generating
  for a Glean-internal build.

## 1.17.0 (2020-02-03)

- Remove default schema URL from `validate_ping`
- Make `schema` argument required for CLI
- BUGFIX: Avoid default import in Swift code for Glean itself
- BUGFIX: Restore order of fields in generated Swift code

## 1.16.0 (2020-01-15)

- Support for `reason` codes on pings was added.

## 1.15.6 (2020-02-06)

- BUGFIX: The version of Jinja2 now specifies < 3.0, since that version no
  longer supports Python 3.5 (backported from 1.17.3).

## 1.15.5 (2019-12-19)

- BUGFIX: Also allow the legacy name `all_pings` for `send_in_pings` parameter
  on metrics

## 1.15.4 (2019-12-19)

- BUGFIX: Also allow the legacy name `all_pings`

## 1.15.3 (2019-12-13)

- Add project title to markdown template.
- Remove "Sorry about that" from markdown template.
- BUGFIX: Replace dashes in variable names to force proper naming

## 1.15.2 (2019-12-12)

- BUGFIX: Use a pure Python library for iso8601 so there is no compilation
  required.

## 1.15.1 (2019-12-12)

- BUGFIX: Add some additional ping names to the non-kebab-case allow list.

## 1.15.0 (2019-12-12)

- Restrict new pings names to be kebab-case and change `all_pings` to
  `all-pings`

## 1.14.0 (2019-12-06)

- `glean_parser` now supports Python versions 3.5, 3.6, 3.7 and 3.8.

## 1.13.0 (2019-12-04)

- The `translate` command will no longer clear extra files in the output
  directory.
- BUGFIX: Ensure all newlines in comments are prefixed with comment markers
- BUGFIX: Escape Swift keywords in variable names in generated code
- Generate documentation for pings that are sent if empty

## 1.12.0 (2019-11-27)

- Reserve the `deletion_request` ping name
- Added a new flag `send_if_empty` for pings

## 1.11.0 (2019-11-13)

- The `glinter` command now performs `yamllint` validation on registry files.

## 1.10.0 (2019-11-11)

- The Kotlin linter `detekt` is now run during CI, and for local
  testing if installed.
- Python 3.8 is now tested in CI (in addition to Python 3.7). Using
  `tox` for this doesn't work in modern versions of CircleCI, so the
  `tox` configuration has been removed.
- `yamllint` has been added to test the YAML files on CI.
- ⚠ Metric types that don't yet have implementations in glean-core
  have been removed. This includes `enumeration`, `rate`, `usage`, and
  `use_counter`, as well as many labeled metrics that don't exist.

## 1.9.5 (2019-10-22)

- Allow a Swift lint for generated code
- New lint: Restrict what metric can go into the `baseline` ping
- New lint: Warn for slight misspellings in ping names
- BUGFIX: change Labeled types labels from lists to sets.

## 1.9.4 (2019-10-16)

- Use lists instead of sets in Labeled types labels to ensure that the order of
  the labels passed to the `metrics.yaml` is kept.
- `glinter` will now check for duplicate labels and error if there are any.

## 1.9.3 (2019-10-09)

- Add labels from Labeled types to the Extra column in the Markdown template.

## 1.9.2 (2019-10-08)

- BUGFIX: Don't call `is_internal_metric` on `Ping` objects.

## 1.9.1 (2019-10-07)

- Don't include Glean internal metrics in the generated markdown.

## 1.9.0 (2019-10-04)

- Glinter now warns when bug numbers (rather than URLs) are used.
- BUGFIX: add `HistogramType` and `MemoryUnit` imports in Kotlin generated code.

## 1.8.4 (2019-10-02)

- Removed unsupported labeled metric types.

## 1.8.3 (2019-10-02)

- Fix indentation for generated Swift code

## 1.8.2 (2019-10-01)

- Created labeled metrics and events in Swift code and wrap it in a
  configured namespace

## 1.8.1 (2019-09-27)

- BUGFIX: `memory_unit` is now passed to the Kotlin generator.

## 1.8.0 (2019-09-26)

- A new parser config, `do_not_disable_expired`, was added to turn off the
  feature that expired metrics are automatically disabled. This is useful if you
  want to retain the disabled value that is explicitly in the `metrics.yaml`
  file.
- `glinter` will now report about superfluous `no_lint` entries.

## 1.7.0 (2019-09-24)

- A `glinter` tool is now included to find common mistakes in metric naming
  and setup. This check is run during `translate` and warnings will be
  displayed. ⚠ These warnings will be treated as errors in a future revision.

## 1.6.1 (2019-09-17)

- BUGFIX: `GleanGeckoMetricsMapping` must include `LabeledMetricType`
  and `CounterMetricType`.

## 1.6.0 (2019-09-17)

- NEW: Support for outputting metrics in Swift.
- BUGFIX: Provides a helpful error message when `geckoview_datapoint` is used on
  an metric type that doesn't support GeckoView exfiltration.
- Generate a lookup table for Gecko categorical histograms in
  `GleanGeckoMetricsMapping`.
- Introduce a 'Swift' output generator.

## 1.4.1 (2019-08-28)

- Documentation only.

## 1.4.0 (2019-08-27)

- Added support for generating markdown documentation from `metrics.yaml` files.

## 1.3.0 (2019-08-22)

- `quantity` metric type has been added.

## 1.2.1 (2019-08-13)

- BUGFIX: `includeClientId` was not being output for PingType.

## 1.2.0 (2019-08-13)

- `memory_distribution` metric type has been added.
- `custom_distribution` metric type has been added.
- `labeled_timespan` is no longer an allowed metric type.

## 1.1.0 (2019-08-05)

-   Add a special `all_pings` value to `send_in_pings`.

## 1.0.0 (2019-07-29)

- First release to start following strict semver.

## 0.1.0 (2018-10-15)

- First release on PyPI.
