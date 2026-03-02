# Logo Design Notes — pytest-libiio Nano Banana

## Concept

The **nano banana** is the official mascot of pytest-libiio.  The name is a
play on the two core themes of the project:

* **nano** — Industrial I/O (IIO) devices routinely measure signals in the
  nano-scale (nanoamperes, nanovolts, nanoseconds).  "Nano" also evokes the
  tiny, embedded nature of IIO hardware.
* **banana** — A banana plug is the standard connector used to probe signals
  on test and measurement equipment, making it the natural symbol for a
  hardware-testing library.

Together the nano banana represents precision measurement at the smallest
scales — a friendly face on serious test infrastructure.

## Visual Design

The mascot is a small banana with an expressive cartoon face:

* **Body** — A yellow crescent shape rendered with two overlapping Bézier
  paths to suggest the natural ridge along a real banana.  The outer fill is
  `#FFD600` (vivid yellow); the inner ridge is `#FFC107` (amber) to give
  depth without a drop shadow.
* **Stem** — A short brown cap (`#6D4C41`) at the top, matching natural
  banana colouring.
* **Eyes** — Two filled circles with a small white specular highlight to give
  the impression of life.  In light mode the irises are near-black
  (`#1A1A1A`); in dark mode they invert to near-white (`#FAFAFA`) so the face
  remains legible.
* **Smile** — A gentle upward-curving arc in brown to match the stem.
* **Cheeks** — Subtle rosy ellipses (`#EF9A9A`, 40 % opacity) for warmth.
* **Signal decoration** — A small sine-wave glyph and the word *nano* in
  green (`#388E3C` / `#66BB6A` dark mode) reference the oscillating IIO
  signals that the plugin manages.

## Dark / Light Mode

The SVG embeds a CSS `@media (prefers-color-scheme: dark)` block so a single
file works correctly in both Furo themes without duplication.  Only the
eye fill, stem, and signal accent colours change; the banana body remains
bright yellow in both modes because yellow is legible on both white and dark
backgrounds.

## File Inventory

| File | Purpose |
|------|---------|
| `docs/_static/logo-pytest-libiio-banana.svg` | Theme-aware SVG master (preferred) |
| `docs/_static/logo-pytest-libiio-banana.png` | PNG raster fallback for environments that do not support SVG |

## Usage in Sphinx

`docs/conf.py` wires the logo into Furo using:

```python
html_logo = "_static/logo-pytest-libiio-banana.svg"

html_theme_options = {
    "light_logo": "logo-pytest-libiio-banana.svg",
    "dark_logo": "logo-pytest-libiio-banana.svg",
}
```

Because the SVG already handles both colour schemes internally, the same file
is referenced for both the `light_logo` and `dark_logo` theme options.

The `docs/_static/custom.css` file constrains the sidebar logo width to avoid
it overflowing on narrow viewports:

```css
.sidebar-brand img {
    max-width: 200px;
}
```
