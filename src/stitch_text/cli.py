from __future__ import annotations

import argparse
import re
from pathlib import Path

from .core import Rasterizer
from .output import save_pdf, save_png, save_svg, save_text

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
    p.add_argument("text", nargs="?")
    p.add_argument("-f", "--file", type=Path, help="read input text from a UTF-8 text file")
    p.add_argument("--font", type=Path)
    p.add_argument("--l-height", type=int, default=12)
    p.add_argument("--low-threshold", type=int, default=64)
    p.add_argument("--high-threshold", type=int, default=192)
    p.add_argument("--phase-steps", type=int, default=8)
    p.add_argument("--tracking", type=int, default=0)
    p.add_argument("--padding", type=int, default=1)
    p.add_argument("-c", "--center", action="store_true")
    p.add_argument("-L", "--line-height", type=float, default=1.0)
    p.add_argument("-P", "--paragraph-height", type=float, default=1.5)
    p.add_argument("--format", choices=("png", "svg", "pdf", "text"))
    p.add_argument("--output", type=Path)
    p.add_argument("--cell-size", type=int, default=24)
    p.add_argument("--headline")
    p.add_argument("--count", type=float, default=14.0)
    p.add_argument("--margin-mm", type=float, default=15.0)
    p.add_argument("--letter-size", action="store_true")
    p.add_argument("--page-overlap", type=int, default=4)
    p.add_argument("--no-overlap-mark", action="store_true")
    p.add_argument("--no-grid", action="store_true")
    p.add_argument("--no-baseline", action="store_true")
    return p


def input_text(args: argparse.Namespace, parser_: argparse.ArgumentParser) -> str:
    if args.text is not None and args.file is not None:
        parser_.error("provide either text or --file, not both")
    if args.text is None and args.file is None:
        parser_.error("provide text or --file")
    if args.file is not None:
        return args.file.read_text(encoding="utf-8")
    return str(args.text)


def headline(args: argparse.Namespace, text: str) -> str:
    if args.headline:
        return str(args.headline)
    if args.file is not None:
        return args.file.stem
    words = re.findall(r"\S+", text)
    if len(words) <= 3:
        return " ".join(words)
    return f"{' '.join(words[:3])}..."


def main() -> int:
    p = parser()
    args = p.parse_args()
    text = input_text(args, p)
    font = args.font or default_font()
    rasterizer = Rasterizer(
        font,
        l_height=args.l_height,
        low_threshold=args.low_threshold,
        high_threshold=args.high_threshold,
        phase_steps=args.phase_steps,
    )
    pattern = rasterizer.render_text(
        text,
        tracking=args.tracking,
        padding=args.padding,
        center=args.center,
        line_height=args.line_height,
        paragraph_height=args.paragraph_height,
    )
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
        elif fmt == "pdf":
            paper_size = "letter" if args.letter_size else "a4"
            save_pdf(
                pattern,
                output,
                headline=headline(args, text),
                count=args.count,
                margin_mm=args.margin_mm,
                paper_size=paper_size,
                page_overlap=args.page_overlap,
                mark_overlap=not args.no_overlap_mark,
                show_grid=not args.no_grid,
                show_baseline=not args.no_baseline,
            )
        else:
            raise ValueError(f"unsupported format: {fmt}")
        print(f"Saved {pattern.width} x {pattern.height} stitches to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
