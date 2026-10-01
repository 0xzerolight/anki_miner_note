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
