# Anki Miner Note v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn this Lapis checkout into "Anki Miner Note": one Anki note type that renders well for every Anki Miner mining language, shipped as a tested `.apkg`.

**Architecture:**
- Lapis's three template files (`src/front.html`, `src/back.html`, `src/styling.css`) are edited in place.
- Lapis's genanki build (`build/genapkg.py` + `build/anki_fields.yaml`) is kept and made importable.
- Tests render real cards with Anki's own Python package (the real template engine) and inspect them in Playwright Chromium.
- Language-specific behaviour comes from three things:
  - a root `lang` attribute, taken from a `Language` field or inferred by a small script;
  - CSS `:lang()` rules;
  - optional extra fields, wrapped in `{{#Field}}` sections.

**Tech Stack:**
- Python 3.11+ with uv.
- genanki 0.13.1, PyYAML 6.0.3.
- anki 26.9.3 (pylib).
- Playwright 1.63.0 (Chromium), pytest 9.1.1, ruff 0.16.9.
- GitHub Actions: checkout v7, setup-uv v10.2.0 (an exact tag: setup-uv publishes no floating major tags since v8), upload-artifact v7, softprops/action-gh-release v3.

**Spec:** `docs/specs/2026-10-01-anki-miner-note-design.md` (read it first; this plan argues from it).

## Global Constraints

- **Note type name:** `Anki Miner Note`.
- **IDs:** model ID `1734918266473`, deck ID `1734918266474`. They are never changed. Lapis's model ID `1667218449922` must never be used.
- **Fields:** 46 fields, in the spec §2 order.
  - The 22 Lapis names are byte-exact.
  - Fields are append-only, enforced by `build/fields.lock`.
- **Extras:** the 22 extras carry `collapsed: true`. No field carries a `font` key.
- **Language:**
  - The root element of both templates is `<div id="lapis" lang="{{text:Language}}">`.
  - No `lang="ja"` remains anywhere in `src/`.
- **Fonts:** system fonts only; no font files are bundled.
- **Empty extras:** an empty extra field produces no element.
- **Labels:** chip labels are short lowercase English words.
- **License:** GPL-3.0 (the `LICENSE` file stays). Lapis is credited in the README.
- **Gate:**
  - `scripts/check.sh` is the Definition-of-Done gate.
  - Redirect its output to a file and read the exit code in a separate step.
  - Commits are conventional: subject ≤72 chars, no `Co-Authored-By` trailers.
- **Workflow:**
  - Every task runs on its own git worktree under `.worktrees/` (ignored via `.git/info/exclude`).
  - Merge to `main` with `--ff-only` when green, then push to `origin`.
  - Never push to `upstream` (its push URL is `DISABLED`).

## Review Focus

1. **Fields that already carry markup from Anki Miner:**
   - RTL fields arrive as `<div dir="rtl" lang="ar">…</div>`.
   - A Chinese sentence arrives as `<span lang="zh-Hans">…</span>`.
   - Pinyin arrives as tone-coloured `<span style="color:…">`.

   The markup must render as markup, inference must read plain text, and the inner `lang` must survive and pick its own fonts. `Language` stays empty in Anki Miner output today. Tests: Task 3 (`test_anki_miner_inner_lang_survives`), Task 4 (`test_inner_lang_span_takes_its_region_fonts`) and Task 5 (`test_pinyin_keeps_tone_colour_markup`).
2. **Messy `Language` values** (`" de "`, `"ZH-HANT"`): they are trimmed and matched case-insensitively. Tests: Task 3 (`test_language_field_is_trimmed`) and Task 4 (`test_language_tag_matches_case_insensitively`).
3. **Long unbreakable text at phone width** (a German compound, a Thai sentence with no spaces): it must wrap, never widen the card. Test: Task 4 (`test_no_horizontal_overflow_on_mobile`).
4. **Japanese regression:** a Japanese card with an empty `Language` must still be tagged `ja`, and keep Lapis's furigana and pitch graph. A Japanese sentence with no kana (大丈夫？) is still tagged `ja` through its reading. Tests: Task 2 (`test_japanese_back_keeps_lapis_furigana_and_pitch`) and Task 3 (`test_root_lang`, including the `ja_kanji` sample).
5. **Languages with no extras** (en, fi, tr, …): the extras area takes no space and leaves no stray labels. Test: Task 5 (`test_no_extras_take_no_space`).

---

### Task 1: Toolchain, identity and the field contract

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `build/samples.py`, `build/fields.lock`, `tests/test_contract.py`
- Modify: `build/genapkg.py` (rewrite), `build/anki_fields.yaml` (rewrite)
- Delete: `build/requirements.txt`, `build/example_card.csv`, `build/media_files/` (samples carry no media)

**Interfaces:**
- Produces, in `build/genapkg.py`:
  - constants: `MODEL_ID: int`, `DECK_ID: int`, `MODEL_NAME: str`, `DECK_NAME: str`;
  - `load_fields() -> list[dict]`;
  - `field_names() -> list[str]`;
  - `build_model() -> genanki.Model`;
  - `build_package(output: Path, samples: Sequence[Sample] = SAMPLES, model: genanki.Model | None = None) -> Path`.
- Produces, in `build/samples.py`:
  - `Sample(name: str, expected_lang: str, fields: Mapping[str, str], ship: bool = True)`;
  - `SAMPLES: tuple[Sample, ...]`, `SAMPLES_BY_NAME: dict[str, Sample]`, `EXTRAS: tuple[str, ...]` (the 22 extra field names, in order);
  - `note_values(sample, names) -> list[str]`.
- Test import path: pytest's `pythonpath = ["build", "tests"]`, so tests write `import genapkg` and `from samples import ...`.

- [ ] **Step 1: Create the worktree**

```bash
cd ~/Projects/anki_miner_note
git worktree add .worktrees/task1 -b feat/toolchain-fields
cd .worktrees/task1
```

- [ ] **Step 2: Add `pyproject.toml` and `.gitignore`, sync**

`pyproject.toml`:

```toml
[project]
name = "anki-miner-note"
version = "0.1.0"
description = "Multilingual Anki mining note type for Anki Miner, based on Lapis"
requires-python = ">=3.11"
license = "GPL-3.0-only"
dependencies = []

[dependency-groups]
dev = [
    "genanki==0.13.1",
    "pyyaml==6.0.3",
    "anki==26.9.3",
    "playwright==1.63.0",
    "pytest==9.1.1",
    "ruff==0.16.9",
]

[tool.uv]
package = false

[tool.pytest.ini_options]
pythonpath = ["build", "tests"]
testpaths = ["tests"]
markers = ["render: renders cards in Chromium (slower)"]

[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.ruff.lint.isort]
known-first-party = ["cards", "genapkg", "samples"]
```

`.gitignore`:

```gitignore
.venv/
__pycache__/
dist/
test-artifacts/
check.log
```

Run: `uv sync && uv run playwright install chromium`
Expected: both finish without errors, and `uv.lock` is created.

- [ ] **Step 3: Write the failing contract tests**

`tests/test_contract.py`:

```python
"""Static contract of the note type: identity, field list, template references."""

import re
from pathlib import Path

import genapkg
from samples import EXTRAS

ROOT = Path(__file__).resolve().parent.parent
LAPIS_MODEL_ID = 1667218449922

LAPIS_CORE = (
    "Expression", "ExpressionFurigana", "ExpressionReading", "ExpressionAudio", "SelectionText",
    "MainDefinition", "DefinitionPicture", "Sentence", "SentenceFurigana", "SentenceAudio", "Picture",
    "Glossary", "Hint", "IsWordAndSentenceCard", "IsClickCard", "IsSentenceCard", "IsAudioCard",
    "PitchPosition", "PitchCategories", "Frequency", "FreqSort", "MiscInfo",
)
ADDED_CORE = ("SentenceTranslation", "Language")
ANKI_SPECIAL_FIELDS = {"FrontSide", "Tags", "Type", "Deck", "Subdeck", "Card", "CardFlag", "CardID"}
TEMPLATE_REF = re.compile(r"\{\{([#^/]?)([^{}]+?)\}\}")


def template_text(name: str) -> str:
    return (ROOT / "src" / name).read_text(encoding="utf-8")


def template_field_refs(text: str) -> set[str]:
    """Field names a template uses, with filters stripped ({{furigana:X}} -> X)."""
    return {body.split(":")[-1].strip() for _, body in TEMPLATE_REF.findall(text)}


def test_model_identity():
    assert genapkg.MODEL_ID == 1734918266473
    assert genapkg.DECK_ID == 1734918266474
    assert genapkg.MODEL_ID != LAPIS_MODEL_ID
    assert genapkg.MODEL_NAME == "Anki Miner Note"


def test_field_layout():
    names = genapkg.field_names()
    assert tuple(names[:22]) == LAPIS_CORE
    assert tuple(names[22:24]) == ADDED_CORE
    assert tuple(names[24:46]) == EXTRAS
    assert len(set(names)) == len(names)


def test_fields_are_lock_plus_appended():
    lock = (ROOT / "build" / "fields.lock").read_text(encoding="utf-8").split()
    names = genapkg.field_names()
    assert names[: len(lock)] == lock, "fields are append-only: never rename, remove or reorder one"


def test_extras_collapsed_and_no_editor_font():
    fields = {field["name"]: field for field in genapkg.load_fields()}
    for name in EXTRAS:
        assert fields[name].get("collapsed") is True, name
    for field in fields.values():
        assert "font" not in field, field["name"]


def test_template_references_exist():
    known = set(genapkg.field_names()) | ANKI_SPECIAL_FIELDS
    for name in ("front.html", "back.html"):
        unknown = template_field_refs(template_text(name)) - known
        assert not unknown, f"{name} references unknown fields {sorted(unknown)}"


def test_package_builds(tmp_path):
    output = genapkg.build_package(tmp_path / "anki-miner-note.apkg")
    assert output.stat().st_size > 0
```

- [ ] **Step 4: Run them and watch them fail**

Run: `uv run pytest tests/test_contract.py -v`
Expected: FAIL. Either `genapkg` can't be imported (Lapis's script reads `sys.argv` at import time) or the assertions on ID and fields fail.

- [ ] **Step 5: Rewrite `build/anki_fields.yaml`**

