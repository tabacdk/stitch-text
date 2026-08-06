from __future__ import annotations

import tomllib
from dataclasses import dataclass, fields
from importlib import resources
from pathlib import Path
from typing import Any, Self


@dataclass(frozen=True)
class Config:
    l_height: int
    low_threshold: int
    high_threshold: int
    phase_steps: int
    tracking: int
    padding: int
    center: bool
    line_height: float
    paragraph_height: float
    cell_size: int
    count: float
    margin_mm: float
    letter_size: bool
    page_overlap: int
    overlap_mark: bool
    grid: bool
    baseline: bool

    @classmethod
    def from_mapping(cls, values: dict[str, Any]) -> Self:
        names = {field.name for field in fields(cls)}
        unknown = sorted(set(values) - names)
        if unknown:
            joined = ", ".join(unknown)
            raise ValueError(f"unknown config key(s): {joined}")
        return cls(**values)


def _read_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as file:
        return tomllib.load(file)


def default_config_values() -> dict[str, Any]:
    default_file = resources.files("stitch_text").joinpath("defaults.toml")
    return tomllib.loads(default_file.read_text(encoding="utf-8"))


def load_config(config_file: Path | None = None) -> Config:
    values = default_config_values()
    if config_file is not None:
        values.update(_read_toml(config_file))
    return Config.from_mapping(values)
