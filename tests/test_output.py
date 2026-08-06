from __future__ import annotations

import pytest

from stitch_text.core import Pattern
from stitch_text.output import (
    pdf_overflows_page,
    pdf_overlap_marker_lines,
    pdf_tile_capacity,
    pdf_tile_starts,
    stitch_aligned_margin_mm,
    stitch_mm,
)


def test_fourteen_count_stitch_size_is_inches_divided_by_count() -> None:
    assert stitch_mm(14) == 25.4 / 14


def test_margin_rounds_up_to_whole_stitches() -> None:
    assert stitch_aligned_margin_mm(15, 14) == (25.4 / 14) * 9


def test_pdf_overflow_detects_too_wide_pattern() -> None:
    pattern = Pattern(((2,) * 200,), (0,))
    assert pdf_overflows_page(pattern, count=14, paper_size="a4")


def test_pdf_tile_capacity_uses_whole_stitches() -> None:
    width, height = pdf_tile_capacity(count=14, paper_size="a4")
    assert width > 0
    assert height > 0
    assert isinstance(width, int)
    assert isinstance(height, int)


def test_pdf_tile_starts_include_overlap() -> None:
    assert pdf_tile_starts(total=200, capacity=80, overlap=4) == (0, 76, 152)


def test_pdf_tile_overlap_must_be_smaller_than_capacity() -> None:
    with pytest.raises(ValueError, match="overlap must be smaller"):
        pdf_tile_starts(total=200, capacity=3, overlap=3)


def test_pdf_overlap_markers_align_on_inner_overlap_gridlines() -> None:
    x_lines, y_lines = pdf_overlap_marker_lines(
        width=80,
        height=100,
        page_overlap=4,
        has_left_overlap=True,
        has_right_overlap=True,
        has_top_overlap=True,
        has_bottom_overlap=True,
    )
    assert x_lines == (2, 78)
    assert y_lines == (2, 98)
