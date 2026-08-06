from __future__ import annotations

import argparse
from pathlib import Path

from .core import Rasterizer
from .output import save_png, save_svg, save_text

FONT_CANDIDATES = (
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/local/share/fonts/DejaVuSans.ttf"),
    Path.home() / ".local/share/fonts/DejaVuSans.ttf",
)


def default_font() -> Path:
    for path in FONT_CANDIDATES:
        if path.is_file():
            return path
    raise FileNotFoundError("DejaVuSans.ttf was not found; use --font")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Convert DejaVu Sans text to cross-stitch.")
    p.add_argument("text")
    p.add_argument("--font", type=Path)
    p.add_argument("--l-height", type=int, default=12)
    p.add_argument("--low-threshold", type=int, default=64)
    p.add_argument("--high-threshold", type=int, default=192)
    p.add_argument("--phase-steps", type=int, default=8)
    p.add_argument("--tracking", type=int, default=0)
    p.add_argument("--padding", type=int, default=1)
    p.add_argument("--format", choices=("png", "svg", "text"))
    p.add_argument("--output", type=Path)
    p.add_argument("--cell-size", type=int, default=24)
    p.add_argument("--no-grid", action="store_true")
    p.add_argument("--no-baseline", action="store_true")
    return p


def main() -> int:
    args = parser().parse_args()
    font = args.font or default_font()
    rasterizer = Rasterizer(
        font,
        l_height=args.l_height,
        low_threshold=args.low_threshold,
        high_threshold=args.high_threshold,
        phase_steps=args.phase_steps,
    )
    pattern = rasterizer.render(args.text, tracking=args.tracking, padding=args.padding)
    fmt = args.format or (args.output.suffix.lstrip(".").lower() if args.output else "text")
    if fmt == "text":
        save_text(pattern, args.output)
    else:
        output = args.output or Path(f"crossstitch.{fmt}")
        if fmt == "png":
            save_png(
                pattern,
                output,
                cell_size=args.cell_size,
                show_grid=not args.no_grid,
                show_baseline=not args.no_baseline,
            )
        elif fmt == "svg":
            save_svg(
                pattern,
                output,
                cell_size=args.cell_size,
                show_grid=not args.no_grid,
                show_baseline=not args.no_baseline,
            )
        else:
            raise ValueError(f"unsupported format: {fmt}")
        print(f"Saved {pattern.width} x {pattern.height} stitches to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
