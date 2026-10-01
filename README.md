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

Import the new `.apkg` with **Merge note types** ticked and **Update note types** set to **Always**. Your notes and their fields are kept. Edits you made to the Styling are replaced, so copy them first and re-apply them after.

## Language

The `Language` field takes a language tag: `ja`, `zh-Hans`, `zh-Hant`, `yue`, `ko`, `ar`, `fa`, `he`, `th`, `de`, and so on.
Left empty, the card guesses the language from the word and sentence.

## Fonts

The card uses fonts already on your device. To change them, edit these variables at the top of the note type's Styling: `--latin-serif`, `--latin-sans`, `--cjk-serif` and `--cjk-sans`. Japanese cards keep Lapis's stacks, so only `--cjk-serif` and `--cjk-sans` change them. The stacks for Chinese, Cantonese, Korean, Arabic, Persian, Hebrew and Thai are in the LANGUAGES section at the end of the Styling.
Lapis's other settings still apply; see [docs/user_settings.md](docs/user_settings.md).

## License

GPL-3.0, like Lapis.
