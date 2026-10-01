"""Updating = re-importing a newer .apkg with "Merge note types": new fields arrive, user notes keep their data."""

from anki.collection import Collection

import genapkg
from cards import import_package
from samples import EXTRAS


def test_imported_note_type_keeps_collapsed_extras(collection):
    """genanki must carry "collapsed" through to Anki; the YAML alone proves nothing."""
    fields = {field["name"]: field for field in collection.models.by_name(genapkg.MODEL_NAME)["flds"]}
    for name in EXTRAS:
        assert fields[name]["collapsed"] is True, name


def test_merge_import_adds_fields_and_keeps_user_notes(tmp_path):
    path = tmp_path / "collection.anki2"
    col = Collection(str(path))
    import_package(col, genapkg.build_package(tmp_path / "v1.apkg"))

    note = col.new_note(col.models.by_name(genapkg.MODEL_NAME))
    note["Expression"] = "user word"
    note["Sentence"] = "user sentence"
    note["Gender"] = "der"
    col.add_note(note, col.decks.id("Mining"))
    note_id = note.id

    model = genapkg.build_model()
    model.fields.append({"name": "MergeProbe", "collapsed": True})
    import_package(col, genapkg.build_package(tmp_path / "v2.apkg", model=model))
    col.close()

    # pylib caches note types; reopen to read what the import actually stored.
    col = Collection(str(path))
    try:
        names = col.models.field_names(col.models.by_name(genapkg.MODEL_NAME))
        assert names == genapkg.field_names() + ["MergeProbe"]
        kept = col.get_note(note_id)
        assert (kept["Expression"], kept["Sentence"], kept["Gender"], kept["MergeProbe"]) == (
            "user word",
            "user sentence",
            "der",
            "",
        )
    finally:
        col.close()
