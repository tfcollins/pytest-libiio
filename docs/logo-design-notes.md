# Logo Design Notes

## Concept: The Nano Banana

The pytest-libiio mascot is a **nano banana** — a playful nod to the
"nano" prefix common in hardware and embedded-systems naming (libiio
targets are often nano-scale SoCs and RF front-ends) combined with the
universally friendly banana shape.

### Design Goals

- **Recognisable at small sizes**: the crescent silhouette reads clearly
  even as a 32 × 32 favicon.
- **Theme-aware**: the SVG embeds `@media (prefers-color-scheme: dark)`
  CSS rules so it adapts automatically in both Furo's light and dark
  sidebar themes without needing separate files.
- **Minimal colour palette**: yellow body (`#f5c518`), brown tips
  (`#6b4c11`), and a semi-transparent highlight — keeping the mark clean
  and reproducible on varied backgrounds.
- **Monospace wordmark**: `pytest-libiio` is set in a monospace font to
  reinforce the library's testing and instrumentation identity.

### Static Assets

| File | Purpose |
|------|---------|
| `_static/logo-pytest-libiio-banana.svg` | Primary logo (theme-aware SVG, used by Sphinx/Furo) |
| `_static/logo-pytest-libiio-banana.png` | PNG fallback for contexts that do not support SVG |

### Colour Reference

| Token | Light mode | Dark mode |
|-------|-----------|-----------|
| Banana body | `#f5c518` | `#e6b800` |
| Tip / stem | `#6b4c11` | `#8a6020` |
| Text label | `#3a3a3a` | `#d0d0d0` |