```yaml
# Field order is a contract: append new fields at the end, never rename, remove or reorder.
# build/fields.lock pins the shipped list.
# Lapis core (names byte-exact, so Lapis presets and Yomitan setups keep working)
- name: Expression
  size: 50
- name: ExpressionFurigana
- name: ExpressionReading
- name: ExpressionAudio
  size: 10
- name: SelectionText
- name: MainDefinition
- name: DefinitionPicture
  size: 15
- name: Sentence
  size: 20
- name: SentenceFurigana
  size: 20
- name: SentenceAudio
  size: 10
- name: Picture
- name: Glossary
- name: Hint
- name: IsWordAndSentenceCard
- name: IsClickCard
- name: IsSentenceCard
- name: IsAudioCard
- name: PitchPosition
- name: PitchCategories
- name: Frequency
- name: FreqSort
- name: MiscInfo
  size: 15
# Added core
- name: SentenceTranslation
- name: Language
# Per-language extras, named after Anki Miner's CardFieldSpec placeholders
- name: Pinyin
  collapsed: true
- name: Jyutping
  collapsed: true
- name: Traditional
  collapsed: true
- name: MeasureWord
  collapsed: true
- name: Hanja
  collapsed: true
- name: HanViet
  collapsed: true
- name: Gender
  collapsed: true
- name: Article
  collapsed: true
- name: Plural
  collapsed: true
- name: PartOfSpeech
  collapsed: true
- name: AspectPair
  collapsed: true
- name: Root
  collapsed: true
- name: Binyan
  collapsed: true
- name: Transliteration
  collapsed: true
- name: Romanization
  collapsed: true
- name: Colloquial
  collapsed: true
- name: PresentStem
  collapsed: true
- name: Classifier
  collapsed: true
- name: Affixes
  collapsed: true
- name: Formal
  collapsed: true
- name: Grammar
  collapsed: true
- name: Segmentation
  collapsed: true
```

- [ ] **Step 6: Write `build/fields.lock`**

One name per line, in order: the 46 names above. Generate it after Step 8 has rewritten `genapkg`. Lapis's version exits at import time, and its usage line would land in the lock:

```bash
uv run python -c "import sys; sys.path.insert(0, 'build'); import genapkg; print('\n'.join(genapkg.field_names()))" > build/fields.lock
```

- [ ] **Step 7: Write `build/samples.py`**

```python
"""Sample notes: the example deck shipped in the .apkg, and the render-test fixtures.

Each sample holds what Anki Miner writes for its language, markup included:
- RTL word and sentence fields arrive wrapped in <div dir="rtl" lang="…">;
- a Chinese sentence arrives in <span lang="zh-Hans|zh-Hant">;
- Pinyin and Jyutping arrive as tone-coloured spans.

``expected_lang`` is the root ``lang`` once the template's language script has run
("" = no tag).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

GERESH = "\u05f3"  # HEBREW PUNCTUATION GERESH, as Anki Miner writes it in he gender labels


@dataclass(frozen=True)
class Sample:
    name: str
    expected_lang: str
    fields: Mapping[str, str]
    ship: bool = True  # False keeps a test-only fixture out of the example deck


def note_values(sample: Sample, names: Sequence[str]) -> list[str]:
    """The sample's field values in note-type order; unknown field names are an error."""
    unknown = set(sample.fields) - set(names)
    if unknown:
        raise ValueError(f"{sample.name}: unknown fields {sorted(unknown)}")
    return [sample.fields.get(name, "") for name in names]


EXTRAS = (
    "Pinyin", "Jyutping", "Traditional", "MeasureWord", "Hanja", "HanViet", "Gender", "Article", "Plural",
    "PartOfSpeech", "AspectPair", "Root", "Binyan", "Transliteration", "Romanization", "Colloquial",
    "PresentStem", "Classifier", "Affixes", "Formal", "Grammar", "Segmentation",
)

# Shipped in the example deck: the spec's 14 script groups. de_compound, id, en and all_extras are test-only.
# Like Anki Miner today, most samples leave Language empty: the root lang then comes from the lang="…"
# Anki Miner writes inside the word or sentence, else from the script of the text.
SAMPLES: tuple[Sample, ...] = (
    Sample("ja", "ja", {
        "Expression": "十中八九",
        "ExpressionFurigana": "十中八九[じっちゅうはっく]",
        "ExpressionReading": "じっちゅうはっく",
        "Sentence": "<b>十中八九</b>、彼が犯人だ。",
        "SentenceFurigana": "<b>十中八九[じっちゅうはっく]</b>、 彼[かれ]が 犯人[はんにん]だ。",
        "MainDefinition": "in 8 or 9 cases out of ten; in all probability",
        "PitchPosition": "5",
        "Frequency": "JPDB: 23154",
        "FreqSort": "23154",
        "MiscInfo": "Sample · Episode 4",
    }),
    Sample("ja_kanji", "ja", {
        "Expression": "大丈夫",
        "ExpressionReading": "だいじょうぶ",
        "Sentence": "<b>大丈夫</b>？",
        "MainDefinition": "all right; OK",
    }, ship=False),
    Sample("zh_hans", "zh-Hans", {
        "Expression": "骨头",
        "Sentence": '<span lang="zh-Hans">他把<b>骨头</b>扔给了狗。</span>',
        "SentenceTranslation": "He threw the bone to the dog.",
        "MainDefinition": "bone",
        "Pinyin": '<span style="color: #e30000">gǔ</span><span style="color: #888888">tou</span>',
        "Traditional": "骨頭",
        "MeasureWord": "根 gēn",
        "FreqSort": "4210",
    }),
    Sample("zh_hant", "zh-Hant", {
        "Expression": "直接",
        "Sentence": '<span lang="zh-Hant">他<b>直接</b>回家了。</span>',
        "MainDefinition": "direct; immediate",
        "Pinyin": '<span style="color: #02b31c">zhí</span><span style="color: #1510f0">jiē</span>',
    }),
    Sample("yue", "zh-Hant", {
        "Expression": "嘢",
        "Sentence": '<span lang="zh-Hant">你食咗<b>嘢</b>未呀？</span>',  # yue_card_lang is always zh-Hant
        "MainDefinition": "thing; stuff",
        "Jyutping": '<span style="color: #e30000">je5</span>',
        "MeasureWord": "啲 di1",
    }),
    Sample("ko", "ko", {
        "Expression": "학교",
        "Sentence": "매일 <b>학교</b>에 가요.",
        "MainDefinition": "school",
        "Hanja": "學校",
    }),
    Sample("vi", "vi", {
        "Language": "vi",
        "Expression": "trường học",
        "Sentence": "Tôi đi <b>trường học</b> mỗi ngày.",
        "MainDefinition": "school",
        "HanViet": "場學",
    }),
    Sample("de", "", {
        "Expression": "Hund",
        "Sentence": "Der <b>Hund</b> schläft.",
        "SentenceTranslation": "The dog is sleeping.",
        "MainDefinition": "dog",
        "Gender": "der",
        "Plural": "Hunde",
        "PartOfSpeech": "NOUN",
    }),
    Sample("de_compound", "de", {
        "Language": "de",
        "Expression": "Donaudampfschifffahrtsgesellschaftskapitän",
        "Sentence": "Sein Großvater war <b>Donaudampfschifffahrtsgesellschaftskapitän</b>.",
        "MainDefinition": "Danube steamship company captain",
        "Gender": "der",
        "PartOfSpeech": "NOUN",
    }, ship=False),
    Sample("pl", "pl", {
        "Language": "pl",
        "Expression": "stół",
        "Sentence": "Książka leży na <b>stole</b>.",
        "MainDefinition": "table",
        "Gender": "m inan",
        "PartOfSpeech": "NOUN",
    }),
    Sample("ru", "", {
        "Expression": "читать",
        "Sentence": "Я люблю <b>читать</b> по вечерам.",
        "MainDefinition": "to read",
        "AspectPair": "прочитать",
        "PartOfSpeech": "VERB",
    }),
    Sample("el", "el", {
        "Language": "el",
        "Expression": "θάλασσα",
        "Sentence": "Η <b>θάλασσα</b> είναι ήρεμη.",
        "MainDefinition": "sea",
        "Gender": "η",
        "PartOfSpeech": "NOUN",
    }),
    Sample("ar", "ar", {
        "Expression": '<div dir="rtl" lang="ar">كتاب</div>',
        "ExpressionReading": "كِتَاب",
        "Sentence": '<div dir="rtl" lang="ar">قرأت <b>كتابا</b> جميلا.</div>',
        "MainDefinition": "book",
        "Root": "ك ت ب",
        "Grammar": "noun, masculine",
        "Segmentation": "كتاب",
    }),
    Sample("fa", "fa", {
        "Expression": '<div dir="rtl" lang="fa">گفتن</div>',
        "Sentence": '<div dir="rtl" lang="fa">او چیزی <b>نگفت</b>.</div>',
        "MainDefinition": "to say",
        "Romanization": "goftan",
        "Colloquial": "goftan",
        "PresentStem": "گو",
    }),
    Sample("he", "he", {
        "Language": "he",
        "Expression": '<div dir="rtl" lang="he">ספר</div>',
        "ExpressionReading": "סֵפֶר",
        "Sentence": '<div dir="rtl" lang="he">קראתי <b>ספר</b> טוב.</div>',
        "MainDefinition": "book",
        "Transliteration": "sefer",
        "Root": "ס־פ־ר",
        "Gender": "ז" + GERESH,
        "Plural": "ספרים",
        "PartOfSpeech": "NOUN",
    }),
    Sample("th", "th", {
        "Expression": "โรงเรียน",
        "Sentence": "ฉันไป<b>โรงเรียน</b>ทุกวันตั้งแต่เช้าจนเย็นโดยไม่หยุดพักเลย",
        "MainDefinition": "school",
        "Classifier": "แห่ง",
    }),
    Sample("id", "id", {
        "Language": "id",
        "Expression": "bermain",
        "Sentence": "Anak-anak <b>bermain</b> di taman.",
        "MainDefinition": "to play",
        "Root": "main",
        "Affixes": "ber-",
        "Formal": "bermain",
        "PartOfSpeech": "VERB",
    }, ship=False),
    Sample("en", "", {
        "Expression": "serendipity",
        "Sentence": "Meeting her there was pure <b>serendipity</b>.",
        "MainDefinition": "the occurrence of events by chance in a happy way",
    }, ship=False),
    Sample(
        "all_extras",
        "en",
        {
            "Language": "en",
            "Expression": "probe",
            "Sentence": "A <b>probe</b> sentence.",
            **{name: f"x-{name}" for name in EXTRAS},
        },
        ship=False,
    ),
)

SAMPLES_BY_NAME: dict[str, Sample] = {sample.name: sample for sample in SAMPLES}
```

