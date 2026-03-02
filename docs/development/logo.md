# Nano-Banana Logo

The **nano-banana** is the mascot of pytest-libiio. The name plays on *libiio* (the
Industrial I/O library) and the lightweight, zero-overhead spirit of the plugin: a tool
so small it fits in your pocket — or, indeed, in a banana.

Full design rationale, colour palette, and theme-aware implementation details are
documented in {doc}`/logo-design-notes`.

## Logo Preview

```{image} /_static/logo-pytest-libiio-banana.svg
:alt: pytest-libiio nano-banana logo
:align: center
:width: 200px
```

## Static Assets

| File                                   | Format | Purpose                                |
|----------------------------------------|--------|----------------------------------------|
| `_static/logo-pytest-libiio-banana.svg` | SVG    | Primary logo — theme-aware via CSS media queries |
| `_static/logo-pytest-libiio-banana.png` | PNG    | Raster fallback for environments that do not support SVG |

The SVG is used for both the Furo light and dark themes because it embeds
`@media (prefers-color-scheme: dark)` rules directly, eliminating the need for
separate per-theme assets.
