"""Per-language font stacks, right-to-left blocks, Thai line height, no overflow at phone width."""

import pytest

from cards import CARD_TYPES, PICTURE
from samples import SAMPLES, SAMPLES_BY_NAME

pytestmark = pytest.mark.render

REGION_SERIF = {
    "zh": "Noto Serif CJK SC",
    "zh-Hans": "Noto Serif CJK SC",
    "zh-Hant": "Noto Serif CJK TC",
    "zh-TW": "Noto Serif CJK TC",
    "yue": "Noto Serif CJK HK",
    "zh-HK": "Noto Serif CJK HK",
    "zh-MO": "Noto Serif CJK HK",
    "zh-Hant-HK": "Noto Serif CJK HK",
    "zh-Hant-MO": "Noto Serif CJK HK",
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
LAPIS_SANS = [
    "Inter",
    "SF Pro Display",
    "Liberation Sans",
    "Segoe UI",
    "Hiragino Kaku Gothic ProN",
    "Noto Sans CJK JP",
    "Noto Sans JP",
    "Meiryo",
    "HanaMinA",
    "HanaMinB",
    "sans-serif",
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
    assert sans == LAPIS_SANS


@pytest.mark.parametrize(
    "name,inner_font",
    [("zh_hant", "Noto Serif CJK TC"), ("yue", "Noto Serif CJK TC"), ("zh_hans", "Noto Serif CJK SC")],
)
def test_inner_lang_span_takes_its_region_fonts(open_card, name, inner_font):
    """Anki Miner tags the sentence (<span lang="zh-Hant|zh-Hans">) and leaves Language empty."""
    stack = families(open_card(SAMPLES_BY_NAME[name].fields).page, ".sentence span[lang]")
    assert inner_font in stack
    assert not ({"Noto Serif CJK SC", "Noto Serif CJK TC"} - {inner_font}) & set(stack), stack


def test_vietnamese_card_draws_han_with_traditional_shapes(open_card):
    """Han in a Vietnamese card (HanViet, glossary etymologies) takes the TC faces, not the Japanese default."""
    page = open_card({"Language": "vi", "Expression": "xương", "MainDefinition": "from 骨"}).page
    sans = families(page, ".main-def")
    assert "Noto Sans CJK TC" in sans and "Noto Sans CJK JP" not in sans, sans
    assert families(page, ".vocab")[0] == "Noto Serif"


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


@pytest.mark.parametrize("lang,word,reading", [("he", "ספר", "סֵפֶר"), ("ar", "قلم", "قَلَم")])
def test_rtl_reading_does_not_flip_the_card_inside_dir_auto(open_card, lang, word, reading):
    """AnkiDroid wraps every card in <div id="content" dir="auto">; a raw RTL reading must not flip the card."""
    fields = {
        "Expression": f'<div dir="rtl" lang="{lang}">{word}</div>',
        "ExpressionReading": reading,
        "Sentence": f'<div dir="rtl" lang="{lang}">{word} {word}.</div>',
        "Glossary": "book. a writing.",
        "PartOfSpeech": "noun",
    }
    page = open_card(fields, mobile=True).page
    page.evaluate("document.getElementById('qa').setAttribute('dir', 'auto')")
    for selector in (".def-header", ".amn-chips", ".main-def"):
        assert computed(page, selector, "direction") == "ltr", selector
    assert computed(page, ".vocab", "direction") == "rtl"


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


def ligatures(page, selector: str) -> str:
    return computed(page, selector, "fontVariantLigatures")


def test_turkish_card_turns_off_the_fi_ligature(open_card):
    """Noto Serif's fi ligature drops the i's dot, so "fi" reads as "fı"; Anki Miner leaves Turkish untagged."""
    fields = {"Expression": "fiyat", "Sentence": "Fıstığın fiyatı arttı."}
    assert ligatures(open_card(fields, side="front").page, ".front-vocab") == "no-common-ligatures"
    front = open_card(fields, card_type="IsSentenceCard", side="front").page
    assert ligatures(front, ".front-sentence") == "no-common-ligatures"
    back = open_card(fields).page
    assert ligatures(back, ".vocab") == "no-common-ligatures"
    assert ligatures(back, ".sentence") == "no-common-ligatures"


# Arabic fonts join letters through common ligatures; Noto Thai joins ฤๅ and ฦๅ the same way.
@pytest.mark.parametrize(
    "expression,selector",
    [('<div dir="rtl" lang="ar">الله</div>', ".front-vocab div"), ("ฤๅษี", ".front-vocab")],
    ids=["ar", "th"],
)
def test_script_fonts_keep_their_common_ligatures(open_card, expression, selector):
    page = open_card({"Expression": expression, "Sentence": "x"}, side="front").page
    assert ligatures(page, selector) == "normal"


KO_LONG = {
    "Expression": "국립중앙박물관",
    "Sentence": (
        "어제저녁에 우리 할머니께서 끓여주신 된장찌개를 먹고 나서 "
        "<b>국립중앙박물관</b>에서 열리는 특별전시회를 보러 "
        "서둘러 지하철을 탔습니다."
    ),
}
# Pairs of Hangul syllables that a line break separates, i.e. breaks inside a word.
HANGUL_SPLITS = """sel => {
    const chars = [];
    const walker = document.createTreeWalker(document.querySelector(sel), NodeFilter.SHOW_TEXT);
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
        for (let i = 0; i < node.data.length; i++) {
            const range = document.createRange();
            range.setStart(node, i);
            range.setEnd(node, i + 1);
            const rect = range.getClientRects()[0];
            if (rect) chars.push([node.data[i], rect.top]);
        }
    }
    const hangul = /[\\uac00-\\ud7af]/;
    const splits = [];
    for (let i = 1; i < chars.length; i++) {
        const [before, beforeTop] = chars[i - 1];
        const [after, afterTop] = chars[i];
        if (afterTop > beforeTop + 5 && hangul.test(before) && hangul.test(after)) splits.push(before + "|" + after);
    }
    return splits;
}"""


def test_korean_wraps_between_words(open_card):
    front = open_card(KO_LONG, card_type="IsSentenceCard", side="front", mobile=True).page
    assert computed(front, ".front-sentence", "wordBreak") == "keep-all"
    assert front.evaluate(HANGUL_SPLITS, ".front-sentence") == []
    back = open_card(KO_LONG, mobile=True).page
    assert back.evaluate(HANGUL_SPLITS, ".sentence-alt") == []
    assert back.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")


def test_keep_all_is_korean_only(open_card):
    fields = {"Expression": "骨", "Sentence": "我们<b>骨</b>头很硬。"}
    page = open_card(fields, card_type="IsSentenceCard", side="front").page
    assert computed(page, ".front-sentence", "wordBreak") == "normal"


def test_wrapped_rtl_glossary_example_aligns_to_its_start_edge(open_card):
    """Anki Miner marks RTL examples unicode-bidi: plaintext; Lapis's .main-def text-align: left left them ragged."""
    example = "دیروز بعد از ظهر با دوستانم به کتابخانهٔ بزرگ شهر رفتیم و چند ساعت آنجا درس خواندیم. " * 2
    glossary = (
        '<div class="yomitan-glossary"><ol data-count="1"><li data-dictionary="wty-fa-en">'
        f'<div data-sc-content="example-sentence-a">{example}</div></li></ol></div>'
        '<style>.yomitan-glossary ol[data-count] [data-sc-content="example-sentence-a"]'
        "{unicode-bidi:plaintext}</style>"
    )
    fields = {
        "Expression": '<div dir="rtl" lang="fa">کتابخانه</div>',
        "Sentence": '<div dir="rtl" lang="fa">به کتابخانه رفتیم.</div>',
        "Glossary": glossary,
    }
    page = open_card(fields, mobile=True).page
    rights = page.eval_on_selector(
        '[data-sc-content="example-sentence-a"]',
        "e => { const r = document.createRange(); r.selectNodeContents(e);"
        " return [...r.getClientRects()].map(q => Math.round(q.right)); }",
    )
    assert len(rights) > 1 and max(rights) - min(rights) <= 2, rights


@pytest.mark.parametrize("sample", SAMPLES, ids=lambda s: s.name)
@pytest.mark.parametrize("card_type", CARD_TYPES, ids=lambda c: c or "word")
@pytest.mark.parametrize("side", ["front", "back"])
def test_no_horizontal_overflow_on_mobile(open_card, sample, card_type, side):
    """Real Anki Miner cards carry a screenshot, so every card here does too."""
    page = open_card({**sample.fields, "Picture": PICTURE}, card_type=card_type, side=side, mobile=True).page
    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")


@pytest.mark.parametrize("sample", SAMPLES, ids=lambda s: s.name)
def test_picture_stays_inside_its_box_on_desktop(open_card, sample):
    """Extras make .dh-vocab taller, and Lapis sizes the picture to that height."""
    page = open_card({**sample.fields, "Picture": PICTURE}).page
    overflow = page.evaluate(
        """() => {
            const box = document.querySelector(".dh-image").getBoundingClientRect();
            const img = document.querySelector(".dh-image img").getBoundingClientRect();
            return img.right - box.right;
        }"""
    )
    assert overflow <= 0.5


# Number of line boxes the element's text occupies.
LINES = """sel => {
    const range = document.createRange();
    range.selectNodeContents(document.querySelector(sel));
    return new Set([...range.getClientRects()].filter((r) => r.width > 1).map((r) => Math.round(r.top))).size;
}"""
WIDTH = "sel => document.querySelector(sel).getBoundingClientRect().width"
FITS = "document.documentElement.scrollWidth <= document.documentElement.clientWidth"


# Extras make .dh-vocab taller, setDHHeight() makes the picture as tall, and so wider: that is when it splits.
@pytest.mark.parametrize(
    "fields,mobile",
    [
        ({"Expression": "καταπολεμούσαμε"}, False),
        ({"Expression": "здравствуйте", "ExpressionReading": "здра́вствуйте", "PartOfSpeech": "interjection"}, False),
        ({"Expression": "niebezpieczeństwo", "Gender": "n", "PartOfSpeech": "noun"}, False),
        ({"Expression": "αλληλογραφία"}, True),
    ],
    ids=["el-desktop", "ru-desktop", "pl-desktop", "el-mobile"],
)
def test_back_headword_takes_room_from_the_picture_before_splitting(open_card, fields, mobile):
    card = open_card({**fields, "Sentence": "x", "Picture": PICTURE}, mobile=mobile)
    assert card.page.evaluate(LINES, ".vocab") == 1
    assert card.page.evaluate(FITS)
    assert card.errors == []


@pytest.mark.parametrize("mobile", [False, True], ids=["desktop", "mobile"])
def test_overlong_back_headword_keeps_the_picture_and_page_width(open_card, mobile):
    fields = {"Expression": "Çekoslovakyalılaştıramadıklarımızdanmışsınız", "Sentence": "x", "Picture": PICTURE}
    page = open_card(fields, mobile=mobile).page
    assert page.evaluate(FITS)
    assert page.eval_on_selector(".def-header", "e => e.scrollWidth <= e.clientWidth")
    assert page.evaluate(WIDTH, ".dh-image img") >= 99.5


# On a 320 px phone the picture gives up room (Lapis's 60vw cap) before an everyday word splits.
@pytest.mark.parametrize("word", ["Arbeitsplatz", "universidad", "öğretmenler", "ประวัติศาสตร์"])
def test_narrow_phone_keeps_a_common_back_headword_whole(open_card, word):
    page = open_card({"Expression": word, "Sentence": "x", "Picture": PICTURE}, mobile=True, width=320).page
    assert page.evaluate(LINES, ".vocab") == 1
    assert page.evaluate(FITS)
    assert page.eval_on_selector(".def-header", "e => e.scrollWidth <= e.clientWidth")


def test_alt_picture_position_gives_the_headword_the_whole_row(open_card):
    page = open_card({"Expression": "kedi", "Sentence": "x", "Picture": PICTURE}).page
    page.evaluate("document.getElementById('lapis').setAttribute('data-main-picture-position', 'alt')")
    assert page.evaluate(WIDTH, ".dh-vocab") == page.evaluate(WIDTH, ".def-header")
