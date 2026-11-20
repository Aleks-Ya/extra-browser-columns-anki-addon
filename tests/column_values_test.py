from anki.cards import CardId
from anki.collection import Collection
from anki.notes import Note

from extra_browser_columns.column_values import ColumnValues, ColumnType
from tests.conftest import create_note


def test_card_mode_not_flagged(col: Collection, column_values: ColumnValues):
    note: Note = create_note(col, "plain")
    card_id: CardId = note.card_ids()[0]
    assert not column_values.is_flagged(ColumnType.SUSPENDED, card_id, is_note=False)
    assert not column_values.is_flagged(ColumnType.BURIED, card_id, is_note=False)
    assert not column_values.is_flagged(ColumnType.MARKED, card_id, is_note=False)


def test_card_mode_suspended(col: Collection, column_values: ColumnValues):
    note: Note = create_note(col, "suspended")
    card_1, card_2 = note.card_ids()
    col.sched.suspend_cards([card_1])
    assert column_values.is_flagged(ColumnType.SUSPENDED, card_1, is_note=False)
    assert not column_values.is_flagged(ColumnType.SUSPENDED, card_2, is_note=False)
    assert not column_values.is_flagged(ColumnType.BURIED, card_1, is_note=False)


def test_card_mode_buried(col: Collection, column_values: ColumnValues):
    note: Note = create_note(col, "buried")
    card_1, card_2 = note.card_ids()
    col.sched.bury_cards([card_1], manual=True)
    col.sched.bury_cards([card_2], manual=False)
    assert column_values.is_flagged(ColumnType.BURIED, card_1, is_note=False)
    assert column_values.is_flagged(ColumnType.BURIED, card_2, is_note=False)
    assert not column_values.is_flagged(ColumnType.SUSPENDED, card_1, is_note=False)


def test_card_mode_marked(col: Collection, column_values: ColumnValues):
    note: Note = create_note(col, "marked", tags=["Marked"])
    card_1, card_2 = note.card_ids()
    assert column_values.is_flagged(ColumnType.MARKED, card_1, is_note=False)
    assert column_values.is_flagged(ColumnType.MARKED, card_2, is_note=False)


def test_card_mode_absent_card(column_values: ColumnValues):
    assert not column_values.is_flagged(ColumnType.SUSPENDED, CardId(123), is_note=False)


def test_note_mode(col: Collection, column_values: ColumnValues):
    plain_note: Note = create_note(col, "plain")
    flagged_note: Note = create_note(col, "flagged", tags=["marked"])
    card_1, card_2 = flagged_note.card_ids()
    col.sched.suspend_cards([card_1])
    col.sched.bury_cards([card_2])
    for column_type in ColumnType:
        assert not column_values.is_flagged(column_type, plain_note.id, is_note=True)
        assert column_values.is_flagged(column_type, flagged_note.id, is_note=True)


def test_flagged_ids(col: Collection, column_values: ColumnValues):
    create_note(col, "plain")
    suspended_note: Note = create_note(col, "suspended")
    buried_note: Note = create_note(col, "buried")
    marked_note: Note = create_note(col, "marked", tags=["marked"])
    suspended_card: CardId = suspended_note.card_ids()[0]
    buried_card: CardId = buried_note.card_ids()[1]
    col.sched.suspend_cards([suspended_card])
    col.sched.bury_cards([buried_card])
    assert column_values.flagged_ids(ColumnType.SUSPENDED, is_note=False) == {suspended_card}
    assert column_values.flagged_ids(ColumnType.BURIED, is_note=False) == {buried_card}
    assert column_values.flagged_ids(ColumnType.MARKED, is_note=False) == set(marked_note.card_ids())
    assert column_values.flagged_ids(ColumnType.SUSPENDED, is_note=True) == {suspended_note.id}
    assert column_values.flagged_ids(ColumnType.BURIED, is_note=True) == {buried_note.id}
    assert column_values.flagged_ids(ColumnType.MARKED, is_note=True) == {marked_note.id}
