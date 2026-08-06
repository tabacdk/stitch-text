from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

Grid = tuple[tuple[int, ...], ...]
PhaseScore = tuple[int, int, int, float, float]
_LEGACY_LANCZOS = "LANCZOS"
GLYPH_GAP = 2
SPACE_WIDTH = 7
DESCENDER_DEPTH = 3
LINE_GAP = 3


def _lanczos() -> int:
    resampling = getattr(Image, "Resampling", None)
    if resampling is not None:
        return int(resampling.LANCZOS)
    return int(getattr(Image, _LEGACY_LANCZOS))


def _grayscale_value(value: Any) -> int:
    if isinstance(value, tuple):
        return int(value[0])
    return int(value)


def _occupied_bounds(grid: Grid) -> tuple[int, int, int, int] | None:
    occupied = [(x, y) for y, row in enumerate(grid) for x, level in enumerate(row) if level]
    if not occupied:
        return None
    xs = [x for x, _ in occupied]
    ys = [y for _, y in occupied]
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def _phase_score(
    grid: Grid,
    *,
    half_tones: int,
    quantization_error: float,
    phase: float,
) -> PhaseScore:
    bounds = _occupied_bounds(grid)
    if bounds is None:
        return (0, 0, half_tones, quantization_error, min(phase, 1.0 - phase))
    x0, y0, x1, y1 = bounds
    width = x1 - x0
    height = y1 - y0
    return (
        width * height,
        width,
        half_tones,
        quantization_error,
        min(phase, 1.0 - phase),
    )


@dataclass(frozen=True)
class GlyphBitmap:
    grid: Grid
    top_from_baseline: int
    phase: float

    @property
    def width(self) -> int:
        return len(self.grid[0]) if self.grid else 0

    @property
    def height(self) -> int:
        return len(self.grid)


@dataclass(frozen=True)
class Pattern:
    grid: Grid
    baseline_rows: tuple[int, ...]

    @property
    def width(self) -> int:
        return len(self.grid[0]) if self.grid else 0

    @property
    def height(self) -> int:
        return len(self.grid)

    @property
    def baseline_row(self) -> int:
        if len(self.baseline_rows) != 1:
            raise ValueError("pattern has multiple baselines")
        return self.baseline_rows[0]


