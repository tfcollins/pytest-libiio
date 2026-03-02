# Logo Design Notes – pytest-libiio Nano-Banana

## Concept

The **nano-banana** mascot captures the spirit of the pytest-libiio project in a single, friendly icon. The name is a play on *libiio* (the Industrial I/O library) and the tiny, low-overhead nature of the plugin — a "nano" tool that handles IIO contexts without getting in your way.

## Design Goals

- **Approachable** – a cartoon banana is immediately recognisable and non-threatening, fitting for a developer-tools project.
- **Memorable** – the banana silhouette is distinctive in a sea of robot/gear/chip logos common to embedded tooling.
- **Theme-aware** – the SVG uses CSS `@media (prefers-color-scheme: dark)` queries so it looks sharp in both Furo's light and dark sidebar themes without needing separate assets.
- **Scalable** – vector format ensures crisp rendering from 16 px favicon to full-page splash.

## Colour Palette

| Token           | Light mode | Dark mode  | Usage               |
|-----------------|------------|------------|---------------------|
| banana-body     | `#FFD700`  | `#F5C518`  | Main banana fill    |
| banana-shadow   | `#E6B800`  | `#D4A900`  | Underside shading   |
| banana-tip      | `#8B6914`  | `#C8A040`  | Stem and bottom tip |
| banana-shine    | `#FFF9C4`  | `#FFFDE7`  | Highlight glint     |
| text-label      | `#3D3D3D`  | `#F0F0F0`  | Primary label text  |
| text-sub        | `#666666`  | `#AAAAAA`  | Subtitle text       |

## Files

| File                                          | Format | Purpose                          |
|-----------------------------------------------|--------|----------------------------------|
| `docs/_static/logo-pytest-libiio-banana.svg`  | SVG    | Primary theme-aware vector logo  |
| `docs/_static/logo-pytest-libiio-banana.png`  | PNG    | Raster fallback (200 × 200 px)   |

## Usage in Sphinx / Furo

The SVG is wired up in `docs/conf.py` as both the light and dark logo.  Because the SVG
contains its own `@media (prefers-color-scheme: dark)` rules, a single file covers both
themes:

```python
html_logo = "_static/logo-pytest-libiio-banana.svg"
html_theme_options = {
    "light_logo": "logo-pytest-libiio-banana.svg",
    "dark_logo": "logo-pytest-libiio-banana.svg",
}
```

A custom CSS rule in `docs/_static/custom.css` constrains the sidebar width:

```css
.sidebar-brand img { max-width: 200px; }
```
