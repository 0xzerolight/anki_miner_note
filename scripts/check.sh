#!/usr/bin/env bash
# Definition-of-Done gate. Redirect the output to a file and read the exit code in a separate step;
# piping it through tail hides a red result.
set -uo pipefail
cd "$(dirname "$0")/.."

status=0
run() {
  echo "==> $*"
  "$@" || status=1
}

run uv run ruff check .
run uv run ruff format --check .
run uv run pytest -q

mapping_python="${ANKI_MINER_PYTHON:-$HOME/Projects/anki_miner/.venv/bin/python}"
if [[ "${SKIP_ANKI_MINER_MAPPING:-0}" != "1" && -x "$mapping_python" ]]; then
  echo "==> anki_miner mapping check ($mapping_python)"
  "$mapping_python" scripts/check_anki_miner_mapping.py
  rc=$?
  if [[ $rc -eq 1 ]]; then status=1; elif [[ $rc -eq 2 ]]; then echo "(mapping check skipped)"; fi
else
  echo "==> anki_miner mapping check skipped"
fi

if [[ $status -eq 0 ]]; then echo "CHECK GREEN"; else echo "CHECK RED"; fi
exit $status
