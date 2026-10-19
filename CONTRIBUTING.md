# Contributing to Anki Miner Note

Thanks for helping out. Anki Miner Note is a solo-maintained note type for [Anki Miner](https://github.com/0xzerolight/anki_miner), forked from [Lapis](https://github.com/donkuri/lapis): one card for every language Anki Miner mines. Contributions of any size are welcome - bug reports, fixes, a better layout for a language, doc improvements.

## Before you start

- Bugs and feature requests: open an [Issue](https://github.com/0xzerolight/anki_miner_note/issues) using the appropriate template.
- General questions and chat: use [Discussions](https://github.com/0xzerolight/anki_miner_note/discussions) or [Discord](https://discord.com/invite/aDtQyZzUVP).
- Security vulnerabilities: see [SECURITY.md](SECURITY.md). Do not open a public issue.
- Code of Conduct: see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Development setup

```bash
git clone https://github.com/0xzerolight/anki_miner_note.git
cd anki_miner_note

uv sync                              # genanki, pyyaml, anki, playwright, pytest, ruff
uv run playwright install chromium   # the render tests drive Chromium
```

The project is managed with [uv](https://docs.astral.sh/uv/) and needs Python 3.11 or newer. Build the `.apkg` with:

```bash
uv run python build/genapkg.py dist/Anki-Miner-Note-dev.apkg
```

The font tests assert the Noto faces CI installs (`sudo apt-get install -y fonts-noto-core fonts-noto-cjk`).

## Workflow

1. Fork the repo and create a branch from `main`.
2. Keep PRs focused - one feature or fix per PR.
3. Run `scripts/check.sh`. See [Tests](#tests).
4. Add an entry under `## [Unreleased]` in [CHANGELOG.md](CHANGELOG.md).
5. Open the PR against `main`. The PR template will populate automatically.

## Code style

- **ruff** for linting and formatting, 120-character lines: `uv run ruff check .` and `uv run ruff format .`.
- The card is mostly Lapis. Additions carry the `amn-` prefix or an `Anki Miner Note` comment, and the CSS ends with the `ANKI MINER NOTE: LANGUAGES` and `EXTRAS` sections. Keep Lapis's own code recognisable so upstream fixes still merge.
- Field order is a contract: append a new field at the end of both `build/anki_fields.yaml` and `build/fields.lock`, and never rename, remove or reorder one. `test_fields_are_lock_plus_appended` enforces it.
- Conventional Commits are preferred (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, `ci:`).

## Tests

`scripts/check.sh` is the gate: `ruff check`, `ruff format --check`, `pytest`, then the Anki Miner mapping check. It runs every step, prints `CHECK GREEN` or `CHECK RED`, and exits nonzero on a failure.

```bash
# What CI runs, and what to run before pushing
scripts/check.sh

# Single file (the contract tests need no browser)
uv run pytest -q tests/test_contract.py
```

- `tests/cards.py` renders notes with Anki's own template engine (the pinned `anki` package), and `tests/conftest.py` opens each rendered side in Playwright Chromium.
- Tests marked `render` drive Chromium and are slower; they write back-of-card screenshots to `test-artifacts/`, which CI uploads as `card-screenshots`. The screenshots are for review, never pixel-diffed.
- Every `Sample` in `build/samples.py` holds what Anki Miner writes for its language, markup included. A sample is a test fixture first; `ship=False` keeps it out of the example deck.
- The mapping check (`scripts/check_anki_miner_mapping.py`) runs under an Anki Miner checkout's interpreter: `ANKI_MINER_PYTHON` points at it, and `SKIP_ANKI_MINER_MAPPING=1` skips it, as CI does.

## Changelog

Add an entry under `## [Unreleased]` in `CHANGELOG.md` using the [Keep a Changelog](https://keepachangelog.com/) sections (Added / Changed / Fixed / Removed). Entries say what changed on the card, not the implementation detail.
