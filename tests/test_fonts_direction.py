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
LAPIS_SERIF = [
    "Hiragino Mincho ProN",
    "Noto Serif CJK JP",
    "Noto Serif JP",
    "Yu Mincho",
    "HanaMinA",
    "HanaMinB",
    "serif",
]


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
