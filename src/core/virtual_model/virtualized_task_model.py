# virtualized_task_model.py - True UI virtualization for TaskGrid
from PySide6 import QtCore, QtGui
import sqlite3
from collections import OrderedDict
from ..db.db_connection_pool import get_db_connection

DB_FILE = "tasks.db"

class LRUCache:
    """Simple LRU cache for row data with memory optimization"""
    def __init__(self, max_size=500):
        self.max_size = max_size
        self.cache = OrderedDict()
        self._original_max_size = max_size

    def get(self, key):
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                # Remove least recently used item
                self.cache.popitem(last=False)
        self.cache[key] = value

    def clear(self):
        self.cache.clear()
    
    def optimize_for_resize(self, enabled=True):
        """Optimize cache for resize operations by reducing size"""
        if enabled:
            # Reduce cache size during resize for better memory performance
            self.max_size = min(100, self._original_max_size)
            # Clear excess items if current cache is larger
            while len(self.cache) > self.max_size:
                self.cache.popitem(last=False)
        else:
            # Restore original cache size
            self.max_size = self._original_max_size

class VirtualizedTaskTableModel(QtCore.QAbstractTableModel):
    """Virtualized task model with lazy DB paging"""

    timeLimitChanged = QtCore.Signal(int, str)  # task_id, new_time_limit_string

    def __init__(self, parent=None, chunk_size=100):
        super().__init__(parent)
        self.parent_widget = parent  # This should be the TaskGrid
        self.chunk_size = chunk_size
        self.row_cache = LRUCache(max_size=chunk_size * 4)
        self.total_row_count = 0
        self.current_week_id = None
        self.selected_tasks = set()
        
        # Performance optimization flags
        self._is_resizing = False
        self._minimal_mode = False

        # Column definitions (same as original TaskTableModel)
        self.columns = [
            "", "Attempt ID", "Duration", "Project ID", "Project Name", 
            "Operation ID", "Time Limit", "Date Audited", "Score", 
            "Feedback", "Locale", "Time Begin", "Time End"
        ]
        self.field_names = [
            None,
            "attempt_id", "duration", "project_id", "project_name",
            "operation_id", "time_limit", "date_audited", "score",
            "feedback", "locale", "time_begin", "time_end"
        ]

    # ---------- Performance optimization methods ---------- #
    
    def set_resize_mode(self, is_resizing):
        """Enable/disable resize optimization mode"""
        self._is_resizing = is_resizing
        if is_resizing:
            self._minimal_mode = True
            # Optimize cache for memory efficiency during resize
            self.row_cache.optimize_for_resize(True)
        else:
            self._minimal_mode = False
            # Restore full cache size after resize
            self.row_cache.optimize_for_resize(False)

    def set_minimal_mode(self, enabled):
        """Enable/disable minimal data mode for better performance"""
        self._minimal_mode = enabled

    # ---------- Required Qt model methods ---------- #

    def rowCount(self, parent=QtCore.QModelIndex()):
        return self.total_row_count

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.columns)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            if 0 <= section < len(self.columns):
                return self.columns[section]
        return None

    # ---------- Data retrieval ---------- #

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid() or index.row() >= self.total_row_count:
            return None

        # Performance optimization: return minimal data during resize operations
        if self._is_resizing or self._minimal_mode:
            if role == QtCore.Qt.DisplayRole:
                col = index.column()
                if col == 0:
                    return ""
                elif col == 1:  # Attempt ID - show something to indicate data exists
                    return "..."
                else:
                    return ""
            elif role == QtCore.Qt.CheckStateRole and index.column() == 0:
                return QtCore.Qt.Unchecked
            return None

        row = index.row()
        col = index.column()

        # Checkbox column
        if col == 0:
            if role == QtCore.Qt.CheckStateRole:
                task_id = self._get_task_id_cached(row)
                return QtCore.Qt.Checked if task_id in self.selected_tasks else QtCore.Qt.Unchecked
            elif role == QtCore.Qt.DisplayRole:
                return ""
            return None

        # Load row data (lazy fetch)
        row_data = self._get_row_cached(row)
        if row_data is None:
            return None

        data_col_idx = col - 1  # adjust for ID column offset
        if data_col_idx >= len(row_data) - 1:
            return None

        value = row_data[data_col_idx + 1]  # +1 skip ID

        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return str(value) if value is not None else ""

        # Provide highlighting info to delegate
        if role == QtCore.Qt.UserRole:
            display_value = str(value) if value is not None else ""
            is_empty = self._is_empty_value(display_value)
            is_init = self._is_init_value(col, display_value)
            return {"is_empty": is_empty, "is_init": is_init, "needs_highlight": is_empty or is_init}
        return None

    # ---------- Editing ---------- #

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags

        col = index.column()
        if col == 0:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable
        if col == 2:  # Duration (open timer)
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        if col == 9:  # Feedback
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        if col == 12:  # Time End
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid() or index.row() >= self.total_row_count:
            return False
        row = index.row()
        col = index.column()

        # Checkbox selection
        if col == 0 and role == QtCore.Qt.CheckStateRole:
            task_id = self._get_task_id_cached(row)
            if task_id is None:
                return False
                
            if value == QtCore.Qt.Checked:
                self.selected_tasks.add(task_id)
            else:
                self.selected_tasks.discard(task_id)
            
            self.dataChanged.emit(index, index, [QtCore.Qt.CheckStateRole])
            
            # Update delete button - fixed parent reference chain
            if self.parent_widget and hasattr(self.parent_widget, 'main_window'):
                main_window = self.parent_widget.main_window
                if main_window and hasattr(main_window, 'update_delete_button'):
                    main_window.update_delete_button()
            return True

        if role == QtCore.Qt.EditRole and col > 0:
            field_name = self.field_names[col] if col < len(self.field_names) else None
            if field_name:
                task_id = self._get_task_id_cached(row)
                if task_id is None:
                    return False
                    
                str_val = str(value)
                self._update_task_field(task_id, field_name, str_val)

                # update cache row if present
                cached_row = list(self.row_cache.get(row)) if self.row_cache.get(row) else None
                if cached_row:
                    data_col_idx = col
                    if data_col_idx < len(cached_row):
                        cached_row[data_col_idx] = str_val
                        self.row_cache.put(row, tuple(cached_row))
                else:
                    # If row not cached yet, store placeholder to avoid DB hit next paint
                    self.row_cache.put(row, None)

                # Emit targeted update
                self.dataChanged.emit(index, index, [QtCore.Qt.DisplayRole])

                if field_name == "time_limit":
                    if self._is_valid_time_format(str_val):
                        self.timeLimitChanged.emit(task_id, str_val)
                    else:
                        self.timeLimitChanged.emit(task_id, "00:00:00")
                return True
        return False

    # ---------- Public helpers ---------- #

    def refresh_week(self, week_id):
        """Switch to a new week and clear caches"""
        self.beginResetModel()
        self.current_week_id = week_id
        self.row_cache.clear()
        self.total_row_count = self._get_total_count(week_id) if week_id else 0
        self.selected_tasks.clear()
        self.endResetModel()

    def get_task_id(self, row):
        return self._get_task_id_cached(row)

    def get_task_data_by_id(self, task_id):
        """Get complete task data for a specific task ID"""
        if self.current_week_id is None:
            return None
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                """SELECT id, attempt_id, duration, project_id, project_name,
                       operation_id, time_limit, date_audited, score, feedback, locale,
                       time_begin, time_end
                       FROM tasks WHERE id=? AND week_id=?""",
                (task_id, self.current_week_id)
            )
            return c.fetchone()
    
    def get_task_row_number(self, task_id):
        """Get the row number (1-based) for a specific task ID within the current week"""
        if self.current_week_id is None:
            return None
        
        # For small datasets, we can afford to scan
        for row in range(self.total_row_count):
            if self._get_task_id_cached(row) == task_id:
                return row + 1  # 1-based indexing
        
        # If not found in cache, query database
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                """SELECT ROW_NUMBER() OVER (ORDER BY id) as row_num
                   FROM tasks WHERE week_id=? AND id=?""",
                (self.current_week_id, task_id)
            )
            result = c.fetchone()
            return result[0] if result else None

    # Compatibility wrappers for TaskGrid legacy calls
    def refresh_tasks(self, week_id):
        self.refresh_week(week_id)

    def get_selected_tasks(self):
        return self.selected_tasks.copy()

    # ---------- Internal helpers ---------- #

    def _get_task_id_cached(self, row):
        row_data = self._get_row_cached(row)
        return row_data[0] if row_data else None

    def _get_row_cached(self, row):
        data = self.row_cache.get(row)
        if data is not None:
            return data
        # Need to load chunk
        chunk_start = (row // self.chunk_size) * self.chunk_size
        self._load_chunk(chunk_start, self.chunk_size)
        return self.row_cache.get(row)

    def _load_chunk(self, start_row, count):
        if self.current_week_id is None:
            return
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                """SELECT id, attempt_id, duration, project_id, project_name,
                       operation_id, time_limit, date_audited, score, feedback, locale,
                       time_begin, time_end
                       FROM tasks WHERE week_id=? ORDER BY id LIMIT ? OFFSET ?""",
                (self.current_week_id, count, start_row)
            )
            rows = c.fetchall()
            for i, row_data in enumerate(rows):
                self.row_cache.put(start_row + i, row_data)

    def _get_total_count(self, week_id):
        if week_id is None:
            return 0
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM tasks WHERE week_id=?", (week_id,))
            return c.fetchone()[0]

    def _update_task_field(self, task_id, field_name, value):
        # Similar validation to original model
        if field_name == "score":
            try:
                ivalue = int(value)
                if ivalue < 1:
                    value = 1
                elif ivalue > 5:
                    value = 5
                value = str(value)
            except ValueError:
                value = "0"
        if field_name in ["duration", "time_limit"]:
            if not self._is_valid_time_format(value):
                value = "00:00:00"
        with get_db_connection() as conn:
            c = conn.cursor()
            query = f"UPDATE tasks SET {field_name}=? WHERE id=?"
            c.execute(query, (value, task_id))
            conn.commit()

    def _is_valid_time_format(self, time_str):
        parts = time_str.split(":" )
        if len(parts) != 3:
            return False
        try:
            h, m, s = map(int, parts)
            return 0 <= h < 100 and 0 <= m < 60 and 0 <= s < 60
        except ValueError:
            return False

    # ---------- Highlight helpers (same logic as legacy model) ---------- #

    def _is_init_value(self, col_idx, value):
        """Check if a value is an initialization default that should be highlighted"""
        if col_idx == 2 or col_idx == 6:  # Duration or Time Limit columns
            return value == "00:00:00"
        if col_idx == 8:  # Score column
            return value == "0"
        return False

    def _is_empty_value(self, value):
        """Check if a cell is visually empty"""
        return not value or not str(value).strip() 