- [ ] **Step 8: Rewrite `build/genapkg.py`**

```python
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

# Never change these: Anki matches note types by ID on import (Lapis is 1667218449922).
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
```

Then delete the Lapis leftovers:

```bash
git rm -q build/requirements.txt build/example_card.csv
git rm -rq build/media_files
```

- [ ] **Step 9: Run the contract tests and watch them pass**

Run: `uv run pytest tests/test_contract.py -v`
Expected: 6 passed. If `test_template_references_exist` fails, Lapis's templates reference something unexpected. Read the message, don't widen `ANKI_SPECIAL_FIELDS` blindly.

- [ ] **Step 10: Lint, then commit**

```bash
uv run ruff format . && uv run ruff check --fix .
git add -A
git commit -m "build: rebrand Lapis build as Anki Miner Note with 46-field contract"
```

- [ ] **Step 11: Merge**

```bash
cd ~/Projects/anki_miner_note && git merge --ff-only feat/toolchain-fields && git push -q origin main
git worktree remove .worktrees/task1 && git branch -d feat/toolchain-fields
```

---

### Task 2: Render harness and the Lapis baseline

**Files:**
- Create: `tests/cards.py`, `tests/conftest.py`, `tests/test_render.py`

**Interfaces:**
- Consumes: `genapkg.build_package`, `genapkg.MODEL_NAME`, `samples.SAMPLES`, `samples.SAMPLES_BY_NAME` (Task 1).
- Produces, in `tests/cards.py`:
  - `CARD_TYPES: tuple[str | None, ...]`;
  - `Rendered(front: str, back: str)`;
  - `render_note(col, fields, card_type=None) -> Rendered`;
  - `page_html(card_html, *, mobile: bool, night: bool) -> str`;
  - `CardPage(page: Page, errors: list[str])`;
  - `import_package(col, apkg: Path) -> None`;
  - `ARTIFACTS: Path`.
- Produces, as fixtures in `tests/conftest.py`:
  - `apkg_path` and `collection` (session-scoped);
  - `browser` (session-scoped);
  - `open_card(fields, *, card_type=None, side="back", mobile=False, night=False) -> CardPage`.

- [ ] **Step 1: Worktree**

```bash
cd ~/Projects/anki_miner_note && git worktree add .worktrees/task2 -b test/render-harness && cd .worktrees/task2 && uv sync
```

- [ ] **Step 2: Write `tests/cards.py`**

```python
"""Render Anki Miner Note cards with Anki's own template engine, for viewing in Chromium."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

import genapkg
from anki.collection import Collection, ImportAnkiPackageOptions, ImportAnkiPackageRequest
from playwright.sync_api import Page

ARTIFACTS = Path(__file__).resolve().parent.parent / "test-artifacts"
CARD_TYPES: tuple[str | None, ...] = (None, "IsWordAndSentenceCard", "IsClickCard", "IsSentenceCard", "IsAudioCard")


@dataclass(frozen=True)
class Rendered:
    front: str
    back: str


@dataclass
class CardPage:
    page: Page
    errors: list[str] = field(default_factory=list)


def import_package(col: Collection, apkg: Path) -> None:
    """Import like a user updating: "Merge note types" on, scheduling off."""
    col.import_anki_package(
        ImportAnkiPackageRequest(
            package_path=str(apkg),
            options=ImportAnkiPackageOptions(merge_notetypes=True, with_scheduling=False),
        )
    )


def render_note(col: Collection, fields: Mapping[str, str], card_type: str | None = None) -> Rendered:
    """Add a note with these fields (plus the card-type toggle) and return its rendered sides, CSS included."""
    note = col.new_note(col.models.by_name(genapkg.MODEL_NAME))
    for name, value in fields.items():
        note[name] = value
    if card_type is not None:
        note[card_type] = "x"
    col.add_note(note, col.decks.id("Render tests"))
    card = note.cards()[0]
    return Rendered(front=card.question(), back=card.answer())


def page_html(card_html: str, *, mobile: bool, night: bool) -> str:
    """Wrap one side the way Anki's reviewer does: html.mobile, body.card(.nightMode), #qa."""
    html_class = "mobile" if mobile else ""
    body_class = "card nightMode night_mode" if night else "card"
    return (
        f'<!doctype html><html class="{html_class}"><head><meta charset="utf-8"></head>'
        f'<body class="{body_class}"><div id="qa">{card_html}</div></body></html>'
    )
```

- [ ] **Step 3: Write `tests/conftest.py`**

```python
from collections.abc import Callable, Iterator, Mapping
from pathlib import Path

import genapkg
import pytest
from anki.collection import Collection
from cards import CardPage, import_package, page_html, render_note
from playwright.sync_api import Browser, sync_playwright

OpenCard = Callable[..., CardPage]


@pytest.fixture(scope="session")
def apkg_path(tmp_path_factory) -> Path:
    return genapkg.build_package(tmp_path_factory.mktemp("dist") / "anki-miner-note-test.apkg")


@pytest.fixture(scope="session")
def collection(apkg_path, tmp_path_factory) -> Iterator[Collection]:
    col = Collection(str(tmp_path_factory.mktemp("collection") / "collection.anki2"))
    import_package(col, apkg_path)
    yield col
    col.close()


@pytest.fixture(scope="session")
def browser() -> Iterator[Browser]:
    with sync_playwright() as playwright:
        chromium = playwright.chromium.launch()
        yield chromium
        chromium.close()


@pytest.fixture
def open_card(browser, collection) -> Iterator[OpenCard]:
    opened = []

    def _open(
        fields: Mapping[str, str],
        *,
        card_type: str | None = None,
        side: str = "back",
        mobile: bool = False,
        night: bool = False,
    ) -> CardPage:
        rendered = render_note(collection, fields, card_type)
        page = browser.new_page(viewport={"width": 390 if mobile else 1280, "height": 900})
        card = CardPage(page)
        page.on("pageerror", lambda exc: card.errors.append(str(exc)))
        page.on(
            "console",
            lambda msg: card.errors.append(msg.text)
            if msg.type == "error" and "Failed to load resource" not in msg.text
            else None,
        )
        page.set_content(page_html(rendered.back if side == "back" else rendered.front, mobile=mobile, night=night))
        opened.append(page)
        return card

    yield _open
    for page in opened:
        page.close()
```

- [ ] **Step 4: Write `tests/test_render.py`** (pins the Lapis baseline)

```python
"""Every sample renders in every card type without script errors; Japanese keeps Lapis's furigana and pitch."""

import warnings

import pytest
from cards import ARTIFACTS, CARD_TYPES
from playwright.sync_api import Error as PlaywrightError
from samples import SAMPLES, SAMPLES_BY_NAME

pytestmark = pytest.mark.render

MODES = [(False, False), (False, True), (True, False), (True, True)]


@pytest.mark.parametrize("sample", SAMPLES, ids=lambda s: s.name)
@pytest.mark.parametrize("card_type", CARD_TYPES, ids=lambda c: c or "word")
@pytest.mark.parametrize("side", ["front", "back"])
@pytest.mark.parametrize("mobile,night", MODES, ids=["desktop-light", "desktop-night", "mobile-light", "mobile-night"])
def test_card_renders_cleanly(open_card, sample, card_type, side, mobile, night):
    card = open_card(sample.fields, card_type=card_type, side=side, mobile=mobile, night=night)
    assert card.errors == []


@pytest.mark.parametrize("sample", SAMPLES, ids=lambda s: s.name)
@pytest.mark.parametrize("mobile,night", MODES, ids=["desktop-light", "desktop-night", "mobile-light", "mobile-night"])
def test_save_screenshots(open_card, sample, mobile, night):
    """Back-of-card screenshots for visual review (CI artifact). A capture failure must not fail the gate."""
    card = open_card(sample.fields, mobile=mobile, night=night)
    ARTIFACTS.mkdir(exist_ok=True)
    mode = f"{'mobile' if mobile else 'desktop'}-{'night' if night else 'light'}"
    try:
        card.page.screenshot(path=ARTIFACTS / f"{sample.name}-{mode}.png", full_page=True)
    except PlaywrightError as exc:
        warnings.warn(f"screenshot {sample.name}-{mode} not captured: {exc}", stacklevel=1)


def test_japanese_back_keeps_lapis_furigana_and_pitch(open_card):
    page = open_card(SAMPLES_BY_NAME["ja"].fields).page
    assert page.locator(".vocab ruby rt").first.inner_text() == "じっちゅうはっく"
    # じ っ ちゅ う は っ く = 7 morae; downstep after the 5th of 7 is nakadaka
    assert page.locator(".pitch .pitch-item > span").count() == 7
    assert page.locator(".pitch .pitch-item.nakadaka").count() == 1
```

- [ ] **Step 5: Run and confirm the baseline is green**

Run: `uv run pytest tests/test_render.py -q`
Expected: all pass (19 samples × 5 card types × 2 sides × 4 modes = 760 cases, plus 76 screenshot captures, plus the Japanese one). This task only pins Lapis's existing behaviour.
- If a case reports a script error, it is a Lapis behaviour with our sample data.
- Read the error and fix the sample if it isn't realistic Anki Miner output. Otherwise stop and report it; never filter it out of `errors`.

- [ ] **Step 6: Commit and merge**

```bash
uv run ruff format . && uv run ruff check --fix .
git add -A && git commit -m "test: render cards with Anki's engine and pin the Lapis baseline"
cd ~/Projects/anki_miner_note && git merge --ff-only test/render-harness && git push -q origin main
git worktree remove .worktrees/task2 && git branch -d test/render-harness
```

---

### Task 3: Language tag and inference

**Files:**
- Modify: `src/front.html`, `src/back.html`
- Create: `tests/test_language.py`

**Interfaces:**
- Consumes: the `open_card` fixture and `SAMPLES` with `expected_lang` (Tasks 1–2).
- Produces:
  - Root `#lapis[lang]` on both sides.
  - Global JS functions `amnInferLang(text: string) -> string` and `amnFieldLang(html: string) -> string`.
  - An inert `<script type="text/plain" id="amn-lang-source">` holding the raw Expression, Sentence, ExpressionFurigana and ExpressionReading. Anki's Browser columns strip script contents, so it doesn't show there.
  - One `<script id="amn-lang">` block per template, identical in both.
  - Tasks 4 and 5 rely on the root `lang`.

- [ ] **Step 1: Worktree**

