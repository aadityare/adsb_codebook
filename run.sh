#!/usr/bin/env sh
cd "$(dirname "$0")" || exit 1
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
  docker compose build -q && docker compose run --rm rq2
else
  echo "Docker not running - using local Python instead."
  [ -d .venv ] || python3 -m venv .venv
  .venv/bin/python -m pip install -q -r requirements.txt && .venv/bin/python src/main.py
fi
