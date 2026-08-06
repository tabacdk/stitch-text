#!/usr/bin/env bash

set -eu

uv sync
uv run pytest
uv run ty check
uv run ruff check
