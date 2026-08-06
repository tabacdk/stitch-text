from __future__ import annotations

import math
from pathlib import Path
from typing import Literal

from PIL import Image, ImageDraw
from reportlab.lib import pagesizes
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .core import Pattern

PaperSize = Literal["a4", "letter"]
Rgb = tuple[int, int, int]
_GRID_LIGHT = (210, 210, 210)
_GRID_ACCENT = (150, 150, 150)
_BASELINE = (220, 40, 40)
_SVG_GRID_LIGHT = "#d2d2d2"
_SVG_GRID_ACCENT = "#969696"
_SVG_BASELINE = "#dc2828"


def stitch_mm(count: float) -> float:
    if count <= 0:
        raise ValueError("count must be greater than 0")
    return 25.4 / count


def stitch_aligned_margin_mm(requested_margin_mm: float, count: float) -> float:
    if requested_margin_mm < 0:
        raise ValueError("margin_mm must not be negative")
    size = stitch_mm(count)
    return math.ceil(requested_margin_mm / size) * size


def _rgb_grid_color(index: int, light: Rgb, accent: Rgb) -> Rgb:
    return accent if index % 10 == 0 else light


def _svg_grid_color(index: int, light: str, accent: str) -> str:
    return accent if index % 10 == 0 else light


def save_text(pattern: Pattern, output: Path | None = None) -> None:
    chars = {0: "·", 1: "▒", 2: "█"}
    lines = []
    baseline_rows = set(pattern.baseline_rows)
    for y, row in enumerate(pattern.grid):
        prefix = "─" if y in baseline_rows else " "
        lines.append(prefix + "".join(chars[value] for value in row))
    content = "\n".join(lines) + "\n"
    if output is None:
        print(content, end="")
    else:
        output.write_text(content, encoding="utf-8")


def save_png(
    pattern: Pattern,
    output: Path,
    *,
    cell_size: int = 24,
    show_grid: bool = True,
    show_baseline: bool = True,
) -> None:
    image = Image.new(
        "RGB",
        (pattern.width * cell_size + 1, pattern.height * cell_size + 1),
        "white",
    )
    draw = ImageDraw.Draw(image)
    fills = {1: (170, 170, 170), 2: (25, 25, 25)}
    for y, row in enumerate(pattern.grid):
        for x, level in enumerate(row):
            if level:
                draw.rectangle(
                    (
                        x * cell_size + 1,
                        y * cell_size + 1,
                        (x + 1) * cell_size - 1,
                        (y + 1) * cell_size - 1,
                    ),
                    fill=fills[level],
                )
    if show_grid:
        for x in range(pattern.width + 1):
            xx = x * cell_size
            draw.line(
                (xx, 0, xx, pattern.height * cell_size),
                fill=_rgb_grid_color(x, _GRID_LIGHT, _GRID_ACCENT),
            )
        for y in range(pattern.height + 1):
            yy = y * cell_size
            draw.line(
                (0, yy, pattern.width * cell_size, yy),
                fill=_rgb_grid_color(y, _GRID_LIGHT, _GRID_ACCENT),
            )
    if show_baseline:
        for baseline_row in pattern.baseline_rows:
            yy = baseline_row * cell_size
            draw.line((0, yy, pattern.width * cell_size, yy), fill=_BASELINE, width=2)
    image.save(output)


def save_svg(
    pattern: Pattern,
    output: Path,
    *,
    cell_size: int = 24,
    show_grid: bool = True,
    show_baseline: bool = True,
) -> None:
    width = pattern.width * cell_size
    height = pattern.height * cell_size
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
    ]
    fills = {1: "#aaaaaa", 2: "#191919"}
    for y, row in enumerate(pattern.grid):
        for x, level in enumerate(row):
            if level:
                parts.append(
                    f'<rect x="{x * cell_size + 1}" y="{y * cell_size + 1}" '
                    f'width="{cell_size - 2}" height="{cell_size - 2}" fill="{fills[level]}"/>'
                )
    if show_grid:
        for x in range(pattern.width + 1):
            xx = x * cell_size
            color = _svg_grid_color(x, _SVG_GRID_LIGHT, _SVG_GRID_ACCENT)
            parts.append(f'<line x1="{xx}" y1="0" x2="{xx}" y2="{height}" stroke="{color}"/>')
        for y in range(pattern.height + 1):
            yy = y * cell_size
            color = _svg_grid_color(y, _SVG_GRID_LIGHT, _SVG_GRID_ACCENT)
            parts.append(f'<line x1="0" y1="{yy}" x2="{width}" y2="{yy}" stroke="{color}"/>')
    if show_baseline:
        for baseline_row in pattern.baseline_rows:
            yy = baseline_row * cell_size
            parts.append(
                f'<line x1="0" y1="{yy}" x2="{width}" y2="{yy}" '
                f'stroke="{_SVG_BASELINE}" stroke-width="2"/>'
            )
    parts.append("</svg>")
    output.write_text("\n".join(parts), encoding="utf-8")