class Rasterizer:
    def __init__(
        self,
        font_path: Path,
        *,
        l_height: int = 12,
        low_threshold: int = 64,
        high_threshold: int = 192,
        phase_steps: int = 8,
        render_size: int = 240,
    ) -> None:
        if l_height < 2:
            raise ValueError("l_height must be at least 2")
        if not 0 <= low_threshold < high_threshold <= 255:
            raise ValueError("thresholds must satisfy 0 <= low < high <= 255")
        if phase_steps < 1:
            raise ValueError("phase_steps must be at least 1")
        if not font_path.is_file():
            raise FileNotFoundError(font_path)

        self.font_path = font_path
        self.l_height = l_height
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold
        self.phase_steps = phase_steps
        self.font = ImageFont.truetype(str(font_path), render_size)

        bbox = self.font.getbbox("l", anchor="ls")
        if bbox is None or bbox[1] >= 0:
            raise ValueError("font does not provide a usable lowercase l")
        self.scale = l_height / (-bbox[1])
        self._cache: dict[str, GlyphBitmap] = {}
        self.line_spacing = l_height + DESCENDER_DEPTH + LINE_GAP

    def _quantize(self, value: int) -> int:
        if value < self.low_threshold:
            return 0
        if value < self.high_threshold:
            return 1
        return 2

    def glyph(self, char: str) -> GlyphBitmap:
        if len(char) != 1:
            raise ValueError("glyph() accepts exactly one character")
        cached = self._cache.get(char)
        if cached is not None:
            return cached

        bbox = self.font.getbbox(char, anchor="ls")
        if bbox is None:
            result = GlyphBitmap((), 0, 0.0)
            self._cache[char] = result
            return result

        left, top, right, bottom = bbox
        source_width = max(1, round(right - left))
        source_height = max(1, round(bottom - top))
        target_width = max(1, round(source_width * self.scale))
        target_height = max(1, round(source_height * self.scale))
        stitch_in_source_pixels = 1.0 / self.scale

        best: tuple[PhaseScore, Grid, float] | None = None
        for step in range(self.phase_steps):
            phase = step / self.phase_steps
            shift = phase * stitch_in_source_pixels
            margin = int(stitch_in_source_pixels) + 24
            image = Image.new(
                "L",
                (
                    source_width + 2 * margin + int(stitch_in_source_pixels) + 2,
                    source_height + 2 * margin,
                ),
                0,
            )
            draw = ImageDraw.Draw(image)
            draw.text(
                (margin - left + shift, margin - top),
                char,
                font=self.font,
                fill=255,
                anchor="ls",
            )
            image = image.crop((margin, margin, margin + source_width, margin + source_height))
            image = image.resize((target_width, target_height), _lanczos())

            rows: list[tuple[int, ...]] = []
            half_tones = 0
            quantization_error = 0.0
            for y in range(target_height):
                row: list[int] = []
                for x in range(target_width):
                    value = _grayscale_value(image.getpixel((x, y)))
                    level = self._quantize(value)
                    row.append(level)
                    half_tones += level == 1
                    quantization_error += abs(value - (0, 128, 255)[level])
                rows.append(tuple(row))

            grid = tuple(rows)
            score = _phase_score(
                grid,
                half_tones=half_tones,
                quantization_error=quantization_error,
                phase=phase,
            )
            if best is None or score < best[0]:
                best = (score, grid, phase)

        assert best is not None
        _, grid, phase = best
        bounds = _occupied_bounds(grid)
        if bounds is None:
            result = GlyphBitmap((), 0, phase)
            self._cache[char] = result
            return result
        x0, y0, x1, y1 = bounds
        tight_grid = tuple(row[x0:x1] for row in grid[y0:y1])
        result = GlyphBitmap(
            grid=tight_grid,
            top_from_baseline=round(top * self.scale) + y0,
            phase=phase,
        )
        self._cache[char] = result
        return result

    def render(self, text: str, *, tracking: int = 0, padding: int = 1) -> Pattern:
        if not text:
            raise ValueError("text must not be empty")
        if padding < 0:
            raise ValueError("padding must not be negative")

        glyphs = [None if char == " " else self.glyph(char) for char in text]
        ascender_px, descender_px = self.font.getmetrics()
        ascender = round(ascender_px * self.scale)
        descender = round(descender_px * self.scale)
        baseline = ascender
        cursor = 0
        placements: list[tuple[int, GlyphBitmap]] = []
        needs_glyph_gap = False
        for glyph in glyphs:
            if glyph is None:
                cursor += SPACE_WIDTH
                needs_glyph_gap = False
                continue
            if not glyph.grid:
                continue
            if needs_glyph_gap:
                cursor += GLYPH_GAP + tracking
            placements.append((cursor, glyph))
            cursor += glyph.width
            needs_glyph_gap = True

        width = max(1, cursor)
        canvas = [[0 for _ in range(width)] for _ in range(ascender + descender)]

        for x0, glyph in placements:
            top = baseline + glyph.top_from_baseline
            for gy, row in enumerate(glyph.grid):
                y = top + gy
                if not 0 <= y < len(canvas):
                    continue
                for gx, level in enumerate(row):
                    x = x0 + gx
                    if level and 0 <= x < width:
                        canvas[y][x] = max(canvas[y][x], level)

        bounds = _occupied_bounds(tuple(tuple(row) for row in canvas))
        if bounds is None:
            raise ValueError("rendering produced no visible stitches")

        occupied_x0, occupied_y0, occupied_x1, occupied_y1 = bounds
        x0 = max(0, occupied_x0 - padding)
        x1 = min(width, occupied_x1 + padding)
        y0 = max(0, occupied_y0 - padding)
        y1 = min(len(canvas), occupied_y1 + padding)
        cropped = tuple(tuple(row[x0:x1]) for row in canvas[y0:y1])
        return Pattern(cropped, (baseline - y0,))

    def render_text(
        self,
        text: str,
        *,
        tracking: int = 0,
        padding: int = 1,
        center: bool = False,
        line_height: float = 1.0,
        paragraph_height: float = 1.5,
    ) -> Pattern:
        if line_height <= 0:
            raise ValueError("line_height must be greater than 0")
        if paragraph_height <= 0:
            raise ValueError("paragraph_height must be greater than 0")

        line_spacing = max(1, round(self.line_spacing * line_height))
        paragraph_spacing = max(1, round(line_spacing * paragraph_height))
        if "\n" not in text:
            return self.render(text, tracking=tracking, padding=padding)

        raw_lines = text.splitlines()
        if not raw_lines:
            raise ValueError("text must not be empty")

        rendered_lines: list[Pattern | None] = [
            None if line == "" else self.render(line, tracking=tracking, padding=padding)
            for line in raw_lines
        ]
        visible_lines = [line for line in rendered_lines if line is not None]
        if not visible_lines:
            raise ValueError("rendering produced no visible stitches")

        width = max(line.width for line in visible_lines)
        line_baselines: list[int] = []
        baseline = visible_lines[0].baseline_rows[0]
        previous_visible = False
        for line in rendered_lines:
            if line is None:
                baseline += paragraph_spacing
                previous_visible = False
                continue
            if previous_visible:
                baseline += line_spacing
            line_baselines.append(baseline)
            previous_visible = True

        line_tops = [
            line_baseline - line.baseline_rows[0]
            for line_baseline, line in zip(line_baselines, visible_lines, strict=True)
        ]
        min_y = min(line_tops)
        if min_y < 0:
            line_tops = [top - min_y for top in line_tops]
            line_baselines = [baseline_row - min_y for baseline_row in line_baselines]

        height = max(top + line.height for top, line in zip(line_tops, visible_lines, strict=True))
        canvas = [[0 for _ in range(width)] for _ in range(height)]
        baseline_rows: list[int] = []
        for top, line, line_baseline in zip(line_tops, visible_lines, line_baselines, strict=True):
            x0 = (width - line.width) // 2 if center else 0
            baseline_rows.append(line_baseline)
            for gy, row in enumerate(line.grid):
                for gx, level in enumerate(row):
                    if level:
                        canvas[top + gy][x0 + gx] = max(canvas[top + gy][x0 + gx], level)

        return Pattern(tuple(tuple(row) for row in canvas), tuple(baseline_rows))
