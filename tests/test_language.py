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


@pytest.mark.render
@pytest.mark.parametrize(
    "sentence",
    [
        "The <b>dog</b> is called حبيبي, my friend.",
        "Sushi (寿司) is what the <b>dog</b> ate.",
        "Der <b>Hund</b> heißt שלום.",
    ],
    ids=["arabic", "han", "hebrew"],
)
def test_latin_headword_keeps_the_card_untagged(open_card, sentence):
    page = open_card({"Expression": "dog", "Sentence": sentence}).page
    assert page.get_attribute("#lapis", "lang") == ""
    assert page.eval_on_selector(".sentence", "e => getComputedStyle(e).direction") == "ltr"


@pytest.mark.render
@pytest.mark.parametrize(
    "fields,expected",
    [
        ({"Expression": "映画", "Sentence": "昨日映画を見ました。"}, "ja"),
        ({"Expression": "學校", "Sentence": "나는 學校에 간다."}, "ko"),
        ({"Expression": "сло́во", "Sentence": "Это <b>слово</b> — سلام."}, ""),
    ],
    ids=["ja-kanji-word", "ko-hanja-word", "ru-with-arabic"],
)
def test_word_fields_gate_the_guess(open_card, fields, expected):
    for side in ("front", "back"):
        assert open_card(fields, side=side).page.get_attribute("#lapis", "lang") == expected
