from __future__ import annotations

import pytest

from stitch_text.cli import input_text, parser


def test_input_text_reads_file(tmp_path) -> None:
    source = tmp_path / "input.txt"
    source.write_text("Korssting\n", encoding="utf-8")
    p = parser()
    args = p.parse_args(["--file", str(source)])
    assert input_text(args, p) == "Korssting\n"


def test_input_text_rejects_text_and_file(tmp_path) -> None:
    source = tmp_path / "input.txt"
    source.write_text("Korssting", encoding="utf-8")
    p = parser()
    args = p.parse_args(["Korssting", "--file", str(source)])
    with pytest.raises(SystemExit):
        input_text(args, p)


def test_input_text_requires_text_or_file() -> None:
    p = parser()
    args = p.parse_args([])
    with pytest.raises(SystemExit):
        input_text(args, p)
