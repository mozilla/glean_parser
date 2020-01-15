``pings.yaml`` file
=====================

The ``pings.yaml`` file defines what pings your application will collect.

The top-level of the file must contain the following key-value pair to indicate
that it is a Glean ``pings.yaml`` file::

   $schema: moz://mozilla.org/schemas/glean/pings/1-0-0

The other keys at the top level of the file are ping names.
Ping names must be in ``kebab-case``.
Ping names have a maximum of 30 characters.

Ping parameters
-----------------

.. ping_parameter:: description

.. ping_parameter:: include_client_id

.. ping_parameter:: send_if_empty

.. ping_parameter:: notification_emails

.. ping_parameter:: bugs

.. ping_parameter:: data_reviews

.. ping_parameter:: reasons

JSON Schema
-----------

There is a formal schema for validating ``pings.yaml`` files, included in its
entirety below:

.. literalinclude:: ../glean_parser/schemas/pings.1-0-0.schema.yaml
   :language: yaml
