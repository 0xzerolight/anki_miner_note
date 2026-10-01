"""Static contract of the note type: identity, field list, template references."""

import re
from pathlib import Path

import genapkg
from samples import EXTRAS, SAMPLES

ROOT = Path(__file__).resolve().parent.parent
LAPIS_MODEL_ID = 1667218449922

LAPIS_CORE = (
    "Expression",
    "ExpressionFurigana",
    "ExpressionReading",
    "ExpressionAudio",
    "SelectionText",
    "MainDefinition",
    "DefinitionPicture",
    "Sentence",
    "SentenceFurigana",
    "SentenceAudio",
    "Picture",
    "Glossary",
    "Hint",
    "IsWordAndSentenceCard",
    "IsClickCard",
    "IsSentenceCard",
    "IsAudioCard",
    "PitchPosition",
    "PitchCategories",
    "Frequency",
    "FreqSort",
    "MiscInfo",
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


def test_extras_only_inside_their_own_section():
    """An extra is referenced only inside {{#Extra}}…{{/Extra}}, so an empty field leaves no markup."""
    back = template_text("back.html")
    for name in EXTRAS:
        outside = re.sub(r"\{\{#" + name + r"\}\}.*?\{\{/" + name + r"\}\}", "", back, flags=re.S)
        stray = [
            body for prefix, body in TEMPLATE_REF.findall(outside) if not prefix and body.split(":")[-1].strip() == name
        ]
        assert not stray, f"{name} is referenced outside its own section: {stray}"


ANKI_MINER_TONE_COLOURS = {"#e75353", "#be7500", "#199a39", "#4286e5", "#868686", "#a66dd2"}
TONE_SPAN = r'<span style="color:(#[0-9a-f]{6})">([^<]+)</span>'
ASPECT_LABELS = {"imperfective", "perfective", "imperfective or perfective"}


def test_samples_hold_anki_miner_formats():
    """Samples are the fixtures and the example deck: each holds what Anki Miner writes (spec §1)."""
    for sample in SAMPLES:
        if sample.name == "all_extras":
            continue
        fields = sample.fields
        pos = fields.get("PartOfSpeech", "")
        assert pos == pos.lower(), sample.name
        aspect = fields.get("AspectPair", "")
        assert not aspect or aspect.split(" (")[0] in ASPECT_LABELS, sample.name
        for name in ("Pinyin", "Jyutping"):
            value = fields.get(name, "")
            if value:
                spans = re.findall(TONE_SPAN, value)
                assert " ".join(f'<span style="color:{c}">{s}</span>' for c, s in spans) == value, sample.name
                assert {c for c, _ in spans} <= ANKI_MINER_TONE_COLOURS, sample.name
                assert fields.get("ExpressionReading") == " ".join(s for _, s in spans), sample.name
        assert not re.search(r"[A-Za-z]", fields.get("MeasureWord", "")), sample.name
        if "Formal" in fields:
            assert fields["Formal"] != fields["Expression"], sample.name
        assert not fields.get("Frequency") or fields["Frequency"].startswith("<ul><li>"), sample.name
