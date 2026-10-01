"""Front script: the click card's toggle and the audio card's hidden word, whatever the sentence holds."""

import pytest

pytestmark = pytest.mark.render

# Subtitles use ` as an apostrophe (Anki Miner keeps it); ${, \u and &#x27; can appear in any sentence.
SENTENCES = [
    ("Perche` non sei <b>venuto</b> ieri?", "Perche` non sei venuto ieri?"),
    ("Він купив <b>м`ясо</b> на ринку.", "Він купив м`ясо на ринку."),
    ("Copy the <b>dog</b> photo to C:\\users\\tom first.", "Copy the dog photo to C:\\users\\tom first."),
    ("The <b>dog</b> costs ${price} today.", "The dog costs ${price} today."),
    ("L&#x27;home ${a} <b>llibre</b>", "L'home ${a} llibre"),
]


@pytest.mark.parametrize(
    "sentence,shown", SENTENCES, ids=["it-backtick", "uk-backtick", "backslash-u", "dollar-brace", "entity"]
)
def test_sentence_text_cannot_break_the_front_script(open_card, sentence, shown):
    fields = {"Expression": "x", "Sentence": sentence}
    audio = open_card(fields, card_type="IsAudioCard", side="front")
    assert audio.errors == []
    assert audio.page.inner_text("#audio b") == "[...]"
    click = open_card(fields, card_type="IsClickCard", side="front")
    click.page.click("#click")
    assert click.errors == []
    assert click.page.inner_text("#click .front-sentence") == shown
    click.page.click("#click")
    assert click.page.inner_text("#click .front-vocab") == "x"


@pytest.mark.parametrize("blank", ["<br>", " ", "<div><br></div>"], ids=["br", "space", "div-br"])
def test_blank_click_toggle_leaves_the_front_script_working(open_card, blank):
    """Anki renders {{#IsClickCard}} empty for a toggle holding only <br> or spaces; the script must agree."""
    fields = {"Expression": "Hund", "Sentence": "Die <b>Hunde</b> bellen.", "IsClickCard": blank, "IsAudioCard": "x"}
    card = open_card(fields, side="front")
    assert card.page.locator("#click").count() == 0
    assert card.errors == []
    assert card.page.inner_text("#audio b") == "[...]"


def test_copy_shortcut_does_not_flip_the_click_card(open_card):
    fields = {"Expression": "Hund", "Sentence": "Die Hunde bellen."}
    page = open_card(fields, card_type="IsClickCard", side="front").page
    page.click("#click")
    page.keyboard.press("Control+c")
    assert page.locator("#click .front-sentence").count() == 1
    page.keyboard.press("c")
    assert page.locator("#click .front-vocab").count() == 1
