"""Every sample renders in every card type without script errors; Japanese keeps Lapis's furigana and pitch."""

import warnings

import pytest
from playwright.sync_api import Error as PlaywrightError

from cards import ARTIFACTS, CARD_TYPES
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


def test_ascii_backslash_downstep_in_pitch_position(open_card):
    page = open_card({"Expression": "食べる", "ExpressionReading": "たべる", "PitchPosition": "た\\べる"}).page
    assert page.inner_text("#pitch-tags li") == "1"


def test_trailing_ascii_backslash_downstep_keeps_the_back_script(open_card):
    card = open_card({"Expression": "橋", "ExpressionReading": "はし", "PitchPosition": "はし\\"})
    assert card.errors == []
    assert card.page.inner_text("#pitch-tags li") == "2"


def test_tag_text_cannot_break_the_back_script(open_card):
    """Anki stores tags as typed and {{Tags}} renders them raw, so ` ${ and a trailing \\ reach the page."""
    fields = {
        "Expression": "橋",
        "ExpressionReading": "はし",
        "PitchPosition": "2",
        "Tags": "don`t ${x} trail\\ a&amp;b",
    }
    card = open_card(fields)
    assert card.errors == []
    assert card.page.locator(".tags-container .tags").all_inner_texts() == ["${x}", "a&b", "don`t", "trail\\"]
    assert card.page.inner_text("#pitch-tags li") == "2"


def envelope(title: str, gloss: str) -> str:
    """One dictionary's hit, in the Yomitan envelope Anki Miner writes into MainDefinition and Glossary."""
    return (
        f'<div class="yomitan-glossary"><ol data-count="1"><li data-dictionary="{title}"><i>({title})</i>'
        f'<ul class="gloss-list" data-count="1"><li class="gloss-item"><div class="gloss-content">{gloss}</div>'
        "</li></ul></li></ol></div>"
    )


def test_glossary_from_another_dictionary_is_kept(open_card):
    """Anki Miner's Definition is the first provider that answers; its Glossary holds only offline ones."""
    fields = {
        "Expression": "十中八九",
        "MainDefinition": envelope("Jisho", "in all probability"),
        "Glossary": envelope("Jitendex.org [2026-06-06]", "in 8 or 9 cases out of ten"),
    }
    page = open_card(fields).page
    assert page.locator("#glossaries").count() == 1
    assert page.inner_text(".def-info").endswith("2")


def test_same_dictionaries_in_another_order_collapse(open_card):
    fields = {
        "Expression": "猫",
        "MainDefinition": envelope("新和英", "a cat") + envelope("JMdict", "cat"),
        "Glossary": envelope("JMdict", "cat") + envelope("新和英", "a cat"),
    }
    assert open_card(fields).page.locator("#glossaries").count() == 0


def test_hand_written_glossary_list_is_kept(open_card):
    fields = {
        "Expression": "猫",
        "MainDefinition": envelope("JMdict", "cat"),
        "Glossary": "<div><ol><li>my own note</li></ol></div>",
    }
    assert open_card(fields).page.locator("#glossaries").count() == 1


# Anki Miner's style block draws a rule between stacked dictionaries.
STACKED_STYLE = (
    "<style>.yomitan-glossary{--anki-miner-owned-style: 1;--am-faint: rgba(128,128,128,0.4);}"
    ".yomitan-glossary + .yomitan-glossary > ol[data-count]{margin-top: 0.85em;padding-top: 0.7em;"
    "border-top: 1px solid var(--am-faint);}</style>"
)


def test_stacked_dictionaries_leave_no_emptied_box(open_card):
    stacked = envelope("CC-CEDICT Canto", "bank") + envelope("CC-Canto", "money lender") + envelope("Words.hk", "bank")
    fields = {
        "Expression": "銀行",
        "Sentence": '<span lang="zh-Hant">我聽日要去銀行攞錢。</span>',
        "MainDefinition": stacked + STACKED_STYLE,
        "Glossary": stacked + STACKED_STYLE,
    }
    page = open_card(fields).page
    assert page.locator("#primary li[data-dictionary]").count() == 3
    assert page.locator("#primary .yomitan-glossary:not(:has(li[data-dictionary]))").count() == 0


