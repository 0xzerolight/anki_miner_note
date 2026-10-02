from collections.abc import Callable, Iterator, Mapping
from pathlib import Path

import pytest
from anki.collection import Collection
from playwright.sync_api import Browser, sync_playwright

import genapkg
from cards import CardPage, import_package, page_html, render_note

OpenCard = Callable[..., CardPage]


@pytest.fixture(scope="session")
def apkg_path(tmp_path_factory) -> Path:
    return genapkg.build_package(tmp_path_factory.mktemp("dist") / "anki-miner-note-test.apkg")


@pytest.fixture(scope="session")
def collection(apkg_path, tmp_path_factory) -> Iterator[Collection]:
    col = Collection(str(tmp_path_factory.mktemp("collection") / "collection.anki2"))
    import_package(col, apkg_path)
    yield col
    col.close()


@pytest.fixture(scope="session")
def browser() -> Iterator[Browser]:
    with sync_playwright() as playwright:
        chromium = playwright.chromium.launch()
        yield chromium
        chromium.close()


@pytest.fixture
def open_card(browser, collection) -> Iterator[OpenCard]:
    opened = []

    def _open(
        fields: Mapping[str, str],
        *,
        card_type: str | None = None,
        side: str = "back",
        mobile: bool = False,
        night: bool = False,
        width: int | None = None,
    ) -> CardPage:
        rendered = render_note(collection, fields, card_type)
        # Set before the content loads: Lapis's setDHHeight() sizes the picture once, at load.
        page = browser.new_page(viewport={"width": width or (390 if mobile else 1280), "height": 900})
        card = CardPage(page)
        page.on("pageerror", lambda exc: card.errors.append(str(exc)))
        page.on(
            "console",
            lambda msg: (
                card.errors.append(msg.text)
                if msg.type == "error" and "Failed to load resource" not in msg.text
                else None
            ),
        )
        page.set_content(page_html(rendered.back if side == "back" else rendered.front, mobile=mobile, night=night))
        opened.append(page)
        return card

    yield _open
    for page in opened:
        page.close()
