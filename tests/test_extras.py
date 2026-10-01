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


def test_extras_line_height_does_not_follow_the_arabic_face(open_card):
    """Noto Sans Arabic leads the ar/fa sans stack; line-height: normal would make each extras line about 2.1em."""
    fields = {
        "Expression": '<div dir="rtl" lang="fa">رفتن</div>',
        "Sentence": '<div dir="rtl" lang="fa">من هر روز به مدرسه می‌روم.</div>',
        "Romanization": "raftan",
    }
    page = open_card(fields).page
    assert page.eval_on_selector(".amn-extras", "e => getComputedStyle(e).lineHeight") != "normal"
    ratio = page.eval_on_selector(
        '[data-amn-field="Romanization"]',
        "e => e.getBoundingClientRect().height / parseFloat(getComputedStyle(e).fontSize)",
    )
    assert ratio <= 1.6, ratio


PINYIN = '<span style="color:#be7500">yín</span> <span style="color:#be7500">háng</span>'


@pytest.mark.parametrize(
    "fields,below",
    [
        ({"Expression": "銀行", "Pinyin": PINYIN}, ".amn-reading"),
        ({"Expression": "嘢", "Jyutping": '<span style="color:#a66dd2">je5</span>'}, ".amn-reading"),
        ({"Expression": "کتاب", "Romanization": "ketâb"}, ".amn-reading"),
        ({"Expression": "Hund", "Gender": "der"}, ".amn-chip"),
    ],
    ids=["pinyin", "jyutping", "romanization", "chip"],
)
def test_no_blank_reading_line_on_mobile(open_card, fields, below):
    """On phones the audio buttons leave .info; its <br> must not leave a blank line under the headword."""
    page = open_card(fields, mobile=True).page
    gap = page.evaluate(
        "below => document.querySelector(below).getBoundingClientRect().top"
        " - document.querySelector('.vocab').getBoundingClientRect().bottom",
        below,
    )
    assert gap < 20, gap


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
    page = open_card({"Expression": "學校", "Sentence": "내일 學校에서 만나요.", "Hanja": "學校"}).page
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
    plain = css_color(page, "var(--fg-color)")
    if kind is None:
        assert actual == plain
    else:
        assert actual == css_color(page, f"var(--gender-{kind})")
        assert actual != plain, "the --gender-* token is missing, so the chip fell back to the text colour"


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


# WCAG contrast of an element's text: the ancestors' background colours composited over white, then the
# text colour, after the element's own brightness() filter, composited over that.
CONTRAST_JS = """e => {
    const rgba = (c) => {
        const v = c.match(/[\\d.]+/g).map(Number);
        return [v[0], v[1], v[2], v.length > 3 ? v[3] : 1];
    };
    const over = (top, under) => top.slice(0, 3).map((v, i) => v * top[3] + under[i] * (1 - top[3]));
    const layers = [];
    for (let n = e; n; n = n.parentElement) layers.unshift(rgba(getComputedStyle(n).backgroundColor));
    let bg = [255, 255, 255];
    for (const layer of layers) bg = over(layer, bg);
    const brightness = /brightness\\(([\\d.]+)\\)/.exec(getComputedStyle(e).filter);
    const k = brightness ? Number(brightness[1]) : 1;
    const [r, g, b, a] = rgba(getComputedStyle(e).color);
    const fg = over([r * k, g * k, b * k].map((v) => Math.min(255, v)).concat(a), bg);
    const lin = (v) => ((v /= 255) <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
    const lum = (c) => 0.2126 * lin(c[0]) + 0.7152 * lin(c[1]) + 0.0722 * lin(c[2]);
    const [hi, lo] = [lum(fg), lum(bg)].sort((x, y) => y - x);
    return (hi + 0.05) / (lo + 0.05);
}"""
MUTED = {
    "Expression": "Hund",
    "Sentence": "Der Hund schläft.",
    "SentenceTranslation": "The dog is sleeping.",
    "PartOfSpeech": "noun",
}
# Anki Miner's tone palette (zh/render.py, yue/render.py), written inline as style="color:#…"
TONE_COLOURS = ("#e75353", "#be7500", "#199a39", "#4286e5", "#868686", "#a66dd2")


@pytest.mark.parametrize("mobile", [False, True], ids=["desktop", "mobile"])
@pytest.mark.parametrize("night", [False, True], ids=["light", "night"])
def test_chip_label_and_translation_contrast(open_card, night, mobile):
    page = open_card(MUTED, night=night, mobile=mobile).page
    translation = ".sentence-alt .amn-translation" if mobile else ".sentence .amn-translation"
    assert page.eval_on_selector(translation, CONTRAST_JS) >= 4.5
    assert page.eval_on_selector(".amn-chip-label", CONTRAST_JS) >= 3


@pytest.mark.parametrize("value", ["der", "die", "das", "common"])
@pytest.mark.parametrize("mobile", [False, True], ids=["desktop", "mobile"])
@pytest.mark.parametrize("night", [False, True], ids=["light", "night"])
def test_gender_chip_contrast(open_card, value, mobile, night):
    page = open_card({"Expression": "Wort", "Gender": value}, mobile=mobile, night=night).page
    assert page.eval_on_selector(".amn-gender", CONTRAST_JS) >= 4.5


@pytest.mark.parametrize("field", ["Pinyin", "Jyutping"])
@pytest.mark.parametrize("mobile", [False, True], ids=["desktop", "mobile"])
@pytest.mark.parametrize("night", [False, True], ids=["light", "night"])
def test_tone_colours_reach_reading_contrast(open_card, field, mobile, night):
    spans = " ".join(f'<span style="color:{colour}">ba{tone}</span>' for tone, colour in enumerate(TONE_COLOURS, 1))
    page = open_card({"Expression": "八", field: spans}, mobile=mobile, night=night).page
    ratios = page.eval_on_selector_all(f'[data-amn-field="{field}"] span', f"els => els.map({CONTRAST_JS})")
    assert len(ratios) == len(TONE_COLOURS)
    assert min(ratios) >= 4.5, [round(ratio, 2) for ratio in ratios]