```bash
cd ~/Projects/anki_miner_note && git worktree add .worktrees/task3 -b feat/language-tag && cd .worktrees/task3 && uv sync
```

- [ ] **Step 2: Write the failing tests**

`tests/test_language.py`:

```python
"""Root lang: the Language field wins (trimmed); otherwise the script infers it from the text."""

import re
from pathlib import Path

import pytest
from samples import SAMPLES, SAMPLES_BY_NAME

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = re.compile(r'<script id="amn-lang">(.*?)</script>', re.S)

INFER_CASES = [
    ("十中八九、彼が犯人だ。", "ja"),
    ("食べる", "ja"),
    ("학교에 가요", "ko"),
    ("โรงเรียน", "th"),
    ("ספר", "he"),
    ("گفتن", "fa"),
    ("کتاب", "fa"),
    ("كتاب", "ar"),
    ("骨头", "zh"),
    ("學校", "zh"),
    ("哈利・波特", "zh"),
    ("ラーメン", "ja"),
    ("Hund", ""),
    ("читать", ""),
    ("θάλασσα", ""),
    ("", ""),
]


def test_lang_script_identical_in_both_templates():
    front = SCRIPT.findall((ROOT / "src" / "front.html").read_text(encoding="utf-8"))
    back = SCRIPT.findall((ROOT / "src" / "back.html").read_text(encoding="utf-8"))
    assert len(front) == 1 and front == back


def test_no_hardcoded_japanese_lang():
    for name in ("front.html", "back.html"):
        assert 'lang="ja"' not in (ROOT / "src" / name).read_text(encoding="utf-8"), name


@pytest.mark.render
@pytest.mark.parametrize("sample", SAMPLES, ids=lambda s: s.name)
@pytest.mark.parametrize("side", ["front", "back"])
def test_root_lang(open_card, sample, side):
    page = open_card(sample.fields, side=side).page
    assert page.get_attribute("#lapis", "lang") == sample.expected_lang


@pytest.mark.render
@pytest.mark.parametrize("raw,expected", [(" de ", "de"), ("ZH-HANT", "ZH-HANT"), ("\tko\n", "ko")])
def test_language_field_is_trimmed(open_card, raw, expected):
    page = open_card({"Expression": "x", "Language": raw}).page
    assert page.get_attribute("#lapis", "lang") == expected


@pytest.mark.render
@pytest.mark.parametrize("text,expected", INFER_CASES)
def test_infer_lang_table(open_card, text, expected):
    page = open_card({"Expression": "x"}).page
    assert page.evaluate("text => amnInferLang(text)", text) == expected


@pytest.mark.render
@pytest.mark.parametrize(
    "html,expected",
    [('<span lang="zh-Hant">他</span>', "zh-Hant"), ('<div dir="rtl" lang="fa">او</div>', "fa"), ("<b>plain</b>", "")],
)
def test_field_lang_reads_anki_miner_tags(open_card, html, expected):
    page = open_card({"Expression": "x"}).page
    assert page.evaluate("html => amnFieldLang(html)", html) == expected


@pytest.mark.render
def test_anki_miner_inner_lang_survives(open_card):
    page = open_card(SAMPLES_BY_NAME["zh_hant"].fields).page
    assert page.locator('#lapis span[lang="zh-Hant"]').count() >= 1
    page = open_card(SAMPLES_BY_NAME["ar"].fields).page
    assert page.locator('#lapis div[dir="rtl"][lang="ar"]').count() >= 1
```

Run: `uv run pytest tests/test_language.py -q`
Expected: FAIL. The script isn't there yet, `lang="ja"` is still hardcoded, and `amnInferLang` is undefined. `test_anki_miner_inner_lang_survives` guards the fixture markup and already passes.

- [ ] **Step 3: Edit `src/front.html`**

Replace lines 1–5:

```html
<div id="lapis">
    <!---------- Header ------------->
    <header style="visibility: hidden"></header>

    <main lang="ja" style="width: 100%;">
```

with:

```html
<div id="lapis" lang="{{text:Language}}">
    <!-- Anki Miner Note: raw word, sentence and reading for the language fallback (see script#amn-lang).
         Inert, and Anki's Browser columns strip script contents. -->
    <script type="text/plain" id="amn-lang-source">{{Expression}} {{Sentence}} {{ExpressionFurigana}} {{ExpressionReading}}</script>
    <!---------- Header ------------->
    <header style="visibility: hidden"></header>

    <main style="width: 100%;">
```

Then delete every remaining ` lang="ja"` attribute in the file. There are seven: the `div`s at Lapis lines 9, 15, 20, 21 (`#hint`), 27 and 34, and the `clickedContent` string at line 57. Use `sed -i 's/ lang="ja"//g' src/front.html` after the edit above, then check with `grep -c 'lang="ja"' src/front.html`, which should print 0.

Insert this block between the closing `</div>` of `#lapis` (line 47) and Lapis's `<script>`:

```html
<script id="amn-lang">
  // Anki Miner Note: language tag. Order: a filled Language field (trimmed); else the first lang="…"
  // Anki Miner wrote inside the word or sentence; else a guess from the script of the text.
  function amnInferLang(text) {
    const rules = [
      [/[\u3041-\u3096\u309d-\u309f\u30a1-\u30fa\u30fd-\u30ff]/, "ja"], // kana, without ・ and ー
      [/[\u1100-\u11ff\u3130-\u318f\uac00-\ud7af]/, "ko"],
      [/[\u0e00-\u0e7f]/, "th"],
      [/[\u0590-\u05ff]/, "he"],
      [/[\u067e\u0686\u0698\u06a9\u06af\u06cc]/, "fa"],
      [/[\u0600-\u06ff\u0750-\u077f]/, "ar"],
      [/[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]/, "zh"],
    ];
    for (const [pattern, lang] of rules) {
      if (pattern.test(text)) return lang;
    }
    return "";
  }

  function amnFieldLang(html) {
    const match = /\blang="([A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*)"/.exec(html);
    return match ? match[1] : "";
  }

  (function amnSetLang() {
    const root = document.getElementById("lapis");
    if (!root) return;
    const given = (root.getAttribute("lang") || "").trim();
    if (given) {
      root.setAttribute("lang", given);
      return;
    }
    const source = document.getElementById("amn-lang-source");
    const fields = source ? source.textContent : "";
    root.setAttribute("lang", amnFieldLang(fields) || amnInferLang(fields));
  })();
</script>
```

- [ ] **Step 4: Edit `src/back.html`**

Replace line 1, `<div id="lapis" lang="ja">`, with:

```html
<div id="lapis" lang="{{text:Language}}">
    <!-- Anki Miner Note: raw word, sentence and reading for the language fallback (see script#amn-lang).
         Inert, and Anki's Browser columns strip script contents. -->
    <script type="text/plain" id="amn-lang-source">{{Expression}} {{Sentence}} {{ExpressionFurigana}} {{ExpressionReading}}</script>
```

Insert the **same** `<script id="amn-lang">…</script>` block, byte-identical, between the closing `</div>` of `#lapis` (after the image modal) and the `<!----------- Scripts ------------>` comment.

- [ ] **Step 5: Run and watch them pass**

Run: `uv run pytest tests/test_language.py tests/test_contract.py -q`
Expected: all pass. The `ja_kanji` sample (kanji-only sentence) is tagged `ja` through its reading. zh_hans, zh_hant and yue take the tag Anki Miner wrote on their sentence.

- [ ] **Step 6: Run the full suite, commit, merge**

```bash
uv run pytest -q && uv run ruff format . && uv run ruff check --fix .
git add -A && git commit -m "feat: tag the card language from Language or infer it from the text"
cd ~/Projects/anki_miner_note && git merge --ff-only feat/language-tag && git push -q origin main
git worktree remove .worktrees/task3 && git branch -d feat/language-tag
```

---

### Task 4: Fonts, direction and wrapping

**Files:**
- Modify: `src/styling.css` (`:root` font variables at lines 31–32; append a section at the end)
- Create: `tests/test_fonts_direction.py`

**Interfaces:**
- Consumes: root `lang` (Task 3), `open_card`, `SAMPLES`.
- Produces, as CSS custom properties: `--latin-serif`, `--latin-sans`, `--cjk-serif`, `--cjk-sans`, `--script-serif`, `--script-sans`, `--font-serif` and `--font-sans`.
  - The composites `--font-serif` and `--font-sans` are declared on `#lapis, #lapis [lang]`.
  - Task 5's CSS uses `var(--font-sans)` and `var(--font-serif)`.

- [ ] **Step 1: Worktree**

```bash
cd ~/Projects/anki_miner_note && git worktree add .worktrees/task4 -b feat/fonts-direction && cd .worktrees/task4 && uv sync
```

- [ ] **Step 2: Write the failing tests**

`tests/test_fonts_direction.py`:

