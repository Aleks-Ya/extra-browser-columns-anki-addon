from anki.cards import CardId
from anki.collection import Collection
from anki.consts import CARD_TYPE_LRN, QUEUE_TYPE_LRN, CARD_TYPE_REV, QUEUE_TYPE_REV, \
    CARD_TYPE_RELEARNING, QUEUE_TYPE_DAY_LEARN_RELEARN, CARD_TYPE_NEW, QUEUE_TYPE_SUSPENDED
from anki.notes import Note

from extra_browser_columns.column_values import ColumnValues, ColumnType
from tests.conftest import create_note, set_card_state


def test_card_mode_plain(col: Collection, column_values: ColumnValues):
    note: Note = create_note(col, "plain")
    card_id: CardId = note.card_ids()[0]
    for column_type in ColumnType:
        assert column_values.is_flagged(column_type, card_id, is_note=False) == (column_type == ColumnType.NEW)


def __flagged_types(column_values: ColumnValues, card_id: CardId) -> set[ColumnType]:
    return {column_type for column_type in ColumnType if column_values.is_flagged(column_type, card_id, is_note=False)}


def test_card_mode_card_types(col: Collection, column_values: ColumnValues):
    note: Note = create_note(col, "card types")
    new_card, learning_card = note.card_ids()
    review_card, relearning_card = create_note(col, "card types 2").card_ids()
    set_card_state(col, learning_card, CARD_TYPE_LRN, QUEUE_TYPE_LRN)
    set_card_state(col, review_card, CARD_TYPE_REV, QUEUE_TYPE_REV)
    set_card_state(col, relearning_card, CARD_TYPE_RELEARNING, QUEUE_TYPE_DAY_LEARN_RELEARN)
    assert __flagged_types(column_values, new_card) == {ColumnType.NEW}
    assert __flagged_types(column_values, learning_card) == {ColumnType.LEARNING}
    assert __flagged_types(column_values, review_card) == {ColumnType.REVIEW}
    assert __flagged_types(column_values, relearning_card) == {ColumnType.LEARNING, ColumnType.REVIEW}


def test_card_mode_suspended_new(col: Collection, column_values: ColumnValues):
    card_id: CardId = create_note(col, "suspended new").card_ids()[0]
    set_card_state(col, card_id, CARD_TYPE_NEW, QUEUE_TYPE_SUSPENDED)
    assert __flagged_types(column_values, card_id) == {ColumnType.NEW, ColumnType.SUSPENDED}


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
    set_card_state(col, card_1, CARD_TYPE_RELEARNING, QUEUE_TYPE_SUSPENDED)
    col.sched.bury_cards([card_2])
    for column_type in ColumnType:
        assert column_values.is_flagged(column_type, plain_note.id, is_note=True) == (column_type == ColumnType.NEW)
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
    learning_card: CardId = marked_note.card_ids()[0]
    review_card: CardId = marked_note.card_ids()[1]
    set_card_state(col, learning_card, CARD_TYPE_LRN, QUEUE_TYPE_LRN)
    set_card_state(col, review_card, CARD_TYPE_REV, QUEUE_TYPE_REV)
    all_cards: set[CardId] = set(col.find_cards(""))
    assert column_values.flagged_ids(ColumnType.NEW, is_note=False) == all_cards - {learning_card, review_card}
    assert column_values.flagged_ids(ColumnType.LEARNING, is_note=False) == {learning_card}
    assert column_values.flagged_ids(ColumnType.REVIEW, is_note=False) == {review_card}
    assert column_values.flagged_ids(ColumnType.NEW, is_note=True) == set(col.find_notes("")) - {marked_note.id}
    assert column_values.flagged_ids(ColumnType.LEARNING, is_note=True) == {marked_note.id}
    assert column_values.flagged_ids(ColumnType.REVIEW, is_note=True) == {marked_note.id}
    assert column_values.flagged_ids(ColumnType.SUSPENDED, is_note=False) == {suspended_card}
    assert column_values.flagged_ids(ColumnType.BURIED, is_note=False) == {buried_card}
    assert column_values.flagged_ids(ColumnType.MARKED, is_note=False) == set(marked_note.card_ids())
    assert column_values.flagged_ids(ColumnType.SUSPENDED, is_note=True) == {suspended_note.id}
    assert column_values.flagged_ids(ColumnType.BURIED, is_note=True) == {buried_note.id}
    assert column_values.flagged_ids(ColumnType.MARKED, is_note=True) == {marked_note.id}