def pdf_page_size(paper_size: PaperSize) -> tuple[float, float]:
    if paper_size == "a4":
        return pagesizes.A4
    if paper_size == "letter":
        return pagesizes.LETTER
    raise ValueError(f"unsupported paper size: {paper_size}")


def pdf_overflows_page(
    pattern: Pattern,
    *,
    count: float = 14.0,
    margin_mm: float = 15.0,
    paper_size: PaperSize = "a4",
    headline_gap_stitches: int = 4,
    headline_height_mm: float = 5.0,
) -> bool:
    page_width, page_height = pdf_page_size(paper_size)
    cell = stitch_mm(count) * mm
    margin = stitch_aligned_margin_mm(margin_mm, count) * mm
    diagram_width = pattern.width * cell
    diagram_height = pattern.height * cell
    headline_block = headline_height_mm * mm + headline_gap_stitches * cell
    return (
        margin + diagram_width > page_width - margin
        or page_height - margin - headline_block - diagram_height < margin
    )


def pdf_tile_capacity(
    *,
    count: float = 14.0,
    margin_mm: float = 15.0,
    paper_size: PaperSize = "a4",
    headline_gap_stitches: int = 4,
    headline_height_mm: float = 5.0,
) -> tuple[int, int]:
    page_width, page_height = pdf_page_size(paper_size)
    cell = stitch_mm(count) * mm
    margin = stitch_aligned_margin_mm(margin_mm, count) * mm
    available_width = page_width - 2 * margin
    available_height = page_height - 2 * margin - headline_height_mm * mm - headline_gap_stitches * cell
    width = math.floor(available_width / cell)
    height = math.floor(available_height / cell)
    if width < 1 or height < 1:
        raise ValueError("page cannot fit any stitches with the requested margin and count")
    return width, height


def pdf_tile_starts(total: int, capacity: int, overlap: int) -> tuple[int, ...]:
    if total < 1:
        raise ValueError("total must be at least 1")
    if capacity < 1:
        raise ValueError("capacity must be at least 1")
    if overlap < 0:
        raise ValueError("overlap must not be negative")
    if overlap >= capacity:
        raise ValueError("overlap must be smaller than the tile capacity")

    starts = [0]
    step = capacity - overlap
    while starts[-1] + capacity < total:
        starts.append(starts[-1] + step)
    return tuple(starts)


