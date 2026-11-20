from typing import Sequence

from anki.cards import CardId
from anki.collection import BrowserColumns, Collection
from anki.notes import Note
from aqt import gui_hooks
from aqt.browser import Column, ItemId, CellRow, SearchContext
from mock.mock import MagicMock

from extra_browser_columns.column_hooks import ColumnHooks
from extra_browser_columns.column_values import ColumnValues
from tests.conftest import assert_no_hooks, create_note

suspended_key: str = "extra-browser-columns-suspended"
buried_key: str = "extra-browser-columns-buried"
marked_key: str = "extra-browser-columns-marked"


def test_setup_hooks(col: Collection, column_values: ColumnValues):
    assert_no_hooks()
    column_hooks: ColumnHooks = ColumnHooks(lambda: col, column_values)
    column_hooks.setup_hooks()
    assert gui_hooks.browser_did_fetch_columns.count() == 1
    assert gui_hooks.browser_did_fetch_row.count() == 1
    assert gui_hooks.browser_will_search.count() == 1
    assert gui_hooks.browser_did_search.count() == 1
    column_hooks.remove_hooks()
    assert_no_hooks()


def __column(key: str, label: str, cards_mode_tooltip: str, notes_mode_tooltip: str) -> Column:
    return Column(
        key=key,
        cards_mode_label=label,
        notes_mode_label=label,
        sorting_cards=BrowserColumns.SORTING_DESCENDING,
        sorting_notes=BrowserColumns.SORTING_DESCENDING,
        uses_cell_font=False,
        alignment=BrowserColumns.ALIGNMENT_CENTER,
        cards_mode_tooltip=cards_mode_tooltip,
        notes_mode_tooltip=notes_mode_tooltip
    )


# noinspection PyUnusedLocal
def test_add_columns(column_hooks: ColumnHooks):
    columns: dict[str, Column] = {}
    gui_hooks.browser_did_fetch_columns(columns)
    assert columns == {
        suspended_key: __column(suspended_key, "Suspended", "Card is suspended", "Note has suspended cards"),
        buried_key: __column(buried_key, "Buried", "Card is buried", "Note has buried cards"),
        marked_key: __column(marked_key, "Marked", "Note is marked", "Note is marked"),
    }


def __fetch_row(item_id: ItemId, is_note: bool) -> list[str]:
    columns: Sequence[str] = ["noteFld", suspended_key, buried_key, marked_key]
    row: CellRow = CellRow.generic(len(columns), "init text")
    gui_hooks.browser_did_fetch_row(item_id, is_note, row, columns)
    return [cell.text for cell in row.cells]


# noinspection PyUnusedLocal
def test_modify_row_cards_mode(col: Collection, column_hooks: ColumnHooks):
    plain_note: Note = create_note(col, "plain")
    marked_note: Note = create_note(col, "marked", tags=["marked"])
    suspended_card, buried_card = marked_note.card_ids()
    col.sched.suspend_cards([suspended_card])
    col.sched.bury_cards([buried_card])
    assert __fetch_row(plain_note.card_ids()[0], is_note=False) == ["init text", "", "", ""]
    assert __fetch_row(suspended_card, is_note=False) == ["init text", "✓", "", "✓"]
    assert __fetch_row(buried_card, is_note=False) == ["init text", "", "✓", "✓"]


# noinspection PyUnusedLocal
def test_modify_row_notes_mode(col: Collection, column_hooks: ColumnHooks):
    plain_note: Note = create_note(col, "plain")
    suspended_note: Note = create_note(col, "suspended")
    marked_note: Note = create_note(col, "marked", tags=["marked"])
    col.sched.suspend_cards([suspended_note.card_ids()[0]])
    assert __fetch_row(plain_note.id, is_note=True) == ["init text", "", "", ""]
    assert __fetch_row(suspended_note.id, is_note=True) == ["init text", "✓", "", ""]
    assert __fetch_row(marked_note.id, is_note=True) == ["init text", "", "", "✓"]


def __search(col: Collection, column_key: str, is_note: bool, reverse: bool) -> Sequence[ItemId]:
    browser: MagicMock = MagicMock()
    browser._switch.isChecked.return_value = is_note
    column: Column = Column(key=column_key)
    context: SearchContext = SearchContext("", browser, column, reverse, addon_metadata={})
    gui_hooks.browser_will_search(context)
    assert context.order == col.get_browser_column("noteFld")
    context.ids = col.find_notes("", context.order, reverse) if is_note \
        else col.find_cards("", context.order, reverse)
    gui_hooks.browser_did_search(context)
    return context.ids


def __note_fronts(col: Collection, note_ids: Sequence[ItemId]) -> list[str]:
    return [col.get_note(note_id)["Front"] for note_id in note_ids]


# noinspection PyUnusedLocal
def test_sort_notes_mode(col: Collection, column_hooks: ColumnHooks):
    create_note(col, "a")
    create_note(col, "b", tags=["marked"])
    create_note(col, "c")
    create_note(col, "d", tags=["marked"])
    assert __note_fronts(col, __search(col, marked_key, is_note=True, reverse=True)) == ["d", "b", "c", "a"]
    assert __note_fronts(col, __search(col, marked_key, is_note=True, reverse=False)) == ["a", "c", "b", "d"]


# noinspection PyUnusedLocal
def test_sort_cards_mode(col: Collection, column_hooks: ColumnHooks):
    note_a: Note = create_note(col, "a")
    note_b: Note = create_note(col, "b")
    suspended_card: ItemId = note_b.card_ids()[1]
    col.sched.suspend_cards([suspended_card])
    ids: Sequence[ItemId] = __search(col, suspended_key, is_note=False, reverse=True)
    assert ids[0] == suspended_card
    assert set(ids[1:]) == set(note_a.card_ids()) | {note_b.card_ids()[0]}
    ids = __search(col, suspended_key, is_note=False, reverse=False)
    assert ids[-1] == suspended_card


# noinspection PyUnusedLocal
def test_sort_by_foreign_column(col: Collection, column_hooks: ColumnHooks):
    create_note(col, "a", tags=["marked"])
    browser: MagicMock = MagicMock()
    column: Column = col.get_browser_column("noteCrt")
    context: SearchContext = SearchContext("", browser, column, False, addon_metadata={})
    gui_hooks.browser_will_search(context)
    assert context.order == column
    ids: list[ItemId] = [CardId(3), CardId(1), CardId(2)]
    context.ids = ids
    gui_hooks.browser_did_search(context)
    assert context.ids == ids
