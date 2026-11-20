from pathlib import Path
from typing import Generator

import pytest
from anki.collection import Collection
from anki.models import NotetypeDict
from anki.notes import Note
from aqt import gui_hooks

from extra_browser_columns.column_hooks import ColumnHooks
from extra_browser_columns.column_values import ColumnValues


@pytest.fixture
def col(tmp_path: Path) -> Generator[Collection, None, None]:
    col: Collection = Collection(str(tmp_path / "collection.anki2"))
    yield col
    col.close()


@pytest.fixture
def column_values(col: Collection) -> ColumnValues:
    return ColumnValues(lambda: col)


@pytest.fixture
def column_hooks(col: Collection, column_values: ColumnValues) -> Generator[ColumnHooks, None, None]:
    column_hooks: ColumnHooks = ColumnHooks(lambda: col, column_values)
    column_hooks.setup_hooks()
    yield column_hooks
    column_hooks.remove_hooks()


def create_note(col: Collection, front: str, tags: list[str] = None) -> Note:
    """Creates a note having 2 cards ("Basic (and reversed card)" note type)."""
    note_type: NotetypeDict = col.models.by_name("Basic (and reversed card)")
    note: Note = col.new_note(note_type)
    note["Front"] = front
    note["Back"] = f"{front} back"
    note.tags = tags if tags else []
    col.add_note(note, col.decks.id_for_name("Default"))
    return note


def assert_no_hooks() -> None:
    assert gui_hooks.browser_did_fetch_columns.count() == 0
    assert gui_hooks.browser_did_fetch_row.count() == 0
    assert gui_hooks.browser_will_search.count() == 0
    assert gui_hooks.browser_did_search.count() == 0
