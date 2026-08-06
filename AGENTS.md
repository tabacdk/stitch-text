# AGENTS.md

## Project purpose
Create a deterministic cross-stitch bitmap font derived from DejaVu Sans.

## Non-negotiable behavior
- The top of lowercase `l` to the baseline is exactly 12 stitches by default.
- A glyph must render identically every time, independent of neighbouring glyphs.
- Do not use kerning or context-dependent shaping.
- Glyph placement is on whole-stitch coordinates.
- Minimize half-tone stitches by trying horizontal subpixel phases per glyph.
- The chosen phase is deterministic and cached per glyph.
- Phase selection first minimizes the visible stitch bounding-box area, then bounding-box width,
  then half-tone stitches.
- Preserve descenders below the baseline.
- Keep compatibility with old Pillow versions that lack `Image.Resampling`.
- Each visible glyph is rendered to its own tight stitch bounding box. Adjacent glyph bounding
  boxes inside a word are separated by exactly 2 stitches by default. A space character advances
  by exactly 7 stitches.
- Input line breaks are authoritative. Do not wrap, reflow, hyphenate, paginate, or resize text
  to fit a target width.
- Multiline output is composed from independently rendered single-line patterns.
- Centering is done only on whole-stitch grid coordinates after each line has been rendered.
- Line and paragraph spacing are calculated once at the start of a run as whole-stitch counts.
  Default baseline-to-baseline line spacing is 18 stitches when `--l-height` is 12. `--line-height`
  scales that spacing; `--paragraph-height` scales the effective line height.

## Commands
- Install: `uv sync --dev`
- Test: `uv run pytest`
- Lint: `uv run ruff check .`
- Type-check: `uv run ty check src`
- Run: `stch_txt "Hamburgefontsiv" --output sample.svg`

## Coding style
- Python 3.10+
- Keep rendering logic pure where practical.
- Add tests for deterministic glyph rendering and baseline height.
- Do not silently change the meaning of the three levels: 0 empty, 1 half-tone, 2 full.


## Roadmap
1. [x] Add an `-f/--file` switch to read input from a text file rather than from commandline
2. [x] Support multiline text by composing independently rendered lines. Add `-c/--center` for
   centered justification on whole-stitch coordinates (left justified is default). Do not add
   automatic line wrapping. Add `-L/--line-height` and `-P/--paragraph-height`.
3. [ ] Support PDF output. Add `--A4` and `--letter-size` for paper size conformity, default A4
4. [ ] Batch mode. Add `--source-dir`, `--dest-dir`, and `--config-file` switches
5. [ ] Add command `stch_gui` for `tkinter`-based GUI tool.
6. Improve README.md
