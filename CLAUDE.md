# CLAUDE.md

Anki Miner Note: a multilingual Anki mining note type for Anki Miner, based on Lapis (donkuri/lapis). GPL-3.0. Private repo.

- Spec: `docs/specs/2026-10-01-anki-miner-note-design.md`. Plan: `docs/plans/2026-10-01-anki-miner-note-v1.md`.
- Setup: `uv sync && uv run playwright install chromium`.
- Build: `uv run python build/genapkg.py dist/Anki-Miner-Note-dev.apkg`.
- Gate: `scripts/check.sh > check.log 2>&1`, then read the exit code in a separate step. Never pipe it through tail.
- Fields are append-only: add new ones at the end of `build/anki_fields.yaml` and `build/fields.lock`, and never rename, remove or reorder one. `MODEL_ID` in `build/genapkg.py` never changes.
- Field names follow Anki Miner's `CardFieldSpec.placeholder` values so "Fill in automatically" maps them; `scripts/check_anki_miner_mapping.py` checks it.
- `upstream` is donkuri/lapis, fetch only. Cherry-pick fixes; don't merge wholesale.
- Making the repo public is the owner's decision.
