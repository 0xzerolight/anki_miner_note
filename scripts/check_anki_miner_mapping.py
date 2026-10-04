#!/usr/bin/env python3
"""Check that Anki Miner's "Fill in automatically" maps this note type for every mining language.

Run it with Anki Miner's interpreter:
    ~/Projects/anki_miner/.venv/bin/python scripts/check_anki_miner_mapping.py
Exit 0: every language maps through the Anki Miner Note preset. 1: a regression. 2: anki_miner not installed (skip).
"""

import sys
from pathlib import Path

LOCK = Path(__file__).resolve().parent.parent / "build" / "fields.lock"
CORE_KEYS = (
    "word",
    "sentence",
    "definition",
    "glossary",
    "picture",
    "audio",
    "expression_audio",
    "expression_reading",
    "sentence_translation",
)


def main() -> int:
    try:
        import anki_miner  # noqa: F401
    except ModuleNotFoundError as exc:
        print(f"SKIP: anki_miner is not installed ({exc})")
        return 2
    # anki_miner is installed: a missing name below is an API change, so let it fail the gate.
    from anki_miner.languages import AVAILABLE_LANGUAGES
    from anki_miner.languages.registry import get_profile
    from anki_miner.services.note_presets import fill_note_type_fields

    fields = LOCK.read_text(encoding="utf-8").split()
    failed = []
    for lang in AVAILABLE_LANGUAGES:
        profile = get_profile(lang)
        fill = fill_note_type_fields(
            fields,
            allow_presets="note_presets" in profile.capabilities,
            extra_specs=profile.extra_card_fields,
        )
        problems = [key for key in CORE_KEYS if not fill.fields.get(key)]
        problems += [spec.placeholder for spec in profile.extra_card_fields if spec.key not in fill.extra_fields]
        if fill.preset is None or fill.preset.id != "anki_miner_note":
            problems.append("must resolve to the Anki Miner Note preset")
        print(f"{lang:4} {'ok' if not problems else 'FAIL ' + ', '.join(problems)}")
        if problems:
            failed.append(lang)
    print(f"{len(AVAILABLE_LANGUAGES) - len(failed)}/{len(AVAILABLE_LANGUAGES)} languages map")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
