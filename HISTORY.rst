=======
History
=======

Unreleased
----------

1.8.3 (2019-10-02)
------------------

* Fix indentation for generated Swift code

1.8.2 (2019-10-01)
------------------

* Created labeled metrics and events in Swift code and wrap it in a configured namespace

1.8.1 (2019-09-27)
------------------

* BUGFIX: `memory_unit` is now passed to the Kotlin generator.

1.8.0 (2019-09-26)
------------------

* A new parser config, `do_not_disable_expired`, was added to turn off the
  feature that expired metrics are automatically disabled. This is useful if you
  want to retain the disabled value that is explicitly in the `metrics.yaml`
  file.

* `glinter` will now report about superfluous `no_lint` entries.

1.7.0 (2019-09-24)
------------------

* A "`glinter`" tool is now included to find common mistakes in metric naming and setup.
  This check is run during `translate` and warnings will be displayed.
  ⚠ These warnings will be treated as errors in a future revision.

1.6.1 (2019-09-17)
------------------

* BUGFIX: `GleanGeckoMetricsMapping` must include `LabeledMetricType` and `CounterMetricType`.

1.6.0 (2019-09-17)
------------------

* NEW: Support for outputting metrics in Swift.

* BUGFIX: Provides a helpful error message when `geckoview_datapoint` is used on an metric type that doesn't support GeckoView exfiltration.

* Generate a lookup table for Gecko categorical histograms in `GleanGeckoMetricsMapping`.

* Introduce a 'Swift' output generator.

1.4.1 (2019-08-28)
------------------

* Documentation only.

1.4.0 (2019-08-27)
------------------

* Added support for generating markdown documentation from `metrics.yaml` files.

1.3.0 (2019-08-22)
------------------

* `quantity` metric type has been added.

1.2.1 (2019-08-13)
------------------

* BUGFIX: `includeClientId` was not being output for PingType.

1.2.0 (2019-08-13)
------------------

* `memory_distribution` metric type has been added.

* `custom_distribution` metric type has been added.

* `labeled_timespan` is no longer an allowed metric type.

1.1.0 (2019-08-05)
------------------

* Add a special `all_pings` value to `send_in_pings`.

1.0.0 (2019-07-29)
------------------

* First release to start following strict semver.

0.1.0 (2018-10-15)
------------------

* First release on PyPI.
