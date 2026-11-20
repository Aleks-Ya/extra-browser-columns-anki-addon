from aqt import gui_hooks, mw

from .column_hooks import ColumnHooks
from .column_values import ColumnValues

column_values: ColumnValues = ColumnValues(lambda: mw.col)
column_hooks: ColumnHooks = ColumnHooks(lambda: mw.col, column_values)

gui_hooks.profile_did_open.append(column_hooks.setup_hooks)
gui_hooks.profile_will_close.append(column_hooks.remove_hooks)
