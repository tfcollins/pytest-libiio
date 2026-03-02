# Logo Design Notes – Nano-Banana Mascot

## Concept

The **nano-banana** is the mascot for pytest-libiio.  The name plays on
*nano* (the ``libiio`` context URI scheme used for USB/serial devices) and
the playful shape of a banana, which echoes the curved crescent profile of
many IIO sensor chips.

## Design Goals

* **Friendly and memorable** – a cartoon banana face makes the project
  approachable for newcomers.
* **Theme-aware** – the SVG uses CSS ``@media (prefers-color-scheme: dark)``
  rules so the logo adapts automatically to the reader's system preference
  without needing separate light/dark image files.
* **Scalable** – as an SVG the logo is resolution-independent and renders
  crisply at any size, from favicon to print.

## Colour Palette

| Token              | Light mode | Dark mode  |
|--------------------|------------|------------|
| `banana-body`      | `#FFD700`  | `#E6C200`  |
| `banana-shadow`    | `#C8A200`  | `#B09000`  |
| `banana-highlight` | `#FFEC6E`  | `#FFF0A0`  |
| `banana-tip`       | `#8B6914`  | `#A07820`  |
| Face / text        | `#1A1A1A`  | `#F0F0F0`  |

## Files

| File                                    | Format | Purpose                          |
|-----------------------------------------|--------|----------------------------------|
| `_static/logo-pytest-libiio-banana.svg` | SVG    | Primary logo (theme-aware)       |
| `_static/logo-pytest-libiio-banana.png` | PNG    | Fallback for environments that   |
|                                         |        | do not support SVG               |

## Usage in Sphinx

The Furo theme reads `light_logo` and `dark_logo` from
``html_theme_options``.  Because the SVG already handles both colour
schemes internally, the same file is referenced for both keys:

```python
html_logo = "_static/logo-pytest-libiio-banana.svg"
html_theme_options = {
    "light_logo": "logo-pytest-libiio-banana.svg",
    "dark_logo":  "logo-pytest-libiio-banana.svg",
}
```