```python
"""Per-language font stacks, right-to-left blocks, Thai line height, no overflow at phone width."""

import pytest
from cards import CARD_TYPES
from samples import SAMPLES, SAMPLES_BY_NAME

pytestmark = pytest.mark.render

REGION_SERIF = {
    "zh": "Noto Serif CJK SC",
    "zh-Hans": "Noto Serif CJK SC",
    "zh-Hant": "Noto Serif CJK TC",
    "yue": "Noto Serif CJK HK",
    "ko": "Noto Serif CJK KR",
}
LAPIS_SERIF = ["Hiragino Mincho ProN", "Noto Serif CJK JP", "Noto Serif JP", "Yu Mincho", "HanaMinA", "HanaMinB", "serif"]


def computed(page, selector: str, prop: str) -> str:
    return page.eval_on_selector(selector, f"e => getComputedStyle(e).{prop}")


def families(page, selector: str) -> list[str]:
    return [name.strip().strip('"') for name in computed(page, selector, "fontFamily").split(",")]


@pytest.mark.parametrize("tag,region_font", REGION_SERIF.items())
def test_cjk_region_stack(open_card, tag, region_font):
    stack = families(open_card({"Expression": "骨", "Language": tag}).page, ".vocab")
    assert region_font in stack
    others = {font for font in REGION_SERIF.values() if font != region_font} | {"Noto Serif CJK JP"}
    assert not others & set(stack), stack
    if tag != "ko":  # Chinese punctuation (“ ” ……) must come from the CJK face
        assert stack.index(region_font) < stack.index("Noto Serif"), stack


def test_japanese_keeps_lapis_serif_stack(open_card):
    """Parity guard: Japanese keeps Lapis's Mincho-first stack, so punctuation and digits stay full-width."""
    page = open_card(SAMPLES_BY_NAME["ja"].fields).page
    assert families(page, ".vocab") == LAPIS_SERIF
    sans = families(page, ".info")
    assert "Noto Sans CJK JP" in sans and not {"Noto Sans CJK SC", "Noto Sans CJK TC", "Noto Sans CJK KR"} & set(sans)


@pytest.mark.parametrize(
    "name,inner_font",
    [("zh_hant", "Noto Serif CJK TC"), ("yue", "Noto Serif CJK TC"), ("zh_hans", "Noto Serif CJK SC")],
)
def test_inner_lang_span_takes_its_region_fonts(open_card, name, inner_font):
    """Anki Miner tags the sentence (<span lang="zh-Hant|zh-Hans">) and leaves Language empty."""
    stack = families(open_card(SAMPLES_BY_NAME[name].fields).page, ".sentence span[lang]")
    assert inner_font in stack
    assert not ({"Noto Serif CJK SC", "Noto Serif CJK TC"} - {inner_font}) & set(stack), stack


@pytest.mark.parametrize(
    "name,first",
    [("ar", "Noto Naskh Arabic"), ("fa", "Noto Naskh Arabic"), ("he", "Noto Serif Hebrew"), ("th", "Noto Serif Thai")],
)
def test_script_faces_lead_for_their_language(open_card, name, first):
    assert families(open_card(SAMPLES_BY_NAME[name].fields).page, ".vocab")[0] == first


def test_language_tag_matches_case_insensitively(open_card):
    family = computed(open_card({"Expression": "直接", "Language": "ZH-HANT"}).page, ".vocab", "fontFamily")
    assert "Noto Serif CJK TC" in family


@pytest.mark.parametrize("name", ["pl", "de", "ru", "el", "en"])
def test_non_cjk_headword_starts_with_a_latin_face(open_card, name):
    family = computed(open_card(SAMPLES_BY_NAME[name].fields).page, ".vocab", "fontFamily")
    first = family.split(",")[0].strip().strip('"')
    assert "CJK" not in first and "Mincho" not in first and "Gothic" not in first, family


@pytest.mark.parametrize("name", ["ar", "fa", "he"])
def test_rtl_blocks(open_card, name):
    fields = SAMPLES_BY_NAME[name].fields
    back = open_card(fields).page
    for selector in (".vocab", ".pitch", ".sentence", ".sentence-alt"):
        assert computed(back, selector, "direction") == "rtl", selector
    assert computed(back, ".main-def", "direction") == "ltr"
    front = open_card(fields, side="front", card_type="IsSentenceCard").page
    assert computed(front, ".front-sentence", "direction") == "rtl"


def test_hint_follows_its_own_text(open_card):
    fields = {**SAMPLES_BY_NAME["he"].fields, "Hint": "Think of a library."}
    assert computed(open_card(fields, side="front").page, "#hint", "direction") == "ltr"


def test_ltr_language_stays_ltr(open_card):
    assert computed(open_card(SAMPLES_BY_NAME["de"].fields).page, ".vocab", "direction") == "ltr"


def test_thai_gets_taller_lines(open_card):
    page = open_card(SAMPLES_BY_NAME["th"].fields).page
    ratio = page.eval_on_selector(
        ".vocab", "e => parseFloat(getComputedStyle(e).lineHeight) / parseFloat(getComputedStyle(e).fontSize)"
    )
    assert ratio >= 1.75


@pytest.mark.parametrize("sample", SAMPLES, ids=lambda s: s.name)
@pytest.mark.parametrize("card_type", CARD_TYPES, ids=lambda c: c or "word")
@pytest.mark.parametrize("side", ["front", "back"])
def test_no_horizontal_overflow_on_mobile(open_card, sample, card_type, side):
    page = open_card(sample.fields, card_type=card_type, side=side, mobile=True).page
    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
```

Run: `uv run pytest tests/test_fonts_direction.py -q`
Expected: FAIL. The region stacks, inner-span fonts, script stacks, RTL blocks, Thai line height and `de_compound` overflow are not implemented yet. `test_japanese_keeps_lapis_serif_stack` is a parity guard and already passes; it must still pass after Step 4.

- [ ] **Step 3: Replace the font variables in `:root`** (`src/styling.css` lines 31–32)

Replace:

```css
  --font-serif: "Hiragino Mincho ProN", "Noto Serif CJK JP", "Noto Serif JP", "Yu Mincho", HanaMinA, HanaMinB, serif;
  --font-sans: "Inter", "SF Pro Display", "Liberation Sans", "Segoe UI", "Hiragino Kaku Gothic ProN", "Noto Sans CJK JP", "Noto Sans JP", "Meiryo", HanaMinA, HanaMinB, sans-serif;
```

with:

```css
  /* Fonts (Anki Miner Note). Latin faces come first, so ł, ş and ő keep one face.
     --cjk-* holds the regional CJK faces (set per language at the end of this file).
     --script-* holds Arabic, Hebrew and Thai faces: per-glyph fallbacks, leading for ar, fa, he and th.
     --font-serif and --font-sans are composed on #lapis; customise the parts here.
     The per-language stacks are in the LANGUAGES section at the end of this file. */
  --latin-serif: "Noto Serif", "Source Serif 4", Georgia, "Times New Roman";
  --latin-sans: "Inter", "SF Pro Display", "Segoe UI", "Noto Sans", "Liberation Sans";
  --cjk-serif: "Hiragino Mincho ProN", "Noto Serif CJK JP", "Noto Serif JP", "Yu Mincho", HanaMinA, HanaMinB;
  --cjk-sans: "Hiragino Kaku Gothic ProN", "Noto Sans CJK JP", "Noto Sans JP", "Meiryo", HanaMinA, HanaMinB;
  --script-serif: "Noto Naskh Arabic", "Noto Serif Hebrew", "Noto Serif Thai";
  --script-sans: "Noto Sans Arabic", "Noto Sans Hebrew", "Noto Sans Thai", "Leelawadee UI", Tahoma;
```

- [ ] **Step 4: Append the language section to the end of `src/styling.css`**

```css

/*
 *  ANKI MINER NOTE: LANGUAGES
 *  The root #lapis carries lang (from the Language field or inferred by script#amn-lang).
 */

/* Compose the stacks where the language is known. Custom properties inherit already substituted,
   so they must be composed on the element whose --cjk-* is set, not on :root. */
#lapis,
#lapis [lang] {
  --font-serif: var(--latin-serif), var(--cjk-serif), var(--script-serif), serif;
  --font-sans: var(--latin-sans), var(--cjk-sans), var(--script-sans), sans-serif;
}

/* Japanese keeps Lapis's stacks: Mincho first, so punctuation and digits in Japanese text stay full-width. */
#lapis:lang(ja),
#lapis [lang]:lang(ja) {
  --font-serif: var(--cjk-serif), serif;
  --font-sans: "Inter", "SF Pro Display", "Liberation Sans", "Segoe UI", var(--cjk-sans), sans-serif;
}

/* Chinese and Cantonese: CJK faces lead the serif stack, so “ ” …… —— keep their full-width forms.
   Sans stays Latin-first, so pinyin and jyutping use a Latin face. */
#lapis:is(:lang(zh), :lang(yue)),
#lapis [lang]:is(:lang(zh), :lang(yue)) {
  --font-serif: var(--cjk-serif), var(--latin-serif), serif;
}

/* Arabic, Persian, Hebrew and Thai faces lead for their own language. Otherwise Latin faces that also
   cover those scripts (Times New Roman, Segoe UI, Tahoma) would take the glyphs first. */
:lang(ar),
:lang(fa) {
  --script-serif: "Noto Naskh Arabic", "Geeza Pro", "Traditional Arabic";
  --script-sans: "Noto Sans Arabic", "Geeza Pro", "Segoe UI";
}

:lang(he) {
  --script-serif: "Noto Serif Hebrew", "Times New Roman";
  --script-sans: "Noto Sans Hebrew", "Arial Hebrew", "Segoe UI";
}

:lang(th) {
  --script-serif: "Noto Serif Thai", "Thonburi", "Leelawadee UI";
  --script-sans: "Noto Sans Thai", "Thonburi", "Leelawadee UI";
}

#lapis:is(:lang(ar), :lang(fa), :lang(he), :lang(th)),
#lapis [lang]:is(:lang(ar), :lang(fa), :lang(he), :lang(th)) {
  --font-serif: var(--script-serif), var(--latin-serif), serif;
  --font-sans: var(--script-sans), var(--latin-sans), sans-serif;
}

/* Regional CJK faces: the same Han codepoint is drawn differently in each region.
   zh-Hant and yue come after zh, which also matches them. */
:lang(zh) {
  --cjk-serif: "Songti SC", "Noto Serif CJK SC", "Noto Serif SC", SimSun;
  --cjk-sans: "PingFang SC", "Noto Sans CJK SC", "Noto Sans SC", "Microsoft YaHei";
}

:lang(zh-Hant) {
  --cjk-serif: "Songti TC", "Noto Serif CJK TC", "Noto Serif TC", PMingLiU;
  --cjk-sans: "PingFang TC", "Noto Sans CJK TC", "Noto Sans TC", "Microsoft JhengHei";
}

:lang(yue),
:lang(zh-HK) {
  --cjk-serif: "Noto Serif CJK HK", "Noto Serif HK", "Songti TC";
  --cjk-sans: "PingFang HK", "Noto Sans CJK HK", "Noto Sans HK", "Microsoft JhengHei";
}

:lang(ko) {
  --cjk-serif: "AppleMyungjo", "Noto Serif CJK KR", "Noto Serif KR", Batang;
  --cjk-sans: "Apple SD Gothic Neo", "Noto Sans CJK KR", "Noto Sans KR", "Malgun Gothic";
}

/* Anki Miner tags the language inside a field (<span lang="zh-Hant">, <div lang="ar">). font-family
   inherits as an already-computed list, so re-declare it there to pick up that language's stack. */
:is(.front-vocab, .front-sentence, #hint, .vocab, .sentence, .sentence-alt) [lang] {
  font-family: var(--font-serif);
}

/* Right-to-left mining languages: the word, its reading and the sentence run RTL.
   The definition box keeps the document direction, because its dictionaries are usually English. */
:is(.front-vocab, .front-sentence, .vocab, .pitch, .sentence, .sentence-alt):is(:lang(ar), :lang(fa), :lang(he)) {
  direction: rtl;
  unicode-bidi: isolate;
}

/* Thai stacks vowels and tone marks above and below the line. */
:is(.front-vocab, .front-sentence, #hint, .vocab, .sentence, .sentence-alt):lang(th) {
  line-height: 1.8;
}

/* Long unbroken words (German compounds, unspaced Thai) wrap instead of widening the card. */
.front-vocab,
.front-sentence,
#hint,
.vocab,
.sentence,
.sentence-alt {
  overflow-wrap: anywhere;
}
```

