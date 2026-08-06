#!/usr/bin/env bash

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/uv-cache}"

run() {
    printf '+ %q' "$@"
    printf '\n'
    "$@"
}

run uv sync --locked --dev
run uv run pytest
run uv run ruff format --check .
run uv run ruff check .
run uv run ty check src
run rm -rf dist
run uv build
