"""Per-language extras: readings, alternate forms, chips, gender colours, sentence translation."""

import pytest

from samples import EXTRAS, SAMPLES, SAMPLES_BY_NAME

pytestmark = pytest.mark.render

GERESH = "\u05f3"
CHIP_LABELS = {
    "Article": "article",
    "Gender": "gender",
    "Plural": "plural",
    "PartOfSpeech": "pos",
    "MeasureWord": "measure word",
    "Classifier": "classifier",
    "AspectPair": "aspect pair",
    "Root": "root",
    "Binyan": "binyan",
    "PresentStem": "present stem",
    "Colloquial": "colloquial",
    "Formal": "formal",
    "Affixes": "affixes",
    "Segmentation": "segmentation",
    "Grammar": "grammar",
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
        ("der", "masc"),
        ("die", "fem"),
        ("das", "neut"),
        ("le", "masc"),
        ("la", "fem"),
        ("el", "masc"),
        ("o", "masc"),
        ("a", "fem"),
        ("masculine", "masc"),
        ("feminine", "fem"),
        ("neuter", "neut"),
        ("common", "common"),
        ("m", "masc"),
        ("f", "fem"),
        ("n", "neut"),
        ("m inan", "masc"),
        ("м.", "masc"),
        ("ж.", "fem"),
        ("с.", "neut"),
        ("ч.", "masc"),
        ("ο", "masc"),
        ("η", "fem"),
        ("το", "neut"),
        ("ז" + GERESH, "masc"),
        ("נ" + GERESH, "fem"),
        ("unknown", None),
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