def yomitan_single_glossary(title: str, gloss: str, style: str = "") -> str:
    """Yomitan's {single-glossary-X} marker: the dictionary's scoped <style> sits inside its own wrapper."""
    return (
        f'<div style="text-align: left;" class="yomitan-glossary"><ol><li data-dictionary="{title}">'
        f'<i>({title})</i> <span class="probe">{gloss}</span></li>{style}</ol></div>'
    )


def test_second_primary_dictionary_keeps_its_yomitan_styles(open_card):
    style = '<style>.yomitan-glossary [data-dictionary="Jitendex"] .probe{color: rgb(1, 2, 3)}</style>'
    main = yomitan_single_glossary("JMdict", "cat") + yomitan_single_glossary("Jitendex", "cat (animal)", style)
    page = open_card({"Expression": "猫", "MainDefinition": main}).page
    assert page.locator("#primary li[data-dictionary]").count() == 2
    colour = page.eval_on_selector('[data-dictionary="Jitendex"] .probe', "e => getComputedStyle(e).color")
    assert colour == "rgb(1, 2, 3)"


# Separators a reader sees on the Glossaries page: the top border of each list that takes up height.
GLOSSARY_SEPARATORS = """() => [...document.querySelectorAll("#glossaries ol[data-count]")]
    .filter((ol) => ol.offsetHeight > 0)
    .map((ol) => getComputedStyle(ol).borderTopWidth)"""


@pytest.mark.parametrize("main", ["Jitendex", "JMdict", "KANJIDIC"], ids=["first", "middle", "last"])
def test_hidden_main_dictionary_leaves_no_stray_separator(open_card, main):
    """Anki Miner's sibling rule still matches a wrapper whose dictionary hideCorrectDefinition hid."""
    stacked = envelope("Jitendex", "to eat") + envelope("JMdict", "to eat; to live on") + envelope("KANJIDIC", "eat")
    fields = {"Expression": "食べる", "MainDefinition": envelope(main, "to eat"), "Glossary": stacked + STACKED_STYLE}
    card = open_card(fields)
    card.page.keyboard.press("ArrowRight")
    assert card.page.inner_text(".def-info").startswith("Glossaries")
    assert card.page.evaluate(GLOSSARY_SEPARATORS) == ["0px", "1px"]
    assert card.errors == []


def test_hidden_glossary_wrapper_keeps_the_style_the_primary_uses(open_card):
    """A <style> inside a hidden dictionary's wrapper still styles the Definition, so the cleanup keeps it."""
    style = '<style>.yomitan-glossary [data-dictionary="Jitendex"] .probe{color: rgb(1, 2, 3)}</style>'
    glossary = yomitan_single_glossary("Jitendex", "cat", style) + envelope("JMdict", "cat")
    fields = {"Expression": "猫", "MainDefinition": yomitan_single_glossary("Jitendex", "cat"), "Glossary": glossary}
    card = open_card(fields)
    assert card.page.locator("#glossaries").count() == 1
    probe = '#primary [data-dictionary="Jitendex"] .probe'
    assert card.page.eval_on_selector(probe, "e => getComputedStyle(e).color") == "rgb(1, 2, 3)"
    assert card.errors == []


def test_hand_written_glossary_survives_the_hidden_dictionary_cleanup(open_card):
    hand_written = '<div class="yomitan-glossary"><ol><li>my own note</li></ol></div>'
    glossary = hand_written + envelope("Jitendex", "to eat") + envelope("JMdict", "to eat") + STACKED_STYLE
    fields = {"Expression": "食べる", "MainDefinition": envelope("Jitendex", "to eat"), "Glossary": glossary}
    assert "my own note" in open_card(fields).page.inner_text("#glossaries")


