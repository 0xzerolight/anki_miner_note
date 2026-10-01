"""Build the Anki Miner Note .apkg from src/ and anki_fields.yaml.

Usage: uv run python build/genapkg.py <output.apkg>
"""

import sys
from collections.abc import Sequence
from pathlib import Path

import genanki
import yaml

from samples import SAMPLES, Sample, note_values

BUILD_DIR = Path(__file__).resolve().parent
SRC_DIR = BUILD_DIR.parent / "src"

# Never change these: Anki matches note types by ID on import. Never reuse Lapis's 1667218449922 either,
# or an import merges into the user's Lapis.
MODEL_ID = 1734918266473
DECK_ID = 1734918266474
MODEL_NAME = "Anki Miner Note"
DECK_NAME = "Anki Miner Note"


def load_fields() -> list[dict]:
    with (BUILD_DIR / "anki_fields.yaml").open(encoding="utf-8") as fields_file:
        return yaml.safe_load(fields_file)


def field_names() -> list[str]:
    return [field["name"] for field in load_fields()]


def build_model() -> genanki.Model:
    return genanki.Model(
        MODEL_ID,
        MODEL_NAME,
        fields=load_fields(),
        templates=[
            {
                "name": "Mining",
                "qfmt": (SRC_DIR / "front.html").read_text(encoding="utf-8"),
                "afmt": (SRC_DIR / "back.html").read_text(encoding="utf-8"),
            }
        ],
        css=(SRC_DIR / "styling.css").read_text(encoding="utf-8"),
    )


def build_package(output: Path, samples: Sequence[Sample] = SAMPLES, model: genanki.Model | None = None) -> Path:
    """Write the .apkg (note type + example deck of the shippable samples) and return its path."""
    model = model or build_model()
    names = [field["name"] for field in model.fields]
    deck = genanki.Deck(DECK_ID, DECK_NAME)
    for sample in samples:
        if not sample.ship:
            continue
        deck.add_note(
            genanki.Note(
                model=model,
                fields=note_values(sample, names),
                tags=["anki_miner_note::sample"],
                guid=genanki.guid_for("anki_miner_note", sample.name),
            )
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    genanki.Package(deck).write_to_file(str(output))
    return output


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: uv run python build/genapkg.py <output.apkg>", file=sys.stderr)
        return 1
    print(build_package(Path(argv[1])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
