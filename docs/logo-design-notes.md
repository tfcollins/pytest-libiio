# Logo design notes

## Final logo

**File:** `docs/_static/logo-pytest-libiio.svg`
**Favicon:** `docs/_static/favicon-pytest-libiio.svg`

Both files are self-contained SVGs with inline CSS `@media (prefers-color-scheme: dark)`
overrides so they render correctly on both light and dark documentation themes.

---

## Visual identity

### pytest element
A large checkmark (`polyline`) in pytest green with a classic short-left / long-right
arm ratio (≈ 1 : 2).

| Token | Light value | Dark override |
|-------|-------------|---------------|
| Checkmark stroke | `#10B981` (Emerald-500) | `#34D399` (Emerald-400) |
| Label fill | `#059669` (Emerald-600) | `#34D399` (Emerald-400) |

Reference: <https://commons.wikimedia.org/wiki/File:Pytest_logo.svg>

### libiio element
A 2.5-period sine wave with filled circle nodes at each zero-crossing, evoking the
Industrial I/O (IIO) signal-flow and circuit motifs used in the libiio project.

| Token | Light value | Dark override |
|-------|-------------|---------------|
| Wave stroke / nodes | `#0055B3` | `#60A5FA` (Blue-400) |
| Label fill | `#0055B3` | `#60A5FA` (Blue-400) |

Reference: <https://analogdevicesinc.github.io/libiio/>

### Separator
`·` in `#888888` / `#9CA3AF` (Gray-400 dark override), weight 300.

---

## Logo geometry (400 × 400 viewBox)

```
Checkmark:  points="55,180 148,258 345,65"   stroke-width=24
Wave:       centre y=308, amplitude=20, half-period=69 px (2.5 periods, x=28–373)
Nodes:      cx=97,166,235,304  cy=308  r=5
Text:       x=200 y=375  font-size=44  text-anchor=middle
```

## Favicon geometry (32 × 32 viewBox)

```
Checkmark:  points="3,14 11,22 29,4"   stroke-width=2.5
Wave:       centre y=27, amplitude=4, half-period=10 px (1.5 periods, x=2–32)
```

---

## conf.py wiring

```python
html_static_path = ["_static"]
html_logo = "_static/logo-pytest-libiio.svg"
html_favicon = "_static/favicon-pytest-libiio.svg"
html_theme_options = {
    "light_logo": "logo-pytest-libiio.svg",
    "dark_logo": "logo-pytest-libiio.svg",
}
```

The same SVG serves both light and dark modes because the dark-mode palette is
encoded directly in the SVG via `@media (prefers-color-scheme: dark)`.
