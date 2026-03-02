.. _logo:

Logo
====

The pytest-libiio project uses the **nano-banana** as its mascot.  The name
is a nod to the ``nano`` URI scheme used by libiio for USB and serial
device connections, while the banana's curved silhouette echoes the crescent
profile found on many IIO sensor packages.

The logo is a theme-aware SVG: embedded CSS ``@media (prefers-color-scheme:
dark)`` rules adjust the colour palette automatically so the same file looks
good on both light and dark documentation themes.

For full design rationale, colour tokens, and usage guidelines see
:doc:`/logo-design-notes` (Markdown source at ``docs/logo-design-notes.md``).

.. image:: /_static/logo-pytest-libiio-banana.svg
   :alt: pytest-libiio nano-banana mascot
   :width: 200px
   :align: center

Static Assets
-------------

The following files live under ``docs/_static/`` and are copied into the
built documentation by Sphinx:

.. list-table::
   :header-rows: 1
   :widths: 45 10 45

   * - Filename
     - Format
     - Purpose
   * - ``logo-pytest-libiio-banana.svg``
     - SVG
     - Primary logo; contains CSS media queries for dark/light mode.
       Used for both ``light_logo`` and ``dark_logo`` in Furo theme options.
   * - ``logo-pytest-libiio-banana.png``
     - PNG
     - Raster fallback for environments that do not support SVG.
   * - ``custom.css``
     - CSS
     - Extra stylesheet loaded by Furo; sets ``max-width: 200px`` on
       ``.sidebar-brand img`` to keep the logo at a sensible sidebar size.
