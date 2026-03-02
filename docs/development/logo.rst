Nano Banana Logo
================

The pytest-libiio project uses a **nano banana** as its mascot.  The name
captures the two core identities of the library: *nano*-scale measurements
(nanoamperes, nanovolts) and the *banana* plug — the connector of choice on
test and measurement benches.  Together they make a friendly symbol for
precise, hardware-level testing.

For full design rationale, colour choices, and dark/light-mode details see
:doc:`/logo-design-notes`.

.. image:: /_static/logo-pytest-libiio-banana.svg
   :alt: pytest-libiio nano banana mascot
   :align: center
   :width: 160px

Static Assets
-------------

The following files are committed under ``docs/_static/`` and are bundled
into the built documentation by Sphinx:

``logo-pytest-libiio-banana.svg``
    Theme-aware SVG master.  A single file used for both the Furo
    ``light_logo`` and ``dark_logo`` options because it embeds
    ``@media (prefers-color-scheme: dark)`` CSS to handle both themes
    internally.

``logo-pytest-libiio-banana.png``
    PNG raster fallback for environments that cannot render SVG (for example,
    some email clients and older documentation renderers).

``custom.css``
    Project-level CSS overrides loaded by Sphinx.  Contains a
    ``.sidebar-brand img`` rule to cap the sidebar logo at 200 px wide.
