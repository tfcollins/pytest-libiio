Nano Banana Logo
================

The pytest-libiio mascot is the **nano banana** — a playful nod to the
"nano" prefix common in hardware and embedded-systems naming (libiio
targets are often nano-scale SoCs and RF front-ends) combined with the
universally friendly banana shape.

The SVG asset embeds ``@media (prefers-color-scheme: dark)`` CSS rules so
it adapts automatically to both Furo's light and dark sidebar themes
without requiring separate image files.

For full design rationale, colour tokens, and usage guidance see
:doc:`/logo-design-notes` (source: ``docs/logo-design-notes.md``).

.. image:: /_static/logo-pytest-libiio-banana.svg
   :alt: pytest-libiio nano-banana mascot
   :width: 200px
   :align: center

Static Assets
-------------

The following files provide the logo in supported formats:

``_static/logo-pytest-libiio-banana.svg``
    Primary theme-aware SVG.  Used directly by Sphinx/Furo for the
    sidebar logo (``html_logo`` in ``conf.py``).  Contains embedded CSS
    media queries so the same file serves both light and dark themes.

``_static/logo-pytest-libiio-banana.png``
    PNG raster fallback for environments that do not support SVG (e.g.
    some email clients, older documentation renderers, or PyPI metadata).
