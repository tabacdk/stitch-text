# Crossstitch Font

A small Python project that converts DejaVu Sans text into a deterministic, three-level cross-stitch pattern.

The default scale is defined typographically: the distance from the top of lowercase **l** to the baseline is exactly **12 stitches**. Descenders extend below the baseline.

Each glyph is rasterized separately and cached, so the same glyph always produces the same stitch pattern. Kerning is intentionally disabled. For each glyph, several horizontal subpixel phases are tested and the phase with the fewest half-tone stitches is selected.

Input line breaks are authoritative. The renderer does not wrap, reflow, hyphenate, paginate, or resize text to fit a target width. Multiline output is composed from independently rendered single-line patterns. Centering, when enabled, is applied only on whole-stitch grid coordinates after each line has been rendered.

## Install

```bash
uv sync --dev
```

On Ubuntu, DejaVu Sans is normally found at:

```text
/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
```

## Usage

```bash
stch_txt "Hamburgefontsiv" --output sample.svg
stch_txt "Korssting" --output sample.png
stch_txt "Dejavu" --format text
```

Useful options:

```bash
--l-height 12
--phase-steps 16
--low-threshold 64
--high-threshold 192
--tracking 0
--padding 1
```

More phase steps can reduce half-tones, at the cost of a little more work.

## Development

```bash
uv run pytest
uv run ruff check .
uv run ty check src
```