Then give both front `#hint` divs `dir="auto"`, so a hint follows its own text. One is the word-and-sentence hint; the other is the user's Hint field, often English on an Arabic card:

```bash
sed -i 's/<div id="hint">/<div id="hint" dir="auto">/g' src/front.html
grep -c 'id="hint" dir="auto"' src/front.html   # 2
```

- [ ] **Step 5: Run and watch them pass**

Run: `uv run pytest tests/test_fonts_direction.py -q`
Expected: all pass.
- If `test_no_horizontal_overflow_on_mobile` still fails for a card, find the widest element with `page.evaluate("[...document.querySelectorAll('#lapis *')].filter(e => e.scrollWidth > document.documentElement.clientWidth).map(e => e.className || e.id)")`.
- Add `overflow-wrap: anywhere` to that element's rule. Don't add `overflow: hidden`, which would clip the text.

- [ ] **Step 6: Full suite, commit, merge**

```bash
uv run pytest -q && uv run ruff format . && uv run ruff check --fix .
git add -A && git commit -m "feat: per-language font stacks, RTL blocks and wrapping"
cd ~/Projects/anki_miner_note && git merge --ff-only feat/fonts-direction && git push -q origin main
git worktree remove .worktrees/task4 && git branch -d feat/fonts-direction
```

---

### Task 5: Per-language extras on the back

**Files:**
- Modify: `src/back.html` (the `.dh-vocab` block at lines 25–43 and both sentence blocks), `src/styling.css` (append), `tests/test_contract.py` (one test)
- Create: `tests/test_extras.py`

**Interfaces:**
- Consumes: `--font-sans` and `--font-serif` (Task 4), root `lang` (Task 3), `open_card`, `SAMPLES`, `samples.EXTRAS` (Task 1).
- Produces:
  - Elements `[data-amn-field="<FieldName>"]`, one per filled extra.
  - Containers `.amn-extras > .amn-readings | .amn-forms | .amn-chips`.
  - Chips `.amn-chip` with `.amn-chip-label`, and `.amn-gender[data-gender]`.
  - `.amn-translation[dir=auto]`.
  - CSS variables `--gender-masc`, `--gender-fem`, `--gender-neut` and `--gender-common`.

- [ ] **Step 1: Worktree**

```bash
cd ~/Projects/anki_miner_note && git worktree add .worktrees/task5 -b feat/extras && cd .worktrees/task5 && uv sync
```

- [ ] **Step 2: Write the failing tests**

Append to `tests/test_contract.py`:

```python
def test_extras_only_inside_their_own_section():
    """An extra is referenced only inside {{#Extra}}…{{/Extra}}, so an empty field leaves no markup."""
    back = template_text("back.html")
    for name in EXTRAS:
        outside = re.sub(r"\{\{#" + name + r"\}\}.*?\{\{/" + name + r"\}\}", "", back, flags=re.S)
        stray = [
            body for prefix, body in TEMPLATE_REF.findall(outside) if not prefix and body.split(":")[-1].strip() == name
        ]
        assert not stray, f"{name} is referenced outside its own section: {stray}"
```

Only value references (no `#`, `^` or `/` prefix) count as stray. So the `{{^Pinyin}}…{{/Pinyin}}` and `{{^Jyutping}}…{{/Jyutping}}` guards added in Step 3 pass; they only suppress the plain reading.

`tests/test_extras.py`:

```python
"""Per-language extras: readings, alternate forms, chips, gender colours, sentence translation."""

import pytest
from samples import EXTRAS, SAMPLES, SAMPLES_BY_NAME

pytestmark = pytest.mark.render

GERESH = "\u05f3"
CHIP_LABELS = {
    "Article": "article", "Gender": "gender", "Plural": "plural", "PartOfSpeech": "pos",
    "MeasureWord": "measure word", "Classifier": "classifier", "AspectPair": "aspect pair", "Root": "root",
    "Binyan": "binyan", "PresentStem": "present stem", "Colloquial": "colloquial", "Formal": "formal",
    "Affixes": "affixes", "Segmentation": "segmentation", "Grammar": "grammar",
}


def css_color(page, value: str) -> str:
    """Resolve a CSS colour expression inside #lapis to the computed rgb() string."""
    return page.evaluate(
        """value => {
            const probe = document.createElement("span");
            probe.style.color = value;
            document.getElementById("lapis").appendChild(probe);
            const color = getComputedStyle(probe).color;
            probe.remove();
            return color;
        }""",
        value,
    )


def test_every_extra_renders_when_filled(open_card):
    page = open_card(SAMPLES_BY_NAME["all_extras"].fields).page
    for name in EXTRAS:
        element = page.locator(f'[data-amn-field="{name}"]')
        assert element.count() == 1, name
        assert f"x-{name}" in element.inner_text(), name
        if name in CHIP_LABELS:
            assert element.locator(".amn-chip-label").inner_text() == CHIP_LABELS[name]


@pytest.mark.parametrize("sample", SAMPLES, ids=lambda s: s.name)
def test_empty_extras_leave_no_element(open_card, sample):
    page = open_card(sample.fields).page
    for name in EXTRAS:
        expected = 1 if sample.fields.get(name) else 0
        assert page.locator(f'[data-amn-field="{name}"]').count() == expected, name


def test_no_extras_take_no_space(open_card):
    page = open_card(SAMPLES_BY_NAME["en"].fields).page
    assert page.eval_on_selector(".amn-extras", "e => e.getBoundingClientRect().height") == 0
    assert page.locator(".amn-chip-label").count() == 0


def test_pinyin_keeps_tone_colour_markup(open_card):
    page = open_card(SAMPLES_BY_NAME["zh_hans"].fields).page
    assert page.locator('[data-amn-field="Pinyin"] span[style*="color"]').count() == 2


def test_plain_reading_yields_to_pinyin(open_card):
    fields = {**SAMPLES_BY_NAME["zh_hans"].fields, "ExpressionReading": "gu3 tou5"}
    assert "gu3 tou5" not in open_card(fields).page.inner_text(".pitch")
    fields_without_pinyin = {**fields, "Pinyin": ""}
    assert "gu3 tou5" in open_card(fields_without_pinyin).page.inner_text(".pitch")


def test_forms_carry_their_own_language(open_card):
    page = open_card(SAMPLES_BY_NAME["zh_hans"].fields).page
    assert page.get_attribute('[data-amn-field="Traditional"]', "lang") == "zh-Hant"
    page = open_card(SAMPLES_BY_NAME["ko"].fields).page
    assert page.get_attribute('[data-amn-field="Hanja"]', "lang") == "ko"
    page = open_card(SAMPLES_BY_NAME["vi"].fields).page  # HanViet holds the Han characters (博士), not a reading
    assert page.get_attribute('[data-amn-field="HanViet"]', "lang") == "zh-Hant"


@pytest.mark.parametrize(
    "value,kind",
    [
        ("der", "masc"), ("die", "fem"), ("das", "neut"), ("le", "masc"), ("la", "fem"), ("el", "masc"),
        ("o", "masc"), ("a", "fem"), ("masculine", "masc"), ("feminine", "fem"), ("neuter", "neut"),
        ("common", "common"), ("m", "masc"), ("f", "fem"), ("n", "neut"), ("m inan", "masc"),
        ("м.", "masc"), ("ж.", "fem"), ("с.", "neut"), ("ч.", "masc"), ("ο", "masc"), ("η", "fem"),
        ("το", "neut"), ("ז" + GERESH, "masc"), ("נ" + GERESH, "fem"), ("unknown", None),
    ],
)
@pytest.mark.parametrize("night", [False, True], ids=["light", "night"])
def test_gender_colour(open_card, value, kind, night):
    page = open_card({"Expression": "x", "Gender": value}, night=night).page
    actual = page.eval_on_selector(".amn-gender", "e => getComputedStyle(e).color")
    expected = css_color(page, f"var(--gender-{kind})" if kind else "var(--fg-color)")
    assert actual == expected


def test_sentence_translation_on_back_only(open_card):
    fields = SAMPLES_BY_NAME["de"].fields
    back = open_card(fields).page
    translation = back.locator(".sentence .amn-translation")
    assert translation.inner_text() == "The dog is sleeping."
    assert translation.get_attribute("dir") == "auto"
    front = open_card(fields, side="front", card_type="IsSentenceCard").page
    assert front.locator(".amn-translation").count() == 0


def test_translation_stays_ltr_under_rtl_sentence(open_card):
    fields = {**SAMPLES_BY_NAME["ar"].fields, "SentenceTranslation": "I read a nice book."}
    page = open_card(fields).page
    assert page.eval_on_selector(".sentence .amn-translation", "e => getComputedStyle(e).direction") == "ltr"
```

Run: `uv run pytest tests/test_extras.py tests/test_contract.py -q`
Expected: FAIL, because none of the `amn-*` markup exists yet.

- [ ] **Step 3: Edit `src/back.html`: reading guard and extras**

In the `.dh-vocab` block, replace the reading line:

```html
                        {{^ExpressionFurigana}}{{ExpressionReading}}{{/ExpressionFurigana}}
```

with:

```html
                        {{^ExpressionFurigana}}{{^Pinyin}}{{^Jyutping}}{{ExpressionReading}}{{/Jyutping}}{{/Pinyin}}{{/ExpressionFurigana}}
```

Directly after the closing `</div>` of `.info` (the one after `<div class="audio-buttons"></div>`), still inside `.dh-vocab`, insert:

