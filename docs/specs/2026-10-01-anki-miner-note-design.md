# Anki Miner Note: design

Status: approved 2026-10-01. Scope: v1, the note type repo only.

## Why this exists

Japanese sentence miners can choose between several polished note types (Lapis, Kiku, Senren,
JPMN). Learners of other languages have none:

- Lapis, Kiku, Senren and JPMN are Japanese-only by stated policy. Requests for Korean
  ([lapis#126](https://github.com/donkuri/lapis/issues/126)), Mandarin
  ([Senren#67](https://github.com/BrenoAqua/Senren/issues/67)) and German
  ([kiku#74](https://github.com/youyoumu/kiku/issues/74)) were declined or closed.
- Migaku ships per-language note types for 12 languages, but they need a paid subscription.
- LapisChinese and about nine other forks each cover one language and are personal projects.

Anki Miner mines 32 languages, and its non-Japanese users ask which note type to use. This repo
gives them one answer: a single note type, based on Lapis, that works for every language Anki
Miner supports, Japanese included.

## Decisions

| Question | Decision |
|---|---|
| Audience | Anki Miner first. Yomitan and asbplayer users can fill the core fields; the per-language extras show only when something fills them. |
| Japanese | Full parity with Lapis: furigana, pitch display, the same card types. |
| Structure | One note type for every language, not per-language variants. |
| v1 scope | This repo only, private. Anki Miner integration comes later (see the last section). |
| License | GPL-3.0, inherited from Lapis. |

## 1. Repository, build, releases, updates

- The repo is seeded from the full history of [donkuri/lapis](https://github.com/donkuri/lapis)
  at `f4eb29bd`.
  - The `upstream` remote points at Lapis, fetch only, for cherry-picking fixes.
  - The README credits Lapis.
- **Identity**
  - The note type is named `Anki Miner Note`.
  - It gets a new model ID, generated once and never changed. It must differ from Lapis's
    `1667218449922`, so importing never merges into a user's Lapis.
  - The example deck is named `Anki Miner Note`.
- **Build**
  - Lapis's genanki pipeline stays: `build/genapkg.py` reads `build/anki_fields.yaml` and
    `src/{front.html,back.html,styling.css}`. Python dependencies are managed with uv.
  - The per-field editor font `Hiragino Sans Pr6N` is removed from every field.
  - The 22 extras (§2) get Anki's per-field `collapsed: true`, so the editor stays short.
  - If genanki drops unknown field keys, `genapkg.py` patches the model before writing.
- **Example deck**
  - One sample note per script group: ja, zh-Hans, zh-Hant, yue, ko, vi, de, pl, ru, el, ar, fa,
    he, th.
  - Each fills the fields Anki Miner fills for that language.
  - The same notes are the render-test fixtures.
- **Releases**
  - A GitHub Actions workflow builds `Anki-Miner-Note-<version>.apkg` on a `v*` tag.
  - It attaches the file to a draft release.
- **Updating**
  - Users re-import the new `.apkg` in Anki 23.10 or later with "Merge note types" checked.
  - Merging keeps every field and template from both versions
    ([manual](https://docs.ankiweb.net/importing/packaged-decks.html)).
- **Field contract**
  - Fields are append-only: never renamed, removed or reordered.
  - `build/fields.lock` lists the shipped fields in order. A test fails unless the current list is
    the lock plus fields appended at the end.

## 2. Fields

46 fields, in this order.

1. **Lapis core (22), names byte-exact:** Expression, ExpressionFurigana, ExpressionReading,
   ExpressionAudio, SelectionText, MainDefinition, DefinitionPicture, Sentence, SentenceFurigana,
   SentenceAudio, Picture, Glossary, Hint, IsWordAndSentenceCard, IsClickCard, IsSentenceCard,
   IsAudioCard, PitchPosition, PitchCategories, Frequency, FreqSort, MiscInfo.
2. **Added core (2):** SentenceTranslation, Language.
3. **Per-language extras (22)**, each named after Anki Miner's `CardFieldSpec.placeholder` for that
   data:

| Field | Filled for | Anki Miner key |
|---|---|---|
| Pinyin | zh | `expression_pinyin` (HTML, tone colours pre-rendered) |
| Jyutping | yue | `expression_jyutping` (HTML) |
| Traditional | zh | `expression_traditional` |
| MeasureWord | zh, yue | `measure_word` |
| Hanja | ko | `hanja` |
| HanViet | vi | `hanviet` (the Han characters a Sino-Vietnamese word is read from) |
| Gender | de, fr, es, pt, ca, it, el, ru, uk, pl, lt, he, … | `noun_gender` |
| Article | da, it, nl, nb, sv | `noun_article` |
| Plural | de, he, sl, sv | `noun_plural` |
| PartOfSpeech | the spaced languages | `pos` |
| AspectPair | ru, uk, pl, el, hr, sl | `aspect_pair` |
| Root | ar, he, id | `root` |
| Binyan | he | `binyan` |
| Transliteration | he | `transliteration` |
| Romanization | fa | `reading_romanized` |
| Colloquial | fa | `colloquial_form` |
| PresentStem | fa | `present_stem` |
| Classifier | th | `classifier` |
| Affixes | id | `affixes` |
| Formal | id | `formal_form` |
| Grammar | ar | `expression_grammar` |
| Segmentation | ar | `clitic_segmentation` |

**Why these names.** They make the note type work with Anki Miner as it is today, with no app
change:

- **ja**: `preset_for_field_names` (anki_miner `services/note_presets.py`) recognizes any superset
  of the Lapis signature. The full Lapis map applies, including the pitch category format.
- **Every other language**: "Fill in automatically" maps the core fields by keyword
  (`auto_map_fields`) and the extras by placeholder name (`auto_map_profile_fields`).

Known gaps, all closed by the later integration:

- Hebrew's part-of-speech placeholder is `POS`, so it doesn't map to `PartOfSpeech`.
- Thai's Paiboon reading placeholder is `Reading`, which has no field here.
- `Language` stays empty, because Anki Miner has no key for it yet.
- The Lapis preset maps no `SentenceTranslation` for ja; users map it by hand.

## 3. Language, fonts and direction

- **Language tag**
  - The template root carries `lang="{{text:Language}}"`. Values are BCP-47 tags: `ja`,
    `zh-Hans`, `zh-Hant`, `yue`, `ko`, `vi`, `ar`, `fa`, `he`, `th`, `de`, and so on.
  - Every hardcoded `lang="ja"` in Lapis's templates goes; descendants inherit the root `lang`.
- **Inference fallback**
  - When `Language` is empty, an inline script sets the root `lang`. It first takes the first
    `lang="…"` that Anki Miner wrote inside Expression or Sentence (see "Inline tags" below).
    Without one, it guesses from the text of Expression, Sentence, ExpressionFurigana and
    ExpressionReading; the reading fields let a kanji-only Japanese sentence (大丈夫？) still count
    as Japanese.
  - The guess applies the first rule that matches:

    | Text contains | `lang` |
    |---|---|
    | kana, excluding ・ and ー (Chinese uses them in foreign names) | `ja` |
    | Hangul | `ko` |
    | Thai | `th` |
    | Hebrew | `he` |
    | Arabic script with any of `پ چ ژ گ ک ی` | `fa` |
    | Arabic script otherwise | `ar` |
    | Han | `zh` |
    | anything else | no tag |

  - The script must be idempotent: it runs on the front, and again on the back.
- **Inline tags from Anki Miner**
  - Anki Miner wraps RTL word and sentence fields in `<div dir="rtl" lang="…">`, and the Chinese
    sentence in `<span lang="zh-Hans|zh-Hant">` (anki_miner `services/anki_note_builder.py`,
    `_rtl_wrap` and `_lang_wrap`).
  - These inner tags win over the root, and the CSS must not fight them: text inside them takes
    their language's font stack.
- **Without JS** the card stays legible: neutral font stacks, Latin first.
- **Fonts**: CSS `:lang()` rules, system fonts only, nothing bundled.
  - The base stacks for headword, sentence and body are Latin-first, sans and serif. This fixes
    the mixed fonts in Lapis's Mincho-first stack, whose CJK fonts lack č, ł, ş, ő and ț.
  - Each CJK tag gets its own stack, so Han characters take the right regional shapes:
    `:lang(ja)` (Lapis's current stacks move here), `:lang(zh)`/`:lang(zh-Hans)`,
    `:lang(zh-Hant)`, `:lang(yue)` and `:lang(ko)`.
  - Japanese keeps Lapis's exact stacks, and Chinese and Cantonese put CJK faces first in the
    serif stack. Either way, CJK punctuation (、。“ ” ……) keeps its full-width forms.
  - `:lang(ar)`, `:lang(fa)` and `:lang(he)` get an Arabic or Hebrew stack. `:lang(th)` gets a
    Thai stack and a taller line height. These faces lead for their own language.
  - The front's two `#hint` blocks carry `dir="auto"`, so an English hint on an Arabic card stays
    left-to-right.
- **Direction**
  - For ar, fa and he, the word and sentence blocks are right-to-left.
  - The glossary and definition stay left-to-right, because their dictionaries are usually
    English.

## 4. Card layout

- **Front.** Lapis's card types are unchanged: the default word card, word+sentence, click,
  sentence, and audio, toggled by the `Is…Card` fields.
- **Back.** Lapis's layout, definitions, picture, audio, frequency and pitch display stay as they
  are. Each addition is wrapped in `{{#Field}}…{{/Field}}`, so an empty field leaves no markup:
  - **Reading line** under the headword: Pinyin and Jyutping (raw HTML, not `text:`),
    Romanization, Transliteration.
  - **Alternate forms**: Traditional, Hanja, HanViet. Each carries its own `lang`
    (`zh-Hant`, `ko`, `zh-Hant`), so it takes the matching CJK font.
  - **Chip row**: Article, Gender, Plural, PartOfSpeech, MeasureWord, Classifier, AspectPair, Root,
    Binyan, PresentStem, Colloquial, Formal, Affixes, Segmentation, Grammar. Each chip has a short
    English label; translating the labels is out of scope for v1.
  - **SentenceTranslation**, muted, under the sentence.
- **Gender colours, no JS**
  - The chip carries `data-gender="{{text:Gender}}"`, and CSS attribute selectors (`i` flag)
    colour it from Anki Miner's current labels:
    - masculine: `masculine`, `der`, `el`, `le`, `o`, `ο`, `м.`, `ч.`, `m`, `m pers`, `m anim`,
      `m inan`, `ז׳`
    - feminine: `feminine`, `die`, `la`, `a`, `η`, `ж.`, `f`, `נ׳`
    - neuter: `neuter`, `das`, `το`, `с.`, `n`
    - common: `common`
  - German `die` also marks plural-only nouns; it takes the feminine colour.
  - Unknown values get the neutral chip.
- **Night mode and mobile**: Lapis's `.nightMode` and mobile rules apply to every addition.

## 5. Testing

The tests use Python and uv only.

- **Contract tests (pytest)**
  - The build succeeds, and the model ID equals the constant.
  - The field list is `fields.lock` plus appended fields only.
  - Every `{{Field}}` (including the `#`, `^`, `text:`, `furigana:`, `kana:` and `kanji:` forms) in
    the templates names an existing field.
  - Every extra appears only inside its own `{{#Extra}}` section.
- **Render tests**
  - Use Anki's own Python package (`anki`, pinned): open a temporary `Collection`, import the built
    `.apkg`, and render `card.question()` and `card.answer()` with the note type's CSS. This uses
    Anki's real template engine.
  - For every sample note × card type × light/`.nightMode` × 1280 px/390 px, load the HTML in
    Playwright Chromium and assert:
    - the root `lang` matches the expected value, from `Language` or by inference;
    - ar, fa and he blocks compute `direction: rtl`;
    - an empty extra leaves no element;
    - at 390 px, `scrollWidth ≤ clientWidth`;
    - the console shows no errors.
  - Save screenshots as CI artifacts for review. They are not pixel-diffed, because fonts differ
    between machines.
- **Inference tests**: the inference function runs in the Playwright page on sample strings for
  every row of the §3 table.
- **Update test**
  1. Import the deck.
  2. Build a variant with one appended field.
  3. Re-import it with `merge_notetypes`.
  4. Assert the existing notes keep their field data.
- **Anki Miner mapping check**
  - `scripts/check_anki_miner_mapping.py` is skipped when `anki_miner` can't be imported.
  - It runs `fill_note_type_fields` on `fields.lock` for all 32 languages, with each profile's
    extra specs.
  - It asserts:
    - the core fields map;
    - every language's extras map, except the known gaps in §2;
    - ja resolves to the Lapis preset.
- **Gate**: `scripts/check.sh` runs `ruff`, the contract and render tests, and the mapping check.
  `CLAUDE.md` names it as the Definition-of-Done gate.
- **CI**
  - The workflow installs `fonts-noto-core` and `fonts-noto-cjk` on ubuntu.
  - It runs the gate without the mapping check, builds the `.apkg`, and uploads the screenshots.
- **Manual end-to-end** before the first release:
  1. In a throwaway Anki profile with AnkiConnect, import the deck.
  2. Mine de, pl, zh, ko, ar and ja with Anki Miner under an isolated `ANKI_MINER_HOME`, mapping
     the fields with "Fill in automatically".
  3. Review the cards in the Anki reviewer, and on AnkiDroid if a device is available. iOS stays
     untested in v1.

## Out of scope for v1

- Bundled fonts.
- A settings or theme JS layer like Kiku's or Senren's.
- Rendering tuned for Yomitan's own output.
- Translated labels.
- iOS testing.
- Any change to Anki Miner.
- Making the repo public.

## Later: Anki Miner integration (separate work)

- An `Anki Miner Note` preset that applies to every mining language and writes `Language` (BCP-47,
  from `card_lang`).
- Rename the Hebrew `POS` and Thai `Reading` placeholders to fields that exist here.
- Map `SentenceTranslation` for ja.
- A RESOURCES.md row and a setup-wizard link to the release.
- Optionally, a machine-readable gender value, so §4's label table can go.
