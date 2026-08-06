from pathlib import Path

import pytest

from stitch_text.core import GLYPH_GAP, SPACE_WIDTH, Rasterizer, _phase_score

FONT = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
pytestmark = pytest.mark.skipif(not FONT.is_file(), reason="DejaVu Sans not installed")


def test_same_glyph_is_deterministic() -> None:
    rasterizer = Rasterizer(FONT)
    assert rasterizer.glyph("a") == rasterizer.glyph("a")


def test_same_letter_pattern_is_context_independent() -> None:
    rasterizer = Rasterizer(FONT)
    glyph = rasterizer.glyph("a")
    rasterizer.render("banana")
    assert rasterizer.glyph("a") == glyph


def test_l_height_is_twelve_stitches() -> None:
    rasterizer = Rasterizer(FONT, l_height=12)
    pattern = rasterizer.render("l", padding=0)
    occupied_rows = [y for y, row in enumerate(pattern.grid) if any(row)]
    assert pattern.baseline_row - min(occupied_rows) == 12


def test_phase_search_does_not_increase_half_tones() -> None:
    one = Rasterizer(FONT, phase_steps=1).glyph("S")
    many = Rasterizer(FONT, phase_steps=16).glyph("S")
    half_one = sum(value == 1 for row in one.grid for value in row)
    half_many = sum(value == 1 for row in many.grid for value in row)
    assert half_many <= half_one


def test_phase_score_prefers_compact_bounds_before_half_tones() -> None:
    compact: tuple[tuple[int, ...], ...] = (
        (2, 2),
        (2, 1),
    )
    wide: tuple[tuple[int, ...], ...] = (
        (2, 0, 0),
        (0, 0, 2),
    )
    assert _phase_score(compact, half_tones=1, quantization_error=10.0, phase=0.0) < _phase_score(
        wide,
        half_tones=0,
        quantization_error=0.0,
        phase=0.0,
    )


def test_adjacent_glyph_bounding_boxes_have_fixed_gap() -> None:
    rasterizer = Rasterizer(FONT)
    glyph = rasterizer.glyph("l")
    pattern = rasterizer.render("ll", padding=0)
    columns = [x for x in range(pattern.width) if any(row[x] for row in pattern.grid)]
    first_right = glyph.width - 1
    second_left = min(x for x in columns if x > first_right)
    assert second_left - first_right - 1 == GLYPH_GAP


def test_space_has_fixed_width_between_glyph_bounding_boxes() -> None:
    rasterizer = Rasterizer(FONT)
    glyph = rasterizer.glyph("l")
    pattern = rasterizer.render("l l", padding=0)
    columns = [x for x in range(pattern.width) if any(row[x] for row in pattern.grid)]
    first_right = glyph.width - 1
    second_left = min(x for x in columns if x > first_right)
    assert second_left - first_right - 1 == SPACE_WIDTH


def test_multiline_pattern_has_one_baseline_per_visible_line() -> None:
    rasterizer = Rasterizer(FONT)
    pattern = rasterizer.render_text("l\nl", padding=0)
    assert len(pattern.baseline_rows) == 2
    assert rasterizer.line_spacing == 18
    assert pattern.baseline_rows[1] - pattern.baseline_rows[0] == 18


def test_centering_uses_whole_stitch_offsets() -> None:
    rasterizer = Rasterizer(FONT)
    left = rasterizer.render_text("lll\ni", padding=0)
    centered = rasterizer.render_text("lll\ni", padding=0, center=True)
    short = rasterizer.render("i", padding=0)
    expected_offset = (centered.width - short.width) // 2
    left_x = min(x for row in left.grid for x, value in enumerate(row) if value)
    centered_second_line_x = min(
        x
        for y, row in enumerate(centered.grid)
        if y > centered.baseline_rows[0]
        for x, value in enumerate(row)
        if value
    )
    assert left_x == 0
    assert centered_second_line_x == expected_offset


def test_empty_line_uses_paragraph_height_relative_to_line_height() -> None:
    rasterizer = Rasterizer(FONT)
    pattern = rasterizer.render_text("l\n\nl", padding=0)
    line_spacing = round(rasterizer.line_spacing * 1.0)
    paragraph_spacing = round(line_spacing * 1.5)
    assert paragraph_spacing == 27
    assert pattern.baseline_rows[1] - pattern.baseline_rows[0] == 27
