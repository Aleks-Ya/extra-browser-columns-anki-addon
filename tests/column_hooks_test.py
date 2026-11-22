from typing import Sequence, Callable

from anki.cards import CardId
from anki.collection import BrowserColumns, Collection
from anki.consts import CARD_TYPE_LRN, QUEUE_TYPE_LRN, CARD_TYPE_REV, QUEUE_TYPE_REV
from anki.notes import Note
from aqt import gui_hooks
from aqt.browser import Column, ItemId, CellRow, SearchContext
from aqt.qt import Qt
from mock.mock import MagicMock

from extra_browser_columns.column_hooks import ColumnHooks
from extra_browser_columns.column_values import ColumnValues
from tests.conftest import assert_no_hooks, create_note, set_card_state

new_key: str = "extra-browser-columns-new"
learning_key: str = "extra-browser-columns-learning"
review_key: str = "extra-browser-columns-review"
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
    assert gui_hooks.browser_will_show.count() == 1
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
        new_key: __column(new_key, "New", "Card is new", "Note has new cards"),
        learning_key: __column(learning_key, "Learning", "Card is in learning", "Note has learning cards"),
        review_key: __column(review_key, "Review", "Card is in review", "Note has review cards"),
        suspended_key: __column(suspended_key, "Suspended", "Card is suspended", "Note has suspended cards"),
        buried_key: __column(buried_key, "Buried", "Card is buried", "Note has buried cards"),
        marked_key: __column(marked_key, "Marked", "Note is marked", "Note is marked"),
    }


def __fetch_row(item_id: ItemId, is_note: bool) -> list[str]:
    columns: Sequence[str] = ["noteFld", new_key, learning_key, review_key, suspended_key, buried_key, marked_key]
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
    learning_card, review_card = plain_note.card_ids()
    set_card_state(col, learning_card, CARD_TYPE_LRN, QUEUE_TYPE_LRN)
    set_card_state(col, review_card, CARD_TYPE_REV, QUEUE_TYPE_REV)
    assert __fetch_row(learning_card, is_note=False) == ["init text", "", "✓", "", "", "", ""]
    assert __fetch_row(review_card, is_note=False) == ["init text", "", "", "✓", "", "", ""]
    assert __fetch_row(suspended_card, is_note=False) == ["init text", "✓", "", "", "✓", "", "✓"]
    assert __fetch_row(buried_card, is_note=False) == ["init text", "✓", "", "", "", "✓", "✓"]


# noinspection PyUnusedLocal
def test_modify_row_notes_mode(col: Collection, column_hooks: ColumnHooks):
    plain_note: Note = create_note(col, "plain")
    suspended_note: Note = create_note(col, "suspended")
    marked_note: Note = create_note(col, "marked", tags=["marked"])
    col.sched.suspend_cards([suspended_note.card_ids()[0]])
    for card_id in marked_note.card_ids():
        set_card_state(col, card_id, CARD_TYPE_REV, QUEUE_TYPE_REV)
    assert __fetch_row(plain_note.id, is_note=True) == ["init text", "✓", "", "", "", "", ""]
    assert __fetch_row(suspended_note.id, is_note=True) == ["init text", "✓", "", "", "✓", "", ""]
    assert __fetch_row(marked_note.id, is_note=True) == ["init text", "", "", "✓", "", "", "✓"]


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
def test_sort_cards_mode_review(col: Collection, column_hooks: ColumnHooks):
    note_a: Note = create_note(col, "a")
    note_b: Note = create_note(col, "b")
    review_card: ItemId = note_a.card_ids()[0]
    set_card_state(col, review_card, CARD_TYPE_REV, QUEUE_TYPE_REV)
    ids: Sequence[ItemId] = __search(col, review_key, is_note=False, reverse=True)
    assert ids[0] == review_card
    assert set(ids[1:]) == {note_a.card_ids()[1]} | set(note_b.card_ids())
    ids = __search(col, review_key, is_note=False, reverse=False)
    assert ids[-1] == review_card


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


def __double_click_header_border(column_key: str, content_width: int) -> MagicMock:
    browser: MagicMock = MagicMock()
    browser.table._model.column_at_section.side_effect = \
        lambda section: MagicMock(key=column_key) if section == 3 else None
    view: MagicMock = browser.table._view
    view.sizeHintForColumn.return_value = content_width
    header: MagicMock = view.horizontalHeader.return_value
    header.minimumSectionSize.return_value = 50
    gui_hooks.browser_will_show(browser)
    slot: Callable[[int], None] = header.sectionHandleDoubleClicked.connect.call_args.args[0]
    slot(3)
    return header


# noinspection PyUnusedLocal
def test_fit_column_to_cells(column_hooks: ColumnHooks):
    header: MagicMock = __double_click_header_border(suspended_key, content_width=18)
    header.resizeSection.assert_called_once_with(3, 50)
    header = __double_click_header_border(marked_key, content_width=70)
    header.resizeSection.assert_called_once_with(3, 70)


# noinspection PyUnusedLocal
def test_fit_foreign_column(column_hooks: ColumnHooks):
    header: MagicMock = __double_click_header_border("noteFld", content_width=18)
    header.resizeSection.assert_not_called()


def __show_browser(column_key: str, section_size: int) -> tuple[Callable[..., object], MagicMock]:
    browser: MagicMock = MagicMock()
    model: MagicMock = browser.table._model
    model.column_at_section.return_value = MagicMock(key=column_key)
    original_header_data: MagicMock = model.headerData
    original_header_data.return_value = "original"
    header: MagicMock = browser.table._view.horizontalHeader.return_value
    header.sectionSize.return_value = section_size
    header.sectionSizeHint.return_value = 93
    gui_hooks.browser_will_show(browser)
    return model.headerData, original_header_data


# noinspection PyUnusedLocal
def test_left_align_clipped_label(column_hooks: ColumnHooks):
    header_data, original_header_data = __show_browser(suspended_key, section_size=50)
    assert header_data(3, Qt.Orientation.Horizontal, Qt.ItemDataRole.TextAlignmentRole) == \
           (Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter).value
    original_header_data.assert_not_called()


# noinspection PyUnusedLocal
def test_keep_alignment_of_not_clipped_label(column_hooks: ColumnHooks):
    header_data, original_header_data = __show_browser(suspended_key, section_size=93)
    assert header_data(3, Qt.Orientation.Horizontal, Qt.ItemDataRole.TextAlignmentRole) == "original"
    original_header_data.assert_called_once_with(3, Qt.Orientation.Horizontal, Qt.ItemDataRole.TextAlignmentRole)


# noinspection PyUnusedLocal
def test_keep_alignment_of_foreign_column(column_hooks: ColumnHooks):
    header_data, original_header_data = __show_browser("noteFld", section_size=50)
    assert header_data(3, Qt.Orientation.Horizontal, Qt.ItemDataRole.TextAlignmentRole) == "original"


# noinspection PyUnusedLocal
def test_keep_label_text(column_hooks: ColumnHooks):
    header_data, original_header_data = __show_browser(suspended_key, section_size=50)
    assert header_data(3, Qt.Orientation.Horizontal) == "original"
    original_header_data.assert_called_once_with(3, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
