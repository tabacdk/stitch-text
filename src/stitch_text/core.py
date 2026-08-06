from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

Grid = tuple[tuple[int, ...], ...]
_LEGACY_LANCZOS = "LANCZOS"


def _lanczos() -> int:
    resampling = getattr(Image, "Resampling", None)
    if resampling is not None:
        return int(resampling.LANCZOS)
    return int(getattr(Image, _LEGACY_LANCZOS))


def _grayscale_value(value: Any) -> int:
    if isinstance(value, tuple):
        return int(value[0])
    return int(value)


@dataclass(frozen=True)
class GlyphBitmap:
    grid: Grid
    left_bearing: int
    advance: int
    top_from_baseline: int
    phase: float


@dataclass(frozen=True)
class Pattern:
    grid: Grid
    baseline_row: int

    @property
    def width(self) -> int:
        return len(self.grid[0]) if self.grid else 0

    @property
    def height(self) -> int:
        return len(self.grid)


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
        advance = max(1, round(self.font.getlength(char) * self.scale))
        if bbox is None:
            result = GlyphBitmap(((0,),), 0, advance, 0, 0.0)
            self._cache[char] = result
            return result

        left, top, right, bottom = bbox
        source_width = max(1, round(right - left))
        source_height = max(1, round(bottom - top))
        target_width = max(1, round(source_width * self.scale))
        target_height = max(1, round(source_height * self.scale))
        stitch_in_source_pixels = 1.0 / self.scale

        best: tuple[tuple[int, float, float], Grid, float] | None = None
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
            score = (half_tones, quantization_error, min(phase, 1.0 - phase))
            if best is None or score < best[0]:
                best = (score, grid, phase)

        assert best is not None
        _, grid, phase = best
        result = GlyphBitmap(
            grid=grid,
            left_bearing=round(left * self.scale + phase),
            advance=advance,
            top_from_baseline=round(top * self.scale),
            phase=phase,
        )
        self._cache[char] = result
        return result

    def render(self, text: str, *, tracking: int = 0, padding: int = 1) -> Pattern:
        if not text:
            raise ValueError("text must not be empty")
        if padding < 0:
            raise ValueError("padding must not be negative")

        glyphs = [self.glyph(char) for char in text]
        ascender_px, descender_px = self.font.getmetrics()
        ascender = round(ascender_px * self.scale)
        descender = round(descender_px * self.scale)
        baseline = ascender
        width = max(1, sum(g.advance for g in glyphs) + tracking * (len(glyphs) - 1))
        canvas = [[0 for _ in range(width)] for _ in range(ascender + descender)]

        cursor = 0
        for glyph in glyphs:
            top = baseline + glyph.top_from_baseline
            x0 = cursor + glyph.left_bearing
            for gy, row in enumerate(glyph.grid):
                y = top + gy
                if not 0 <= y < len(canvas):
                    continue
                for gx, level in enumerate(row):
                    x = x0 + gx
                    if level and 0 <= x < width:
                        canvas[y][x] = max(canvas[y][x], level)
            cursor += glyph.advance + tracking

        occupied = [(x, y) for y, row in enumerate(canvas) for x, level in enumerate(row) if level]
        if not occupied:
            raise ValueError("rendering produced no visible stitches")

        xs = [x for x, _ in occupied]
        ys = [y for _, y in occupied]
        x0 = max(0, min(xs) - padding)
        x1 = min(width, max(xs) + 1 + padding)
        y0 = max(0, min(ys) - padding)
        y1 = min(len(canvas), max(ys) + 1 + padding)
        cropped = tuple(tuple(row[x0:x1]) for row in canvas[y0:y1])
        return Pattern(cropped, baseline - y0)
