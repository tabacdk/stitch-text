from __future__ import annotations

import pytest

from stitch_text.cli import config_from_args, headline, input_text, parser


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


def test_headline_option_wins(tmp_path) -> None:
    source = tmp_path / "input.txt"
    source.write_text("ignored", encoding="utf-8")
    args = parser().parse_args(["--file", str(source), "--headline", "Chosen"])
    assert headline(args, "ignored") == "Chosen"


def test_headline_uses_file_stem(tmp_path) -> None:
    source = tmp_path / "Linda.txt"
    source.write_text("ignored", encoding="utf-8")
    args = parser().parse_args(["--file", str(source)])
    assert headline(args, "ignored") == "Linda"


def test_headline_falls_back_to_first_three_words() -> None:
    args = parser().parse_args(["Dette er en lang tekst"])
    assert headline(args, "Dette er en lang tekst") == "Dette er en..."


def test_config_uses_packaged_defaults() -> None:
    args = parser().parse_args(["Korssting"])
    config = config_from_args(args)
    assert config.l_height == 12
    assert config.count == 14.0
    assert config.page_overlap == 4


def test_config_file_can_be_partial(tmp_path) -> None:
    source = tmp_path / "config.toml"
    source.write_text("count = 16\npage_overlap = 5\n", encoding="utf-8")
    args = parser().parse_args(["Korssting", "--config-file", str(source)])
    config = config_from_args(args)
    assert config.count == 16
    assert config.page_overlap == 5
    assert config.l_height == 12


def test_cli_overrides_config_file(tmp_path) -> None:
    source = tmp_path / "config.toml"
    source.write_text("count = 16\n", encoding="utf-8")
    args = parser().parse_args(["Korssting", "--config-file", str(source), "--count", "18"])
    assert config_from_args(args).count == 18