def pdf_overlap_marker_lines(
    *,
    width: int,
    height: int,
    page_overlap: int,
    has_left_overlap: bool,
    has_right_overlap: bool,
    has_top_overlap: bool,
    has_bottom_overlap: bool,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    seam_offset = page_overlap // 2
    x_lines = tuple(
        line
        for line in (
            seam_offset if has_left_overlap else None,
            width - seam_offset if has_right_overlap else None,
        )
        if line is not None and 0 < line < width
    )
    y_lines = tuple(
        line
        for line in (
            seam_offset if has_top_overlap else None,
            height - seam_offset if has_bottom_overlap else None,
        )
        if line is not None and 0 < line < height
    )
    return x_lines, y_lines


def _draw_pdf_overlap_markers(
    pdf: canvas.Canvas,
    *,
    grid_left: float,
    grid_top: float,
    grid_bottom: float,
    cell: float,
    width: int,
    height: int,
    page_overlap: int,
    has_left_overlap: bool,
    has_right_overlap: bool,
    has_top_overlap: bool,
    has_bottom_overlap: bool,
) -> None:
    marker = cell * 0.65
    offset = cell * 0.35
    x_lines, y_lines = pdf_overlap_marker_lines(
        width=width,
        height=height,
        page_overlap=page_overlap,
        has_left_overlap=has_left_overlap,
        has_right_overlap=has_right_overlap,
        has_top_overlap=has_top_overlap,
        has_bottom_overlap=has_bottom_overlap,
    )
    pdf.setFillColorRGB(0.20, 0.20, 0.20)

    for x_line in x_lines:
        path = pdf.beginPath()
        x = grid_left + x_line * cell
        y = grid_top + offset
        path.moveTo(x - marker / 2, y + marker)
        path.lineTo(x, y)
        path.lineTo(x + marker / 2, y + marker)
        path.close()
        pdf.drawPath(path, stroke=0, fill=1)

    for y_line in y_lines:
        path = pdf.beginPath()
        x = grid_left - offset
        y = grid_top - y_line * cell
        path.moveTo(x - marker, y + marker / 2)
        path.lineTo(x, y)
        path.lineTo(x - marker, y - marker / 2)
        path.close()
        pdf.drawPath(path, stroke=0, fill=1)


def save_pdf(
    pattern: Pattern,
    output: Path,
    *,
    headline: str,
    count: float = 14.0,
    margin_mm: float = 15.0,
    paper_size: PaperSize = "a4",
    page_overlap: int = 4,
    mark_overlap: bool = True,
    show_grid: bool = True,
    show_baseline: bool = True,
) -> None:
    page_width, page_height = pdf_page_size(paper_size)
    cell = stitch_mm(count) * mm
    margin = stitch_aligned_margin_mm(margin_mm, count) * mm
    headline_gap = 4 * cell
    headline_font_size = 14
    headline_y = page_height - margin - headline_font_size
    grid_left = margin
    grid_top = headline_y - headline_gap
    tile_width, tile_height = pdf_tile_capacity(count=count, margin_mm=margin_mm, paper_size=paper_size)
    x_starts = pdf_tile_starts(pattern.width, tile_width, page_overlap)
    y_starts = pdf_tile_starts(pattern.height, tile_height, page_overlap)

    pdf = canvas.Canvas(str(output), pagesize=(page_width, page_height))
    pdf.setTitle(headline)
    fills = {1: (0.67, 0.67, 0.67), 2: (0.10, 0.10, 0.10)}

    for page_y, y_start in enumerate(y_starts, start=1):
        for page_x, x_start in enumerate(x_starts, start=1):
            x_end = min(pattern.width, x_start + tile_width)
            y_end = min(pattern.height, y_start + tile_height)
            width = x_end - x_start
            height = y_end - y_start
            grid_bottom = grid_top - height * cell
            page_headline = f"{headline} [{page_x}/{len(x_starts)}, {page_y}/{len(y_starts)}]"

            pdf.setFont("Helvetica", headline_font_size)
            pdf.drawString(margin, headline_y, page_headline)

            if mark_overlap:
                _draw_pdf_overlap_markers(
                    pdf,
                    grid_left=grid_left,
                    grid_top=grid_top,
                    grid_bottom=grid_bottom,
                    cell=cell,
                    width=width,
                    height=height,
                    page_overlap=page_overlap,
                    has_left_overlap=x_start > 0,
                    has_right_overlap=page_x < len(x_starts),
                    has_top_overlap=y_start > 0,
                    has_bottom_overlap=page_y < len(y_starts),
                )

            for global_y in range(y_start, y_end):
                row = pattern.grid[global_y]
                for global_x in range(x_start, x_end):
                    level = row[global_x]
                    if level:
                        pdf.setFillColorRGB(*fills[level])
                        local_x = global_x - x_start
                        local_y = global_y - y_start
                        pdf.rect(
                            grid_left + local_x * cell,
                            grid_bottom + (height - local_y - 1) * cell,
                            cell,
                            cell,
                            stroke=0,
                            fill=1,
                        )

            if show_grid:
                pdf.setLineWidth(0.25)
                for global_x in range(x_start, x_end + 1):
                    pdf.setStrokeColor(
                        _SVG_GRID_ACCENT if global_x % 10 == 0 else _SVG_GRID_LIGHT
                    )
                    xx = grid_left + (global_x - x_start) * cell
                    pdf.line(xx, grid_bottom, xx, grid_top)
                for global_y in range(y_start, y_end + 1):
                    pdf.setStrokeColor(
                        _SVG_GRID_ACCENT if global_y % 10 == 0 else _SVG_GRID_LIGHT
                    )
                    yy = grid_top - (global_y - y_start) * cell
                    pdf.line(grid_left, yy, grid_left + width * cell, yy)

            if show_baseline:
                pdf.setStrokeColor(_SVG_BASELINE)
                pdf.setLineWidth(0.5)
                for baseline_row in pattern.baseline_rows:
                    if y_start <= baseline_row <= y_end:
                        yy = grid_top - (baseline_row - y_start) * cell
                        pdf.line(grid_left, yy, grid_left + width * cell, yy)

            if not (page_y == len(y_starts) and page_x == len(x_starts)):
                pdf.showPage()

    pdf.save()
