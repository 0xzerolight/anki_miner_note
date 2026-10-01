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
    "Pinyin",
    "Jyutping",
    "Traditional",
    "MeasureWord",
    "Hanja",
    "HanViet",
    "Gender",
    "Article",
    "Plural",
    "PartOfSpeech",
    "AspectPair",
    "Root",
    "Binyan",
    "Transliteration",
    "Romanization",
    "Colloquial",
    "PresentStem",
    "Classifier",
    "Affixes",
    "Formal",
    "Grammar",
    "Segmentation",
)

# Shipped in the example deck: 14 samples, one per script group. ja_kanji, de_compound, id, en and all_extras
# are test-only.
# Like Anki Miner today, most samples leave Language empty: the root lang then comes from the lang="…"
# Anki Miner writes inside the word or sentence, else from the script of the text.
SAMPLES: tuple[Sample, ...] = (
    Sample(
        "ja",
        "ja",
        {
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
        },
    ),
    Sample(
        "ja_kanji",
        "ja",
        {
            "Expression": "大丈夫",
            "ExpressionReading": "だいじょうぶ",
            "Sentence": "<b>大丈夫</b>？",
            "MainDefinition": "all right; OK",
        },
        ship=False,
    ),
    Sample(
        "zh_hans",
        "zh-Hans",
        {
            "Expression": "骨头",
            "Sentence": '<span lang="zh-Hans">他把<b>骨头</b>扔给了狗。</span>',
            "SentenceTranslation": "He threw the bone to the dog.",
            "MainDefinition": "bone",
            "Pinyin": '<span style="color: #e30000">gǔ</span><span style="color: #888888">tou</span>',
            "Traditional": "骨頭",
            "MeasureWord": "根 gēn",
            "FreqSort": "4210",
        },
    ),
    Sample(
        "zh_hant",
        "zh-Hant",
        {
            "Expression": "直接",
            "Sentence": '<span lang="zh-Hant">他<b>直接</b>回家了。</span>',
            "MainDefinition": "direct; immediate",
            "Pinyin": '<span style="color: #02b31c">zhí</span><span style="color: #1510f0">jiē</span>',
        },
    ),
    Sample(
        "yue",
        "zh-Hant",
        {
            "Expression": "嘢",
            "Sentence": '<span lang="zh-Hant">你食咗<b>嘢</b>未呀？</span>',  # yue_card_lang is always zh-Hant
            "MainDefinition": "thing; stuff",
            "Jyutping": '<span style="color: #e30000">je5</span>',
            "MeasureWord": "啲 di1",
        },
    ),
    Sample(
        "ko",
        "ko",
        {
            "Expression": "학교",
            "Sentence": "매일 <b>학교</b>에 가요.",
            "MainDefinition": "school",
            "Hanja": "學校",
        },
    ),
    Sample(
        "vi",
        "vi",
        {
            "Language": "vi",
            "Expression": "trường học",
            "Sentence": "Tôi đi <b>trường học</b> mỗi ngày.",
            "MainDefinition": "school",
            "HanViet": "場學",
        },
    ),
    Sample(
        "de",
        "",
        {
            "Expression": "Hund",
            "Sentence": "Der <b>Hund</b> schläft.",
            "SentenceTranslation": "The dog is sleeping.",
            "MainDefinition": "dog",
            "Gender": "der",
            "Plural": "Hunde",
            "PartOfSpeech": "NOUN",
        },
    ),
    Sample(
        "de_compound",
        "de",
        {
            "Language": "de",
            "Expression": "Donaudampfschifffahrtsgesellschaftskapitän",
            "Sentence": "Sein Großvater war <b>Donaudampfschifffahrtsgesellschaftskapitän</b>.",
            "MainDefinition": "Danube steamship company captain",
            "Gender": "der",
            "PartOfSpeech": "NOUN",
        },
        ship=False,
    ),
    Sample(
        "pl",
        "pl",
        {
            "Language": "pl",
            "Expression": "stół",
            "Sentence": "Książka leży na <b>stole</b>.",
            "MainDefinition": "table",
            "Gender": "m inan",
            "PartOfSpeech": "NOUN",
        },
    ),
    Sample(
        "ru",
        "",
        {
            "Expression": "читать",
            "Sentence": "Я люблю <b>читать</b> по вечерам.",
            "MainDefinition": "to read",
            "AspectPair": "прочитать",
            "PartOfSpeech": "VERB",
        },
    ),
    Sample(
        "el",
        "el",
        {
            "Language": "el",
            "Expression": "θάλασσα",
            "Sentence": "Η <b>θάλασσα</b> είναι ήρεμη.",
            "MainDefinition": "sea",
            "Gender": "η",
            "PartOfSpeech": "NOUN",
        },
    ),
    Sample(
        "ar",
        "ar",
        {
            "Expression": '<div dir="rtl" lang="ar">كتاب</div>',
            "ExpressionReading": "كِتَاب",
            "Sentence": '<div dir="rtl" lang="ar">قرأت <b>كتابا</b> جميلا.</div>',
            "MainDefinition": "book",
            "Root": "ك ت ب",
            "Grammar": "noun, masculine",
            "Segmentation": "كتاب",
        },
    ),
    Sample(
        "fa",
        "fa",
        {
            "Expression": '<div dir="rtl" lang="fa">گفتن</div>',
            "Sentence": '<div dir="rtl" lang="fa">او چیزی <b>نگفت</b>.</div>',
            "MainDefinition": "to say",
            "Romanization": "goftan",
            "Colloquial": "goftan",
            "PresentStem": "گو",
        },
    ),
    Sample(
        "he",
        "he",
        {
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
        },
    ),
    Sample(
        "th",
        "th",
        {
            "Expression": "โรงเรียน",
            "Sentence": "ฉันไป<b>โรงเรียน</b>ทุกวันตั้งแต่เช้าจนเย็นโดยไม่หยุดพักเลย",
            "MainDefinition": "school",
            "Classifier": "แห่ง",
        },
    ),
    Sample(
        "id",
        "id",
        {
            "Language": "id",
            "Expression": "bermain",
            "Sentence": "Anak-anak <b>bermain</b> di taman.",
            "MainDefinition": "to play",
            "Root": "main",
            "Affixes": "ber-",
            "Formal": "bermain",
            "PartOfSpeech": "VERB",
        },
        ship=False,
    ),
    Sample(
        "en",
        "",
        {
            "Expression": "serendipity",
            "Sentence": "Meeting her there was pure <b>serendipity</b>.",
            "MainDefinition": "the occurrence of events by chance in a happy way",
        },
        ship=False,
    ),
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
