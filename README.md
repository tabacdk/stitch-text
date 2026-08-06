# Crossstitch Font

A small Python project that converts DejaVu Sans text into a deterministic, three-level cross-stitch pattern.

The default scale is defined typographically: the distance from the top of lowercase **l** to the baseline is exactly **12 stitches**. Descenders extend below the baseline.

Each glyph is rasterized separately and cached, so the same glyph always produces the same stitch pattern. Kerning is intentionally disabled. For each glyph, several horizontal subpixel phases are tested. Phase selection first minimizes the visible stitch bounding-box area, then bounding-box width, then half-tone stitches.

Each visible glyph is placed by its own tight stitch bounding box. Adjacent glyph boxes inside a word are separated by exactly 2 stitches by default. A space character advances by exactly 7 stitches.

Input line breaks are authoritative. The renderer does not wrap, reflow, hyphenate, paginate, or resize text to fit a target width. Multiline output is composed from independently rendered single-line patterns. Centering, when enabled, is applied only on whole-stitch grid coordinates after each line has been rendered.

Line and paragraph spacing are fixed whole-stitch counts calculated once at the start of a run. With the default `--l-height 12`, baseline-to-baseline line spacing is 18 stitches. `--line-height` scales that spacing. `--paragraph-height` is relative to the effective line height and is used for empty input lines, so the default paragraph distance is 27 stitches.

PDF output uses fabric count for physical scale. The default is 14-count, meaning 14 stitches per inch. The renderer never autoscales to fit the page. Large patterns are split across as many pages as needed in both directions, with a 4-stitch overlap by default. Page joins are marked with small filled triangles in the margin, positioned to overlap when adjacent pages are taped together. PNG, SVG, and PDF grids accent every 10 stitches with a darker grid line.

## Install

```bash
uv sync --dev
```

On Ubuntu, DejaVu Sans is normally found at:

```text
/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
```

## Why Half-Tones Help

Traditional bitmap letters are built by deciding whether each square is either fully on or fully off. That works well at large sizes, but small stitched letters have very few squares to describe curves, diagonals, and thin details. A round letter like `e` or `s` can become jagged, cramped, or hard to recognize when every stitch must be completely black or completely empty.

Half-tones add a middle choice. Instead of only "no stitch" and "full stitch", this project uses three levels:

```text
0 empty
1 half-tone
2 full
```

In cross-stitch terms, a half-tone is a lighter stitch or a visually softer mark. It lets the pattern suggest that only part of a square belongs to the letter. The grid is still made of whole stitches, but the edge of the letter can look less stair-stepped because some edge stitches are allowed to be lighter than the main body of the letter.

This is similar to sketching with a light pencil before using a dark pen. The dark stitches carry the main shape. The half-tone stitches soften corners, diagonals, and curves so the eye reads the intended letter more easily.

The program still keeps the pattern deterministic and simple: every cell is always one of the same three stitch levels, and the meaning of those levels never changes.

## Usage

```bash
stch_txt "Hamburgefontsiv" --output sample.svg
stch_txt "Korssting" --output sample.png
stch_txt "Dejavu" --format text
stch_txt --file input.txt --output sample.svg
stch_txt --file poem.txt --center --line-height 1.1 --paragraph-height 1.5 --output poem.svg
stch_txt --file chart.txt --headline "Linda" --format pdf --output linda.pdf
stch_txt --config-file local.toml --file chart.txt --format pdf --output chart.pdf
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
--headline "Title"
--count 14
--margin-mm 15
--letter-size
--page-overlap 4
--no-overlap-mark
--config-file local.toml
```

More phase steps can reduce half-tones, at the cost of a little more work.

## Configuration

Default options live in the packaged `stitch_text/defaults.toml` asset. A local TOML file can override any subset of those values. See `local-example.toml` for a fully commented template.

```toml
count = 16
margin_mm = 18
page_overlap = 4
grid = true
baseline = true
```

Precedence is: packaged defaults, then `--config-file`, then explicit CLI options.

## Development

```bash
uv run pytest
uv run ruff check .
uv run ty check src
```

## Release

Releases are made from a clean `main` checkout with:

```bash
python3 scripts/release.py
python3 scripts/release.py --yes
```

The first command is a dry-run. The release script allows ignored local artifacts such as `dist/`,
`artifacts/`, caches, PNGs, and SVGs, but aborts on tracked changes or non-ignored untracked files.
It removes a `-pre` suffix for the release if present, runs `uv sync`, commits the release version,
pushes `main`, creates and pushes the annotated `vX.Y.Z` tag, then bumps `main` to the next
`X.Y.(Z+1)-pre` development version.