```html

                <!-- Anki Miner Note: per-language extras; each piece renders only when its field is filled -->
                <div class="amn-extras">
                    <div class="amn-readings">
                        {{#Pinyin}}<span class="amn-reading" data-amn-field="Pinyin">{{Pinyin}}</span>{{/Pinyin}}
                        {{#Jyutping}}<span class="amn-reading" data-amn-field="Jyutping">{{Jyutping}}</span>{{/Jyutping}}
                        {{#Romanization}}<span class="amn-reading" data-amn-field="Romanization">{{Romanization}}</span>{{/Romanization}}
                        {{#Transliteration}}<span class="amn-reading" data-amn-field="Transliteration">{{Transliteration}}</span>{{/Transliteration}}
                    </div>
                    <div class="amn-forms">
                        {{#Traditional}}<span class="amn-form" data-amn-field="Traditional" lang="zh-Hant">{{Traditional}}</span>{{/Traditional}}
                        {{#Hanja}}<span class="amn-form" data-amn-field="Hanja" lang="ko">{{Hanja}}</span>{{/Hanja}}
                        {{#HanViet}}<span class="amn-form" data-amn-field="HanViet" lang="zh-Hant">{{HanViet}}</span>{{/HanViet}}
                    </div>
                    <div class="amn-chips">
                        {{#Article}}<span class="amn-chip" data-amn-field="Article"><span class="amn-chip-label">article</span> {{Article}}</span>{{/Article}}
                        {{#Gender}}<span class="amn-chip amn-gender" data-amn-field="Gender" data-gender="{{text:Gender}}"><span class="amn-chip-label">gender</span> {{Gender}}</span>{{/Gender}}
                        {{#Plural}}<span class="amn-chip" data-amn-field="Plural"><span class="amn-chip-label">plural</span> {{Plural}}</span>{{/Plural}}
                        {{#PartOfSpeech}}<span class="amn-chip" data-amn-field="PartOfSpeech"><span class="amn-chip-label">pos</span> {{PartOfSpeech}}</span>{{/PartOfSpeech}}
                        {{#MeasureWord}}<span class="amn-chip" data-amn-field="MeasureWord"><span class="amn-chip-label">measure word</span> {{MeasureWord}}</span>{{/MeasureWord}}
                        {{#Classifier}}<span class="amn-chip" data-amn-field="Classifier"><span class="amn-chip-label">classifier</span> {{Classifier}}</span>{{/Classifier}}
                        {{#AspectPair}}<span class="amn-chip" data-amn-field="AspectPair"><span class="amn-chip-label">aspect pair</span> {{AspectPair}}</span>{{/AspectPair}}
                        {{#Root}}<span class="amn-chip" data-amn-field="Root"><span class="amn-chip-label">root</span> {{Root}}</span>{{/Root}}
                        {{#Binyan}}<span class="amn-chip" data-amn-field="Binyan"><span class="amn-chip-label">binyan</span> {{Binyan}}</span>{{/Binyan}}
                        {{#PresentStem}}<span class="amn-chip" data-amn-field="PresentStem"><span class="amn-chip-label">present stem</span> {{PresentStem}}</span>{{/PresentStem}}
                        {{#Colloquial}}<span class="amn-chip" data-amn-field="Colloquial"><span class="amn-chip-label">colloquial</span> {{Colloquial}}</span>{{/Colloquial}}
                        {{#Formal}}<span class="amn-chip" data-amn-field="Formal"><span class="amn-chip-label">formal</span> {{Formal}}</span>{{/Formal}}
                        {{#Affixes}}<span class="amn-chip" data-amn-field="Affixes"><span class="amn-chip-label">affixes</span> {{Affixes}}</span>{{/Affixes}}
                        {{#Segmentation}}<span class="amn-chip" data-amn-field="Segmentation"><span class="amn-chip-label">segmentation</span> {{Segmentation}}</span>{{/Segmentation}}
                        {{#Grammar}}<span class="amn-chip" data-amn-field="Grammar"><span class="amn-chip-label">grammar</span> {{Grammar}}</span>{{/Grammar}}
                    </div>
                </div>
```

- [ ] **Step 4: Edit `src/back.html`: sentence translation**

In **both** `<div class="sentence">` and `<div class="sentence-alt">`, insert this line directly before `<div class="audio-buttons-alt"></div>`:

```html
            {{#SentenceTranslation}}<div class="amn-translation" dir="auto">{{SentenceTranslation}}</div>{{/SentenceTranslation}}
```

- [ ] **Step 5: Append the extras CSS to `src/styling.css`**

```css

/*
 *  ANKI MINER NOTE: EXTRAS
 */
:root {
  --light-mode-gender-masc: #1f6fd1;
  --light-mode-gender-fem: #d02f5a;
  --light-mode-gender-neut: #2f8f4e;
  --light-mode-gender-common: #8a5cc2;
  --dark-mode-gender-masc: #6aa8ff;
  --dark-mode-gender-fem: #ff7b9c;
  --dark-mode-gender-neut: #6fd08f;
  --dark-mode-gender-common: #c3a2f2;
}

.card.nightMode {
  --gender-masc: var(--dark-mode-gender-masc);
  --gender-fem: var(--dark-mode-gender-fem);
  --gender-neut: var(--dark-mode-gender-neut);
  --gender-common: var(--dark-mode-gender-common);
}

.card:not(.nightMode) {
  --gender-masc: var(--light-mode-gender-masc);
  --gender-fem: var(--light-mode-gender-fem);
  --gender-neut: var(--light-mode-gender-neut);
  --gender-common: var(--light-mode-gender-common);
}

/* Empty rows have no children, no padding and no margin, so they take no space. */
.amn-extras {
  font-family: var(--font-sans);
  font-size: var(--info-font-size);
  overflow-wrap: anywhere;
}

.amn-readings,
.amn-forms,
.amn-chips {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0 0.6em;
}

.amn-reading,
.amn-form,
.amn-chip {
  margin-top: 0.3em;
}

.amn-form {
  font-family: var(--font-serif);
  font-size: 1.2em;
}

.amn-chip {
  border: 1px solid var(--fg-subtle);
  border-radius: 5px;
  padding: 0 0.4em;
  line-height: 1.6;
}

.amn-chip-label {
  color: var(--fg-subtle);
  font-size: 0.75em;
}

/* Gender: Anki Miner writes a language's own label (der/die/das, le/la, м./ж./с., …). */
.amn-gender:is([data-gender="masculine" i], [data-gender="der" i], [data-gender="le" i], [data-gender="el" i],
  [data-gender="o" i], [data-gender="m" i], [data-gender="m pers" i], [data-gender="m anim" i],
  [data-gender="m inan" i], [data-gender="ο"], [data-gender="м."], [data-gender="ч."], [data-gender="ז׳"]) {
  --gender: var(--gender-masc);
}

/* German "die" also marks plural-only nouns; it takes the feminine colour. */
.amn-gender:is([data-gender="feminine" i], [data-gender="die" i], [data-gender="la" i], [data-gender="a" i],
  [data-gender="f" i], [data-gender="η"], [data-gender="ж."], [data-gender="נ׳"]) {
  --gender: var(--gender-fem);
}

.amn-gender:is([data-gender="neuter" i], [data-gender="das" i], [data-gender="n" i], [data-gender="το"],
  [data-gender="с."]) {
  --gender: var(--gender-neut);
}

.amn-gender[data-gender="common" i] {
  --gender: var(--gender-common);
}

.amn-gender {
  color: var(--gender, var(--fg-color));
  border-color: var(--gender, var(--fg-subtle));
}

.amn-translation {
  font-family: var(--font-sans);
  font-size: var(--info-font-size);
  color: var(--fg-subtle);
  margin-top: 0.2em;
}
```

The `׳` in `"ז׳"` and `"נ׳"` must be U+05F3 (HEBREW PUNCTUATION GERESH), not an ASCII apostrophe. To check, run `grep -P '\x{05F3}' src/styling.css | wc -l`; it should print 2.

- [ ] **Step 6: Run and watch them pass**

Run: `uv run pytest tests/test_extras.py tests/test_contract.py -q`
Expected: all pass.

- [ ] **Step 7: Full suite, commit, merge**

```bash
uv run pytest -q && uv run ruff format . && uv run ruff check --fix .
git add -A && git commit -m "feat: show per-language extras, gender colours and sentence translation"
cd ~/Projects/anki_miner_note && git merge --ff-only feat/extras && git push -q origin main
git worktree remove .worktrees/task5 && git branch -d feat/extras
```

---

### Task 6: Update path, Anki Miner mapping check and the gate

**Files:**
- Create: `tests/test_update.py`, `scripts/check_anki_miner_mapping.py`, `scripts/check.sh`

**Interfaces:**
- Consumes:
  - `genapkg.build_model`, `genapkg.build_package(..., model=)` and `genapkg.field_names` (Task 1);
  - `cards.import_package` (Task 2);
  - from Anki Miner: `anki_miner.languages.AVAILABLE_LANGUAGES`, `anki_miner.languages.registry.get_profile(code).extra_card_fields`, `.capabilities`, and `anki_miner.services.note_presets.fill_note_type_fields(names, *, allow_presets, extra_specs) -> NoteTypeFill(preset, fields, extra_fields)`.
- Produces:
  - `scripts/check.sh`: exit 0 means green, and the last line is `CHECK GREEN` or `CHECK RED`.
  - The mapping script: exit 0 means ok, 1 a regression, 2 a skip.

- [ ] **Step 1: Worktree**

```bash
cd ~/Projects/anki_miner_note && git worktree add .worktrees/task6 -b test/update-gate && cd .worktrees/task6 && uv sync
```

