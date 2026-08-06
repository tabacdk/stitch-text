# Crossstitch Font

A small Python project that converts DejaVu Sans text into a deterministic, three-level cross-stitch pattern.

The default scale is defined typographically: the distance from the top of lowercase **l** to the baseline is exactly **12 stitches**. Descenders extend below the baseline.

Each glyph is rasterized separately and cached, so the same glyph always produces the same stitch pattern. Kerning is intentionally disabled. For each glyph, several horizontal subpixel phases are tested. Phase selection first minimizes the visible stitch bounding-box area, then bounding-box width, then half-tone stitches.

Each visible glyph is placed by its own tight stitch bounding box. Adjacent glyph boxes inside a word are separated by exactly 2 stitches by default. A space character advances by exactly 7 stitches.

Input line breaks are authoritative. The renderer does not wrap, reflow, hyphenate, paginate, or resize text to fit a target width. Multiline output is composed from independently rendered single-line patterns. Centering, when enabled, is applied only on whole-stitch grid coordinates after each line has been rendered.

Line and paragraph spacing are fixed whole-stitch counts calculated once at the start of a run. With the default `--l-height 12`, baseline-to-baseline line spacing is 18 stitches. `--line-height` scales that spacing. `--paragraph-height` is relative to the effective line height and is used for empty input lines, so the default paragraph distance is 27 stitches.

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
stch_txt --file input.txt --output sample.svg
stch_txt --file poem.txt --center --line-height 1.1 --paragraph-height 1.5 --output poem.svg
```

Useful options:

```bash
--l-height 12
--phase-steps 16
--low-threshold 64
--high-threshold 192
--tracking 0
--padding 1
-f, --file input.txt
-c, --center
-L, --line-height 1.0
-P, --paragraph-height 1.5
```

More phase steps can reduce half-tones, at the cost of a little more work.

## Development

```bash
uv run pytest
uv run ruff check .
uv run ty check src
```
