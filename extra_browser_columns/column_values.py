import logging
from enum import Enum
from logging import Logger
from typing import Callable, Optional

from anki.collection import Collection
from anki.consts import QUEUE_TYPE_SUSPENDED, QUEUE_TYPE_SIBLING_BURIED, QUEUE_TYPE_MANUALLY_BURIED
from anki.notes import NoteId
from aqt.browser import ItemId

log: Logger = logging.getLogger(__name__)


class ColumnType(Enum):
    SUSPENDED = "is:suspended"
    BURIED = "is:buried"
    MARKED = "tag:marked"


class ColumnValues:
    __marked_tag: str = "marked"
    __buried_queues: tuple[int, ...] = (QUEUE_TYPE_SIBLING_BURIED, QUEUE_TYPE_MANUALLY_BURIED)

    def __init__(self, col_provider: Callable[[], Collection]) -> None:
        self.__col_provider: Callable[[], Collection] = col_provider
        log.debug(f"{self.__class__.__name__} was instantiated")

    def is_flagged(self, column_type: ColumnType, item_id: ItemId, is_note: bool) -> bool:
        col: Collection = self.__col_provider()
        note_id: NoteId
        queues: list[int]
        if is_note:
            note_id = NoteId(item_id)
            queues = col.db.list("select queue from cards where nid = ?", item_id)
        else:
            row: Optional[list] = col.db.first("select nid, queue from cards where id = ?", item_id)
            if row is None:
                return False
            note_id = NoteId(row[0])
            queues = [row[1]]
        if column_type == ColumnType.SUSPENDED:
            return QUEUE_TYPE_SUSPENDED in queues
        if column_type == ColumnType.BURIED:
            return any(queue in ColumnValues.__buried_queues for queue in queues)
        return col.get_note(note_id).has_tag(ColumnValues.__marked_tag)

    def flagged_ids(self, column_type: ColumnType, is_note: bool) -> set[ItemId]:
        col: Collection = self.__col_provider()
        search: str = column_type.value
        return set(col.find_notes(search) if is_note else col.find_cards(search))

    def __del__(self):
        log.debug(f"{self.__class__.__name__} was deleted")