- [ ] **Step 2: Write `tests/test_update.py`** (the spec's update contract)

```python
"""Updating = re-importing a newer .apkg with "Merge note types": new fields arrive, user notes keep their data."""

import genapkg
from anki.collection import Collection
from cards import import_package
from samples import EXTRAS


def test_imported_note_type_keeps_collapsed_extras(collection):
    """genanki must carry "collapsed" through to Anki; the YAML alone proves nothing."""
    fields = {field["name"]: field for field in collection.models.by_name(genapkg.MODEL_NAME)["flds"]}
    for name in EXTRAS:
        assert fields[name]["collapsed"] is True, name


def test_merge_import_adds_fields_and_keeps_user_notes(tmp_path):
    path = tmp_path / "collection.anki2"
    col = Collection(str(path))
    import_package(col, genapkg.build_package(tmp_path / "v1.apkg"))

    note = col.new_note(col.models.by_name(genapkg.MODEL_NAME))
    note["Expression"] = "user word"
    note["Sentence"] = "user sentence"
    note["Gender"] = "der"
    col.add_note(note, col.decks.id("Mining"))
    note_id = note.id

    model = genapkg.build_model()
    model.fields.append({"name": "MergeProbe", "collapsed": True})
    import_package(col, genapkg.build_package(tmp_path / "v2.apkg", model=model))
    col.close()

    # pylib caches note types; reopen to read what the import actually stored.
    col = Collection(str(path))
    try:
        names = col.models.field_names(col.models.by_name(genapkg.MODEL_NAME))
        assert names == genapkg.field_names() + ["MergeProbe"]
        kept = col.get_note(note_id)
        assert (kept["Expression"], kept["Sentence"], kept["Gender"], kept["MergeProbe"]) == (
            "user word",
            "user sentence",
            "der",
            "",
        )
    finally:
        col.close()
```

Run: `uv run pytest tests/test_update.py -v`
Expected: PASS. A spike on 2026-10-01 confirmed the behaviour; this test locks it in.

- [ ] **Step 3: Write `scripts/check_anki_miner_mapping.py`**

```python
#!/usr/bin/env python3
"""Check that Anki Miner's "Fill in automatically" maps this note type for every mining language.

Run it with Anki Miner's interpreter:
    ~/Projects/anki_miner/.venv/bin/python scripts/check_anki_miner_mapping.py
Exit 0: every language maps (known gaps allowed). 1: a regression. 2: anki_miner not importable (skip).
"""

import sys
from pathlib import Path

LOCK = Path(__file__).resolve().parent.parent / "build" / "fields.lock"
CORE_KEYS = ("word", "sentence", "definition", "glossary", "picture", "audio", "expression_audio", "sentence_translation")
# Closed by the Anki Miner integration (spec §2, "Known gaps").
KNOWN_GAPS = {("ja", "sentence_translation"), ("he", "POS"), ("th", "Reading")}


def main() -> int:
    try:
        from anki_miner.languages import AVAILABLE_LANGUAGES
        from anki_miner.languages.registry import get_profile
        from anki_miner.services.note_presets import fill_note_type_fields
    except ImportError as exc:
        print(f"SKIP: anki_miner is not importable ({exc})")
        return 2

    fields = LOCK.read_text(encoding="utf-8").split()
    failed = []
    for lang in AVAILABLE_LANGUAGES:
        profile = get_profile(lang)
        fill = fill_note_type_fields(
            fields,
            allow_presets="note_presets" in profile.capabilities,
            extra_specs=profile.extra_card_fields,
        )
        problems = [key for key in CORE_KEYS if not fill.fields.get(key) and (lang, key) not in KNOWN_GAPS]
        problems += [
            spec.placeholder
            for spec in profile.extra_card_fields
            if spec.key not in fill.extra_fields and (lang, spec.placeholder) not in KNOWN_GAPS
        ]
        if lang == "ja" and (fill.preset is None or fill.preset.id != "lapis"):
            problems.append("ja must resolve to the Lapis preset")
        print(f"{lang:4} {'ok' if not problems else 'FAIL ' + ', '.join(problems)}")
        if problems:
            failed.append(lang)
    print(f"{len(AVAILABLE_LANGUAGES) - len(failed)}/{len(AVAILABLE_LANGUAGES)} languages map")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
```

Run: `~/Projects/anki_miner/.venv/bin/python scripts/check_anki_miner_mapping.py; echo "exit=$?"`
Expected: 32 lines, all `ok`, then `32/32 languages map` and `exit=0`. The dry run on 2026-10-01 showed exactly the three known gaps and nothing else.

- [ ] **Step 4: Write `scripts/check.sh`** and make it executable

```bash
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
```

```bash
chmod +x scripts/check.sh scripts/check_anki_miner_mapping.py
```

- [ ] **Step 5: Format, lint, run the gate**

```bash
uv run ruff format . && uv run ruff check --fix .
scripts/check.sh > check.log 2>&1
```

Then, as a separate step: `echo "exit=$?"; tail -5 check.log`
Expected: `exit=0`, with `CHECK GREEN` as the last line.

- [ ] **Step 6: Commit and merge**

```bash
git add -A && git commit -m "test: lock the merge-update contract and add the check gate"
cd ~/Projects/anki_miner_note && git merge --ff-only test/update-gate && git push -q origin main
git worktree remove .worktrees/task6 && git branch -d test/update-gate
```

---

### Task 7: README, CLAUDE.md, CI and releases

**Files:**
- Modify: `README.md` (rewrite)
- Create: `CLAUDE.md`, `.github/workflows/ci.yml`, `.github/workflows/release.yml`
- Delete: `.github/workflows/draft_release.yaml`

**Interfaces:**
- Consumes: `scripts/check.sh` (Task 6) and `build/genapkg.py` (Task 1).
- Produces:
  - CI on pushes to `main` and on pull requests.
  - A draft GitHub release on `v*` tags, with `Anki-Miner-Note-<tag>.apkg` attached.

- [ ] **Step 1: Worktree**

```bash
cd ~/Projects/anki_miner_note && git worktree add .worktrees/task7 -b docs/readme-ci && cd .worktrees/task7
```

- [ ] **Step 2: Rewrite `README.md`**

```markdown
# Anki Miner Note

An Anki note type for sentence mining in any language, made for [Anki Miner](https://github.com/0xzerolight/anki_miner).
Based on [Lapis](https://github.com/donkuri/lapis) by donkuri and contributors.

- One note type for every language Anki Miner mines, Japanese included.
- Lapis's card types: word, word + sentence, click, sentence and audio.
- Per-language extras (pinyin, jyutping, hanja, gender, plural, root, …) appear only when filled.
- Right-to-left layout for Arabic, Persian and Hebrew, and regional fonts so Chinese, Japanese and Korean characters take the right shapes.

## Install

1. Download `Anki-Miner-Note-<version>.apkg` from Releases.
2. In Anki 23.10 or later, choose File → Import and pick the file.
3. In Anki Miner, choose Settings → Cards & Anki, select the **Anki Miner Note** note type, then click **Fill in automatically**.

## Update

Import the new `.apkg` with **Merge note types** ticked. Your notes and their fields are kept.

## Language

The `Language` field takes a language tag: `ja`, `zh-Hans`, `zh-Hant`, `yue`, `ko`, `ar`, `fa`, `he`, `th`, `de`, and so on.
Left empty, the card guesses the language from the word and sentence.

## Fonts

The card uses fonts already on your device. To change them, edit these variables at the top of the note type's Styling: `--latin-serif`, `--latin-sans`, `--cjk-serif` and `--cjk-sans`. The stacks for Chinese, Cantonese, Korean, Arabic, Persian, Hebrew and Thai are in the LANGUAGES section at the end of the Styling.
Lapis's other settings still apply; see [docs/user_settings.md](docs/user_settings.md).

## License

GPL-3.0, like Lapis.
```

- [ ] **Step 3: Write `CLAUDE.md`**

```markdown
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
```

- [ ] **Step 4: Write the workflows and remove Lapis's**

`.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: astral-sh/setup-uv@v10.2.0
      - name: Install fonts
        run: sudo apt-get update && sudo apt-get install -y fonts-noto-core fonts-noto-cjk
      - run: uv sync --locked
      - run: uv run playwright install --with-deps chromium
      - name: Gate
        run: scripts/check.sh
        env:
          SKIP_ANKI_MINER_MAPPING: "1"
      - uses: actions/upload-artifact@v7
        if: always()
        with:
          name: card-screenshots
          path: test-artifacts/
```

`.github/workflows/release.yml`:

```yaml
name: Release

on:
  push:
    tags: ["v*"]

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: astral-sh/setup-uv@v10.2.0
      - run: uv sync --locked
      - run: uv run python build/genapkg.py "dist/Anki-Miner-Note-${GITHUB_REF_NAME}.apkg"
      - uses: softprops/action-gh-release@v3
        with:
          draft: true
          files: dist/Anki-Miner-Note-${{ github.ref_name }}.apkg
          body: |
            Import into Anki 23.10 or later. When updating, tick "Merge note types" in the import dialog.
```

```bash
git rm -q .github/workflows/draft_release.yaml
```

- [ ] **Step 5: Gate, commit, merge, watch CI**

```bash
scripts/check.sh > check.log 2>&1
```

Read `echo "exit=$?"` as a separate step; it must be `exit=0`. Then:

```bash
git add -A && git commit -m "docs: rewrite README for Anki Miner Note; add CI and tag releases"
cd ~/Projects/anki_miner_note && git merge --ff-only docs/readme-ci && git push -q origin main
git worktree remove .worktrees/task7 && git branch -d docs/readme-ci
gh run watch --repo 0xzerolight/anki_miner_note --exit-status "$(gh run list --repo 0xzerolight/anki_miner_note --limit 1 --json databaseId --jq '.[0].databaseId')"
```

Expected: the CI run succeeds. Download the `card-screenshots` artifact and look at them, especially ar, he, th, ko and zh_hant, in both light and night mode.

---

### Task 8: End-to-end in real Anki and the v0.1.0 draft release (owner-assisted)

This task touches the owner's Anki and Anki Miner. Ask before each step that writes to them.

- [ ] **Step 1:** Build the release candidate: `uv run python build/genapkg.py dist/Anki-Miner-Note-v0.1.0.apkg`.
- [ ] **Step 2:** Ask the owner where to import it.
  - Option (a): a new Anki profile (Anki → Switch Profile → Add), with AnkiConnect enabled there.
  - Option (b): their main profile. This adds the note type and the example deck.
  - Import through File → Import, or through AnkiConnect `importPackage` once the owner approves.
- [ ] **Step 3:** Mine with an isolated Anki Miner home, never the owner's real one:

```bash
export ANKI_MINER_HOME="$(mktemp -d)"
anki_miner_gui
```

  For each of de, pl, zh, ko, ar and ja:
  1. Run the Setup Wizard for the language. It downloads that language's free resources.
  2. Choose Settings → Cards & Anki → note type **Anki Miner Note** → **Fill in automatically**.
  3. Mine one short subtitle file through Reading → Subtitle Files.

  The run writes to whichever Anki profile is open, so keep the Step 2 profile open.
- [ ] **Step 4:** Review the new cards in the Anki desktop reviewer, front and back, light and night mode, and on AnkiDroid if available. Screenshot each language. Note anything Task 2–5 tests did not catch, in particular:
  - whether zh fills `ExpressionReading`; if it does, the Pinyin guard should hide it;
  - the actual Pinyin markup.
- [ ] **Step 5:** Fix any defect on a worktree, with a regression test first. Re-run the gate.
- [ ] **Step 6:** Tag and release:

```bash
git tag v0.1.0
git push origin v0.1.0
```

Then check that the draft release appeared with the `.apkg` attached:

```bash
gh release view v0.1.0 --repo 0xzerolight/anki_miner_note
```

The release stays a draft in the private repo.
