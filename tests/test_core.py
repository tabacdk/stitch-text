from pathlib import Path

import pytest

from stitch_text.core import Rasterizer

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
