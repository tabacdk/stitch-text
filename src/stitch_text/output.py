from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from .core import Pattern


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
            draw.line((xx, 0, xx, pattern.height * cell_size), fill=(210, 210, 210))
        for y in range(pattern.height + 1):
            yy = y * cell_size
            draw.line((0, yy, pattern.width * cell_size, yy), fill=(210, 210, 210))
    if show_baseline:
        for baseline_row in pattern.baseline_rows:
            yy = baseline_row * cell_size
            draw.line((0, yy, pattern.width * cell_size, yy), fill=(220, 40, 40), width=2)
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
            parts.append(f'<line x1="{xx}" y1="0" x2="{xx}" y2="{height}" stroke="#d2d2d2"/>')
        for y in range(pattern.height + 1):
            yy = y * cell_size
            parts.append(f'<line x1="0" y1="{yy}" x2="{width}" y2="{yy}" stroke="#d2d2d2"/>')
    if show_baseline:
        for baseline_row in pattern.baseline_rows:
            yy = baseline_row * cell_size
            parts.append(
                f'<line x1="0" y1="{yy}" x2="{width}" y2="{yy}" '
                'stroke="#dc2828" stroke-width="2"/>'
            )
    parts.append("</svg>")
    output.write_text("\n".join(parts), encoding="utf-8")