JITENDEX = (
    '<div class="yomitan-glossary"><ol data-count="1"><li data-dictionary="Jitendex.org [2026-06-06]"'
    ' data-dictionary-id="jitendex-org-2026-06-06" data-has-styles=""><span class="gloss-tag"'
    ' data-category="popular" title="high priority entry">★</span><i>(Jitendex.org [2026-06-06])</i>'
    '<ul class="gloss-list" data-count="1"><li class="gloss-item"><div class="gloss-content">'
    '<ul class="gloss-sc-ul" data-sc-content="sense-groups" lang="ja"><li class="gloss-sc-li">'
    '<ul class="gloss-sc-ul" data-sc-content="glossary"><li class="gloss-sc-li">to eat</li></ul>'
    "</li></ul></div></li></ul></li></ol></div>"
)
JMDICT = (
    '<div class="yomitan-glossary"><ol data-count="1"><li data-dictionary="JMdict [2026-06-28]"'
    ' data-dictionary-id="jmdict-2026-06-28"><i>(JMdict [2026-06-28])</i><ul class="gloss-list" data-count="1">'
    '<li class="gloss-item"><div class="gloss-content"><ul class="gloss-sc-ul" data-sc-content="glossary" lang="en">'
    '<li class="gloss-sc-li">to eat</li><li class="gloss-sc-li">to live on</li></ul></div></li></ul></li></ol></div>'
)
ANKI_MINER_STYLE = "<style>.yomitan-glossary{--anki-miner-owned-style: 1;}</style>"


def test_anki_miner_list_style_turns_off_lapis_jmdict_separators(open_card):
    """Anki Miner's inline rule ties Lapis's nested " | " rule on specificity and wins by coming later."""
    style = (
        "<style>.yomitan-glossary ol[data-count] li.gloss-sc-li{display: list-item;}"
        ".yomitan-glossary ol[data-count] li.gloss-sc-li::before{content: none;}</style>"
    )
    page = open_card({"Expression": "食べる", "MainDefinition": JMDICT + style}).page
    second = '#primary [data-sc-content="glossary"] > li:nth-child(2)'
    assert page.eval_on_selector(second, "e => getComputedStyle(e, '::before').content") == "none"


def test_japanese_anki_miner_back_runs_lapis_definition_and_pitch_code(open_card):
    """Anki Miner's real ja output (Lapis preset): Yomitan envelopes + style tail, <ul> Frequency, romaji categories."""
    card = open_card(
        {
            "Expression": "食べる",
            "ExpressionFurigana": "食[た]べる",
            "ExpressionReading": "たべる",
            "Sentence": "美味しい料理を<b>食べる</b>",
            "SentenceFurigana": "美味[おい]しい 料理[りょうり]を<b> 食[た]べる</b>",
            "MainDefinition": JITENDEX + ANKI_MINER_STYLE,
            "Glossary": JITENDEX + JMDICT + ANKI_MINER_STYLE,
            "PitchPosition": "0,2",
            "PitchCategories": "heiban,kifuku",
            "Frequency": "<ul><li>JPDB v2.2 Kana Frequency: 1031</li><li>Jiten Frequency: 1203</li></ul>",
            "FreqSort": "1110",
            "MiscInfo": "Night Train — Episode 3 @ 00:12:34",
        }
    )
    page = card.page
    assert card.errors == []
    assert page.inner_text(".def-info") == "Primary Definition 1/2"
    shown = page.eval_on_selector_all(
        "#glossaries li[data-dictionary]",
        "els => els.filter(e => getComputedStyle(e).display !== 'none').map(e => e.dataset.dictionary)",
    )
    assert shown == ["JMdict [2026-06-28]"]
    assert page.locator(".pitch .pitch-item.heiban").count() == 1
    assert page.locator(".pitch .pitch-item.kifuku").count() == 1
    assert page.locator(".sentence b.heiban").count() == 1
    assert page.locator(".freq-list-container li").count() == 2
