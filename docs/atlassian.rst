API documentation
=================

This page lists the public clients and lower-level helpers exposed by the
``atlassian_api`` package.

Most scripts should import one of the product clients from ``atlassian_api``:

.. code-block:: python

   from atlassian_api import Jira, Bitbucket, Confluence

Use ``atlassian_api.client.AtlassianAPI`` directly only when you need to call an
endpoint that does not yet have a convenience method.

atlassian_api.jira module
---------------------

.. automodule:: atlassian_api.jira
   :members:
   :undoc-members:
   :show-inheritance:

atlassian_api.bitbucket module
--------------------------

.. automodule:: atlassian_api.bitbucket
   :members:
   :undoc-members:
   :show-inheritance:

atlassian_api.confluence module
---------------------------

.. automodule:: atlassian_api.confluence
   :members:
   :undoc-members:
   :show-inheritance:

atlassian_api.client module
-----------------------

.. automodule:: atlassian_api.client
   :members:
   :undoc-members:
   :show-inheritance:

atlassian_api.error module
----------------------

.. automodule:: atlassian_api.error
   :members:
   :undoc-members:
   :show-inheritance:

atlassian_api.logger module
-----------------------

.. automodule:: atlassian_api.logger
   :members:
   :undoc-members:
   :show-inheritance:
