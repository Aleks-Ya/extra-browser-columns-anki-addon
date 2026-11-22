import logging
from logging import Logger
from typing import Sequence, Optional, Callable, Any

from anki.collection import BrowserColumns, Collection
from aqt import gui_hooks
from aqt.browser import Browser, Column, SearchContext, ItemId, CellRow
from aqt.qt import QTableView, QHeaderView, Qt, qconnect

from .column_values import ColumnValues, ColumnType

log: Logger = logging.getLogger(__name__)


class ColumnHooks:
    __columns: dict[str, tuple[ColumnType, str, str]] = {
        "extra-browser-columns-new": (ColumnType.NEW, "New", "Card is new"),
        "extra-browser-columns-learning": (ColumnType.LEARNING, "Learning", "Card is in learning"),
        "extra-browser-columns-review": (ColumnType.REVIEW, "Review", "Card is in review"),
        "extra-browser-columns-suspended": (ColumnType.SUSPENDED, "Suspended", "Card is suspended"),
        "extra-browser-columns-buried": (ColumnType.BURIED, "Buried", "Card is buried"),
        "extra-browser-columns-marked": (ColumnType.MARKED, "Marked", "Note is marked"),
    }
    __notes_mode_tooltips: dict[ColumnType, str] = {
        ColumnType.NEW: "Note has new cards",
        ColumnType.LEARNING: "Note has learning cards",
        ColumnType.REVIEW: "Note has review cards",
        ColumnType.SUSPENDED: "Note has suspended cards",
        ColumnType.BURIED: "Note has buried cards",
        ColumnType.MARKED: "Note is marked",
    }
    __sort_key_metadata: str = "extra-browser-columns-sort-key"
    __flagged_text: str = "✓"
    __not_flagged_text: str = ""

    def __init__(self, col_provider: Callable[[], Collection], column_values: ColumnValues) -> None:
        self.__col_provider: Callable[[], Collection] = col_provider
        self.__column_values: ColumnValues = column_values
        self.__hook_browser_did_fetch_columns: Callable[[dict[str, Column]], None] = ColumnHooks.__add_columns
        self.__hook_browser_did_fetch_row: Callable[[ItemId, bool, CellRow, Sequence[str]], None] = \
            self.__modify_row
        self.__hook_browser_will_search: Callable[[SearchContext], None] = self.__on_browser_will_search
        self.__hook_browser_did_search: Callable[[SearchContext], None] = self.__on_browser_did_search
        self.__hook_browser_will_show: Callable[[Browser], None] = ColumnHooks.__on_browser_will_show
        log.debug(f"{self.__class__.__name__} was instantiated")

    def setup_hooks(self) -> None:
        gui_hooks.browser_did_fetch_columns.append(self.__hook_browser_did_fetch_columns)
        gui_hooks.browser_did_fetch_row.append(self.__hook_browser_did_fetch_row)
        gui_hooks.browser_will_search.append(self.__hook_browser_will_search)
        gui_hooks.browser_did_search.append(self.__hook_browser_did_search)
        gui_hooks.browser_will_show.append(self.__hook_browser_will_show)
        log.info(f"{self.__class__.__name__} are set")

    def remove_hooks(self) -> None:
        gui_hooks.browser_did_fetch_columns.remove(self.__hook_browser_did_fetch_columns)
        gui_hooks.browser_did_fetch_row.remove(self.__hook_browser_did_fetch_row)
        gui_hooks.browser_will_search.remove(self.__hook_browser_will_search)
        gui_hooks.browser_did_search.remove(self.__hook_browser_did_search)
        gui_hooks.browser_will_show.remove(self.__hook_browser_will_show)
        log.info(f"{self.__class__.__name__} are removed")

    @staticmethod
    def __add_columns(columns: dict[str, Column]) -> None:
        for column_key, (column_type, label, cards_mode_tooltip) in ColumnHooks.__columns.items():
            columns[column_key] = Column(
                key=column_key,
                cards_mode_label=label,
                notes_mode_label=label,
                sorting_cards=BrowserColumns.SORTING_DESCENDING,
                sorting_notes=BrowserColumns.SORTING_DESCENDING,
                uses_cell_font=False,
                alignment=BrowserColumns.ALIGNMENT_CENTER,
                cards_mode_tooltip=cards_mode_tooltip,
                notes_mode_tooltip=ColumnHooks.__notes_mode_tooltips[column_type]
            )
        log.info("Columns were added")

    def __modify_row(self, item_id: ItemId, is_note: bool, row: CellRow, columns: Sequence[str]) -> None:
        for column_index, column_key in enumerate(columns):
            if column_key in ColumnHooks.__columns:
                column_type: ColumnType = ColumnHooks.__columns[column_key][0]
                is_flagged: bool = self.__column_values.is_flagged(column_type, item_id, is_note)
                row.cells[column_index].text = \
                    ColumnHooks.__flagged_text if is_flagged else ColumnHooks.__not_flagged_text

    def __on_browser_will_search(self, context: SearchContext) -> None:
        if isinstance(context.order, Column) and context.order.key in ColumnHooks.__columns:
            log.debug(f"Browser will search sorted by column: {context.order.key}")
            if context.addon_metadata is None:
                context.addon_metadata = {}
            context.addon_metadata[ColumnHooks.__sort_key_metadata] = context.order.key
            context.order = self.__col_provider().get_browser_column("noteFld")

    def __on_browser_did_search(self, context: SearchContext) -> None:
        column_key: Optional[str] = context.addon_metadata.get(ColumnHooks.__sort_key_metadata) \
            if context.addon_metadata else None
        if column_key and context.ids:
            log.debug(f"Browser did search sorted by column: {column_key}")
            column_type: ColumnType = ColumnHooks.__columns[column_key][0]
            is_note: bool = ColumnHooks.__is_notes_mode(context.browser)
            flagged_ids: set[ItemId] = self.__column_values.flagged_ids(column_type, is_note)
            context.ids = sorted(context.ids, key=lambda item_id: item_id in flagged_ids, reverse=context.reverse)

    @staticmethod
    def __on_browser_will_show(browser: Browser) -> None:
        # Qt fits a column to the wider of its cells and its label on a header border double-click:
        # fit our columns to their cells ("✓") instead (the label gets elided)
        # noinspection PyProtectedMember
        view: QTableView = browser.table._view
        header: QHeaderView = view.horizontalHeader()
        qconnect(header.sectionHandleDoubleClicked,
                 lambda section: ColumnHooks.__fit_column_to_cells(browser, view, header, section))
        ColumnHooks.__patch_header_data(browser, header)

    @staticmethod
    def __patch_header_data(browser: Browser, header: QHeaderView) -> None:
        # Anki's header stylesheet prevents eliding, so a clipped centered label shows its middle ("New" -> "e"):
        # left-align the labels of our columns that are narrower than their labels to show the beginning ("N").
        # Show the label and description of our columns as a header tooltip (Anki shows it only in the context menu).
        # noinspection PyProtectedMember
        model = browser.table._model
        original_header_data: Callable[..., Any] = model.headerData
        measuring: bool = False

        def is_clipped(section: int) -> bool:
            nonlocal measuring
            measuring = True  # "sectionSizeHint" may query the alignment
            try:
                return header.sectionSize(section) < header.sectionSizeHint(section)
            finally:
                measuring = False

        def header_data(section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
            if orientation == Qt.Orientation.Horizontal and role in (Qt.ItemDataRole.TextAlignmentRole,
                                                                     Qt.ItemDataRole.ToolTipRole) and not measuring:
                column_key: str = model.column_at_section(section).key
                if column_key in ColumnHooks.__columns:
                    if role == Qt.ItemDataRole.ToolTipRole:
                        return ColumnHooks.__header_tooltip(browser, column_key)
                    if is_clipped(section):
                        return (Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter).value
            return original_header_data(section, orientation, role)

        model.headerData = header_data

    @staticmethod
    def __header_tooltip(browser: Browser, column_key: str) -> str:
        column_type, label, cards_mode_tooltip = ColumnHooks.__columns[column_key]
        description: str = ColumnHooks.__notes_mode_tooltips[column_type] \
            if ColumnHooks.__is_notes_mode(browser) else cards_mode_tooltip
        return f"{label}\n{description}"

    @staticmethod
    def __fit_column_to_cells(browser: Browser, view: QTableView, header: QHeaderView, section: int) -> None:
        # noinspection PyProtectedMember
        column_key: str = browser.table._model.column_at_section(section).key
        if column_key in ColumnHooks.__columns:
            width: int = max(view.sizeHintForColumn(section), header.minimumSectionSize())
            log.debug(f"Fit column {column_key} to cells: {width}")
            header.resizeSection(section, width)

    @staticmethod
    def __is_notes_mode(browser: Browser) -> bool:
        # "Table.is_notes_mode" returns the previous state while searching after toggling the switch
        # noinspection PyProtectedMember
        return browser._switch.isChecked()

    def __del__(self):
        log.debug(f"{self.__class__.__name__} was deleted")
