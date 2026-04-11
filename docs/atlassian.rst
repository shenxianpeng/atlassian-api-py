API documentation
=================

This page lists the public clients and lower-level helpers exposed by the
``atlassian`` package.

Most scripts should import one of the product clients from ``atlassian``:

.. code-block:: python

   from atlassian import Jira, Bitbucket, Confluence

Use ``atlassian.client.AtlassianAPI`` directly only when you need to call an
endpoint that does not yet have a convenience method.

atlassian.jira module
---------------------

.. automodule:: atlassian.jira
   :members:
   :undoc-members:
   :show-inheritance:

atlassian.bitbucket module
--------------------------

.. automodule:: atlassian.bitbucket
   :members:
   :undoc-members:
   :show-inheritance:

atlassian.confluence module
---------------------------

.. automodule:: atlassian.confluence
   :members:
   :undoc-members:
   :show-inheritance:

atlassian.client module
-----------------------

.. automodule:: atlassian.client
   :members:
   :undoc-members:
   :show-inheritance:

atlassian.error module
----------------------

.. automodule:: atlassian.error
   :members:
   :undoc-members:
   :show-inheritance:

atlassian.logger module
-----------------------

.. automodule:: atlassian.logger
   :members:
   :undoc-members:
   :show-inheritance:
