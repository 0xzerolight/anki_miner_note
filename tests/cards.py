"""Render Anki Miner Note cards with Anki's own template engine, for viewing in Chromium."""

import base64
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from anki.collection import Collection, ImportAnkiPackageOptions, ImportAnkiPackageRequest
from playwright.sync_api import Page

import genapkg

ARTIFACTS = Path(__file__).resolve().parent.parent / "test-artifacts"
# A 16:9 picture like the screenshot Anki Miner puts on every card (inline, so the test needs no media).
PICTURE = '<img src="data:image/svg+xml;base64,{}">'.format(
    base64.b64encode(
        b'<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360"><rect width="640" height="360"/></svg>'
    ).decode()
)
CARD_TYPES: tuple[str | None, ...] = (None, "IsWordAndSentenceCard", "IsClickCard", "IsSentenceCard", "IsAudioCard")


@dataclass(frozen=True)
class Rendered:
    front: str
    back: str


@dataclass
class CardPage:
    page: Page
    errors: list[str] = field(default_factory=list)


def import_package(col: Collection, apkg: Path) -> None:
    """Import like a user updating: "Merge note types" on, scheduling off."""
    col.import_anki_package(
        ImportAnkiPackageRequest(
            package_path=str(apkg),
            options=ImportAnkiPackageOptions(merge_notetypes=True, with_scheduling=False),
        )
    )


def render_note(col: Collection, fields: Mapping[str, str], card_type: str | None = None) -> Rendered:
    """Add a note with these fields (plus the card-type toggle) and return its rendered sides, CSS included."""
    note = col.new_note(col.models.by_name(genapkg.MODEL_NAME))
    for name, value in fields.items():
        if name == "Tags":  # Anki's special field: the note's space-separated tags
            note.tags = value.split()
        else:
            note[name] = value
    if card_type is not None:
        note[card_type] = "x"
    col.add_note(note, col.decks.id("Render tests"))
    card = note.cards()[0]
    return Rendered(front=card.question(), back=card.answer())


def page_html(card_html: str, *, mobile: bool, night: bool) -> str:
    """Wrap one side the way Anki's reviewer does: html.mobile, body.card(.nightMode), #qa."""
    html_class = "mobile" if mobile else ""
    body_class = "card nightMode night_mode" if night else "card"
    return (
        f'<!doctype html><html class="{html_class}"><head><meta charset="utf-8"></head>'
        f'<body class="{body_class}"><div id="qa">{card_html}</div></body></html>'
    )
