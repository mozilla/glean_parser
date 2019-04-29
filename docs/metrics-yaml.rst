``metrics.yaml`` file
=====================

The ``metrics.yaml`` file defines what metrics and events your application will
collect.

The top-level of the file must contain the following key-value pair to indicate
that it is a Glean ``metrics.yaml`` file::

   $schema: moz://mozilla.org/schemas/glean/metrics/1-0-0

The other keys at the top level of the file are category names. Category names
must be in ``snake_case``, but may also contain ``.`` to indicate *ad hoc*
subcategories. Category names have a maximum of 40 characters.

Within each category, the individual metrics are defined. The key is the name of
the metric (``snake_case`` with a maximum of 30 characters), and each value is
an object with the following parameters described below.

Metric parameters
-----------------

.. metric_parameter:: type

.. metric_parameter:: description

.. metric_parameter:: notification_emails

.. metric_parameter:: bugs

.. metric_parameter:: data_reviews

.. metric_parameter:: lifetime

.. metric_parameter:: send_in_pings

.. metric_parameter:: disabled

.. metric_parameter:: expires

.. metric_parameter:: version

.. metric_parameter:: values

.. metric_parameter:: time_unit

.. metric_parameter:: labels

.. metric_parameter:: denominator

.. metric_parameter:: extra_keys

JSON Schema
-----------

There is a formal schema for validating ``metrics.yaml`` files, included in its
entirety below:

.. literalinclude:: ../glean_parser/schemas/metrics.1-0-0.schema.yaml
   :language: yaml
