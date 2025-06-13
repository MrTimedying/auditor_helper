import sqlite3
from PySide6 import QtCore, QtWidgets, QtGui
from datetime import datetime, timedelta
from .timer_dialog import TimerDialog

DB_FILE = "tasks.db"

class TaskTableModel(QtCore.QAbstractTableModel):
    """Custom table model that supports UI virtualization"""
    
    # Custom signals
    timeLimitChanged = QtCore.Signal(int, str)  # task_id, new_time_limit_string
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks = []
        self.selected_tasks = set()
        self.main_window = parent
        self.current_week_id = None
        
        # Column definitions
        self.columns = [
            "", "Attempt ID", "Duration", "Project ID", "Project Name", 
            "Operation ID", "Time Limit", "Date Audited", "Score", 
            "Feedback", "Locale", "Time Begin", "Time End"
        ]
        
        # Field names mapping (excluding checkbox column)
        self.field_names = [
            None,  # Skip selection checkbox column
            "attempt_id", "duration", "project_id", "project_name",
            "operation_id", "time_limit", "date_audited", "score",
            "feedback", "locale", "time_begin", "time_end"
        ]
    
    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.tasks)
    
    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.columns)
    
    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            if 0 <= section < len(self.columns):
                return self.columns[section]
        return None
    
    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self.tasks):
            return None
        
        row = index.row()
        col = index.column()
        task = self.tasks[row]
        task_id = task[0]
        
        # Handle checkbox column (column 0)
        if col == 0:
            if role == QtCore.Qt.CheckStateRole:
                return QtCore.Qt.Checked if task_id in self.selected_tasks else QtCore.Qt.Unchecked
            elif role == QtCore.Qt.DisplayRole:
                return ""
            return None
        
        # Handle data columns (adjust index for task tuple)
        data_col_idx = col - 1  # Adjust for checkbox column
        if data_col_idx >= len(task) - 1:  # -1 because task[0] is ID
            return None
        
        # Get the actual value from task tuple
        if data_col_idx < len(task) - 3:  # Regular columns (excluding time_begin, time_end)
            value = task[data_col_idx + 1]  # +1 to skip ID
        elif data_col_idx == len(task) - 3:  # time_begin
            value = task[-2]
        elif data_col_idx == len(task) - 2:  # time_end
            value = task[-1]
        else:
            value = None
        
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return str(value) if value is not None else ""
        
        elif role == QtCore.Qt.ToolTipRole:
            # Special tooltip for feedback column
            if col == 9:  # Feedback column
                return str(value) if value is not None else ""
            return None
        
        elif role == QtCore.Qt.UserRole:
            # Custom role for highlighting state
            display_value = str(value) if value is not None else ""
            is_empty = self.is_empty_value(display_value)
            is_init = self.is_init_value(col, display_value)
            return {"is_empty": is_empty, "is_init": is_init, "needs_highlight": is_empty or is_init}
        
        return None
    
    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid() or index.row() >= len(self.tasks):
            return False
        
        row = index.row()
        col = index.column()
        task_id = self.tasks[row][0]
        
        # Handle checkbox column
        if col == 0 and role == QtCore.Qt.CheckStateRole:
            if value == QtCore.Qt.Checked:
                self.selected_tasks.add(task_id)
            else:
                self.selected_tasks.discard(task_id)
            
            self.dataChanged.emit(index, index, [QtCore.Qt.CheckStateRole])
            
            # Update delete button text
            if hasattr(self.main_window, 'update_delete_button'):
                self.main_window.update_delete_button()
            return True
        
        # Handle data columns
        if role == QtCore.Qt.EditRole and col > 0:
            field_name = self.field_names[col] if col < len(self.field_names) else None
            
            if field_name:
                # Update the database
                self.update_task_field(task_id, field_name, str(value))
                
                # Emit signal if time_limit column was changed
                if field_name == "time_limit":
                    if self.is_valid_time_format(str(value)):
                        self.timeLimitChanged.emit(task_id, str(value))
                    else:
                        self.timeLimitChanged.emit(task_id, "00:00:00")
                
                # Refresh data to get updated values
                self.refresh_tasks(self.current_week_id)
                return True
        
        return False
    
    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        
        col = index.column()
        
        # Checkbox column
        if col == 0:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable
        
        # Duration column (2) - not editable, only openable via timer dialog
        if col == 2:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        
        # Feedback column (9) - not editable directly, only via dialog
        if col == 9:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        
        # Time End column (12) - read-only
        if col == 12:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        
        # All other columns are editable
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable
    
    def update_task_field(self, task_id, field_name, value):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # Special handling for some fields
        if field_name == "score":
            try:
                value = int(value)
                if value < 1:
                    value = 1
                elif value > 5:
                    value = 5
            except ValueError:
                value = 0
        
        # Validate time format for duration and time_limit
        if field_name in ["duration", "time_limit"]:
            if not self.is_valid_time_format(value):
                value = "00:00:00"
        
        query = f"UPDATE tasks SET {field_name}=? WHERE id=?"
        c.execute(query, (value, task_id))
        conn.commit()
        conn.close()
        
        # Update analysis
        try:
            if hasattr(self.main_window, 'refresh_analysis'):
                self.main_window.refresh_analysis()
        except Exception as e:
            print(f"Error updating analysis: {e}")
    
    def is_valid_time_format(self, time_str):
        try:
            parts = time_str.split(":")
            if len(parts) != 3:
                return False
            hours, minutes, seconds = map(int, parts)
            if not (0 <= hours < 100 and 0 <= minutes < 60 and 0 <= seconds < 60):
                return False
            return True
        except ValueError:
            return False
    
    def is_init_value(self, col_idx, value):
        """Check if a value is an initialization value that should be highlighted"""
        if col_idx == 2 or col_idx == 6:  # Duration or Time Limit
            return value == "00:00:00"
        elif col_idx == 8:  # Score
            return value == "0"
        return False
    
    def is_empty_value(self, value):
        """Check if a value is empty"""
        return not value or not str(value).strip()
    
    def refresh_tasks(self, week_id):
        self.beginResetModel()
        
        self.current_week_id = week_id
        self.selected_tasks.clear()
        
        if week_id is None:
            self.tasks = []
            self.endResetModel()
            return
            
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(
            """SELECT id, attempt_id, duration, project_id, project_name,
               operation_id, time_limit, date_audited, score, feedback, locale,
               time_begin, time_end
               FROM tasks WHERE week_id=? ORDER BY id""", 
            (week_id,)
        )
        self.tasks = c.fetchall()
        conn.close()
        
        self.endResetModel()
    
    def get_task_id(self, row):
        """Get task ID for a given row"""
        if 0 <= row < len(self.tasks):
            return self.tasks[row][0]
        return None
    
    def get_selected_tasks(self):
        """Get set of selected task IDs"""
        return self.selected_tasks.copy()


class TaskGrid(QtWidgets.QTableView):
    # Define custom signal for time limit changes
    timeLimitChanged = QtCore.Signal(int, str)  # task_id, new_time_limit_string
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TaskTable")
        self.main_window = parent
        
        # Create and set the model
        self.task_model = TaskTableModel(parent)
        self.setModel(self.task_model)
        
        # Forward model signals
        self.task_model.timeLimitChanged.connect(self.timeLimitChanged.emit)
        
        # Setup table structure
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        
        # Allow editing by double click
        self.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked | 
                             QtWidgets.QAbstractItemView.EditKeyPressed)
        self.doubleClicked.connect(self.handle_cell_double_clicked)
        
        # Set column widths
        self.setColumnWidth(0, 30)   # Selection checkbox column
        self.setColumnWidth(1, 100)  # Attempt ID
        self.setColumnWidth(2, 80)   # Duration
        self.setColumnWidth(3, 80)   # Project ID
        self.setColumnWidth(4, 120)  # Project Name
        self.setColumnWidth(5, 100)  # Operation ID
        self.setColumnWidth(6, 80)   # Time Limit
        self.setColumnWidth(7, 100)  # Date Audited
        self.setColumnWidth(8, 60)   # Score
        self.setColumnWidth(9, 200)  # Feedback
        self.setColumnWidth(10, 80)  # Locale
        self.setColumnWidth(11, 80)  # Time Begin
        self.setColumnWidth(12, 80)  # Time End
        
        # Connect signals
        self.clicked.connect(self.handle_cell_clicked)
        
        # Custom item delegate for cell highlighting
        self.setItemDelegate(TaskGridItemDelegate(self))
    
    @property
    def current_week_id(self):
        return self.task_model.current_week_id
    
    @property
    def selected_tasks(self):
        return self.task_model.selected_tasks
    
    def handle_cell_double_clicked(self, index):
        if not index.isValid():
            return
            
        row = index.row()
        col = index.column()
        task_id = self.task_model.get_task_id(row)
        
        if not task_id:
            return
        
        # Skip checkbox column
        if col == 0:
            return
        
        # Handle Duration cell (col 2) - open timer dialog instead of inline edit
        if col == 2:
            self.open_timer_dialog(task_id)
            return
            
        # Handle feedback cell (col 9) - open dialog instead of inline edit
        if col == 9:
            self.edit_feedback(task_id)
            return
    
    def handle_cell_clicked(self, index):
        if not index.isValid():
            return
            
        row = index.row()
        col = index.column()
        task_id = self.task_model.get_task_id(row)
        
        if not task_id:
            return
        
        # Handle selection checkbox column clicks
        if col == 0:
            current_state = self.task_model.data(index, QtCore.Qt.CheckStateRole)
            new_state = QtCore.Qt.Unchecked if current_state == QtCore.Qt.Checked else QtCore.Qt.Checked
            self.task_model.setData(index, new_state, QtCore.Qt.CheckStateRole)
    
    def refresh_tasks(self, week_id):
        self.task_model.refresh_tasks(week_id)
        
        # Update office hour count display when tasks are refreshed
        self.update_office_hour_count_display()
        
        # Update delete button text
        if hasattr(self.main_window, 'update_delete_button'):
            self.main_window.update_delete_button()
    
    def edit_feedback(self, task_id):
        # Get current feedback text
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT feedback FROM tasks WHERE id=?", (task_id,))
        feedback = c.fetchone()[0] or ""
        conn.close()
        
        # Show dialog with markdown editor
        dialog = FeedbackDialog(self, feedback, task_id)
        if dialog.exec():
            # Refresh the model to show updated feedback
            self.task_model.refresh_tasks(self.current_week_id)
    
    def delete_selected_tasks(self):
        selected_tasks = self.task_model.get_selected_tasks()
        if not selected_tasks:
            return
            
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        for task_id in selected_tasks:
            c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            
        conn.commit()
        conn.close()
        
        # Refresh the grid and analysis
        self.refresh_tasks(self.current_week_id)
        
        # Update analysis
        try:
            if hasattr(self.main_window, 'refresh_analysis'):
                self.main_window.refresh_analysis()
        except Exception as e:
            print(f"Error updating analysis after deletion: {e}")
    
    def delete_task(self, task_id):
        # Legacy method kept for compatibility
        self.task_model.selected_tasks = {task_id}
        self.delete_selected_tasks()
    
    def add_task(self, week_id):
        """Add a new task to the specified week"""
        if not week_id:
            return
        
        # Check if we should validate task boundaries  
        from global_settings import global_settings
        if global_settings.should_show_boundary_warnings():
            # For new task creation, we can only check against current time
            # More precise validation will happen when time_begin is set
            current_time = datetime.now()
            if self.is_task_outside_week_boundaries(week_id, current_time):
                if global_settings.should_auto_suggest_new_week():
                    # Show suggestion to create new week
                    self.suggest_new_week_for_task(week_id, current_time)
                    return
        
        self.create_task_in_week(week_id)
    
    def create_task_in_week(self, week_id):
        """Create a new task in the specified week"""
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # Default values for a new task
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute(
            """INSERT INTO tasks (
                week_id, attempt_id, duration, project_id, project_name,
                operation_id, time_limit, date_audited, score, feedback, locale,
                time_begin, time_end
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (week_id, "", "00:00:00", "", "", "", "00:00:00", today, 0, "", "", "", "")
        )
        conn.commit()
        conn.close()
        
        # Refresh the grid
        self.refresh_tasks(week_id)
    
    def is_task_outside_week_boundaries(self, week_id, task_time):
        """Check if a task time falls outside the week's boundaries"""
        try:
            from global_settings import global_settings
            
            # Get week boundaries
            week_start, week_end = self.get_week_boundaries(week_id)
            
            if week_start and week_end:
                return task_time < week_start or task_time > week_end
            
            return False
        except Exception as e:
            print(f"Error checking week boundaries: {e}")
            return False
    
    def get_week_boundaries(self, week_id):
        """Get the start and end boundaries for a week"""
        try:
            from global_settings import global_settings
            
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            
            # Get week settings (both custom and global defaults)
            c.execute("""
                SELECT week_label, week_start_day, week_start_hour, week_end_day, week_end_hour, is_custom_duration
                FROM weeks WHERE id=?
            """, (week_id,))
            
            week_data = c.fetchone()
            conn.close()
            
            if not week_data:
                return None, None
            
            week_label, custom_start_day, custom_start_hour, custom_end_day, custom_end_hour, is_custom = week_data
            
            # Parse week start date from label (format: "dd/MM/yyyy - dd/MM/yyyy")
            try:
                week_start_date_str = week_label.split(" - ")[0]
                week_start_date = datetime.strptime(week_start_date_str, "%d/%m/%Y").date()
            except ValueError:
                # Try alternative format
                week_start_date = datetime.strptime(week_start_date_str, "%m/%d/%Y").date()
            
            # Determine which settings to use
            if is_custom and custom_start_day is not None:
                # Use custom week settings
                start_day = custom_start_day
                start_hour = custom_start_hour or 0
                end_day = custom_end_day
                end_hour = custom_end_hour or 23
            else:
                # Use global defaults
                default_settings = global_settings.get_default_week_settings()
                start_day = default_settings['week_start_day']
                start_hour = default_settings['week_start_hour']
                end_day = default_settings['week_end_day'] 
                end_hour = default_settings['week_end_hour']
            
            # Calculate actual start and end datetimes
            # Find the correct start day of the week
            days_since_monday = week_start_date.weekday()  # Monday is 0
            target_start_day_offset = (start_day - 1) % 7  # Convert to 0-based, Monday=0
            
            if target_start_day_offset <= days_since_monday:
                # Target day is in the same week
                days_to_start = target_start_day_offset - days_since_monday
            else:
                # Target day is in the previous week
                days_to_start = target_start_day_offset - days_since_monday - 7
            
            actual_start_date = week_start_date + timedelta(days=days_to_start)
            week_start_datetime = datetime.combine(actual_start_date, datetime.min.time().replace(hour=start_hour))
            
            # Calculate end datetime (might be in next week)
            target_end_day_offset = (end_day - 1) % 7
            if target_end_day_offset >= target_start_day_offset:
                days_to_end = target_end_day_offset - target_start_day_offset
            else:
                days_to_end = target_end_day_offset - target_start_day_offset + 7
                
            actual_end_date = actual_start_date + timedelta(days=days_to_end)
            week_end_datetime = datetime.combine(actual_end_date, datetime.min.time().replace(hour=end_hour, minute=59, second=59))
            
            return week_start_datetime, week_end_datetime
            
        except Exception as e:
            print(f"Error calculating week boundaries: {e}")
            return None, None
    
    def suggest_new_week_for_task(self, current_week_id, task_time):
        """Suggest creating a new week for the task"""
        if not hasattr(self.main_window, 'toaster_manager'):
            return
        
        # Calculate suggested week dates
        week_start_date = task_time.date()
        # Adjust to proper week start based on global settings
        from global_settings import global_settings
        default_settings = global_settings.get_default_week_settings()
        start_day_of_week = default_settings['week_start_day']  # 1=Monday, 7=Sunday
        
        # Calculate days to subtract to get to the correct start day
        current_day_of_week = week_start_date.weekday() + 1  # Convert to 1=Monday, 7=Sunday
        days_to_subtract = (current_day_of_week - start_day_of_week) % 7
        suggested_start_date = week_start_date - timedelta(days=days_to_subtract)
        suggested_end_date = suggested_start_date + timedelta(days=6)
        
        message = (
            f"This task would fall outside the current week's boundaries.\n\n"
            f"Would you like to create a new week ({suggested_start_date.strftime('%d/%m/%Y')} - {suggested_end_date.strftime('%d/%m/%Y')}) "
            f"and add the task there?"
        )
        
        self.main_window.toaster_manager.show_question(
            message,
            "Task Outside Week Boundaries",
            lambda result: self.handle_new_week_suggestion(result, suggested_start_date, suggested_end_date, current_week_id)
        )
    
    def handle_new_week_suggestion(self, user_accepted, suggested_start_date, suggested_end_date, original_week_id):
        """Handle the user's response to the new week suggestion"""
        if user_accepted:
            # Create new week
            start_date_str = suggested_start_date.strftime("%d/%m/%Y")
            end_date_str = suggested_end_date.strftime("%d/%m/%Y")
            week_label = f"{start_date_str} - {end_date_str}"
            
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            
            try:
                # Insert new week with global default settings
                from global_settings import global_settings
                default_settings = global_settings.get_default_week_settings()
                
                c.execute("""
                    INSERT INTO weeks (
                        week_label, week_start_day, week_start_hour, week_end_day, week_end_hour, 
                        is_custom_duration, is_bonus_week
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    week_label,
                    default_settings['week_start_day'],
                    default_settings['week_start_hour'], 
                    default_settings['week_end_day'],
                    default_settings['week_end_hour'],
                    0,  # Use global defaults
                    0   # Not a bonus week by default
                ))
                
                new_week_id = c.lastrowid
                conn.commit()
                
                # Create task in new week
                self.create_task_in_week(new_week_id)
                
                # Update week widget and switch to new week
                if hasattr(self.main_window, 'week_widget'):
                    self.main_window.week_widget.refresh_weeks()
                    self.main_window.week_widget.select_week_by_id(new_week_id)
                
                # Show success message
                self.main_window.toaster_manager.show_info(
                    f"New week created and task added successfully!",
                    "Week Created",
                    3000
                )
                
            except sqlite3.IntegrityError:
                # Week already exists
                self.main_window.toaster_manager.show_warning(
                    f"A week with these dates already exists.",
                    "Duplicate Week",
                    5000
                )
            except Exception as e:
                self.main_window.toaster_manager.show_error(
                    f"Failed to create new week: {str(e)}",
                    "Creation Failed",
                    5000
                )
            finally:
                conn.close()
        else:
            # User declined, add to current week anyway
            self.create_task_in_week(original_week_id)
    
    def update_task_time_and_duration_from_timer(self, task_id, new_duration_seconds, 
                                                  is_first_start_for_task, has_duration_changed, 
                                                  start_timestamp_for_new_task=None):
        """
        Update task duration and time columns based on timer dialog activity.
        Called by TimerDialog when it closes.
        """
        from datetime import datetime
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # Convert duration seconds to HH:MM:SS format
        hours = int(new_duration_seconds // 3600)
        minutes = int((new_duration_seconds % 3600) // 60)
        seconds = int(new_duration_seconds % 60)
        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # Update duration
        c.execute("UPDATE tasks SET duration=? WHERE id=?", (duration_str, task_id))
        
        # Handle time_begin logic
        if is_first_start_for_task and start_timestamp_for_new_task:
            # Check if time_begin is currently empty
            c.execute("SELECT time_begin FROM tasks WHERE id=?", (task_id,))
            current_time_begin = c.fetchone()[0]
            
            if not current_time_begin or current_time_begin.strip() == "":
                # Record the start timestamp
                time_begin_str = start_timestamp_for_new_task.strftime('%Y-%m-%d %H:%M:%S')
                c.execute("UPDATE tasks SET time_begin=? WHERE id=?", (time_begin_str, task_id))
        
        # Handle time_end logic
        if has_duration_changed:
            # Record current time as end time
            time_end_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            c.execute("UPDATE tasks SET time_end=? WHERE id=?", (time_end_str, task_id))
        
        conn.commit()
        conn.close()
        
        # Validate task boundaries after timestamps are updated
        self.validate_task_against_boundaries(task_id, self.current_week_id)
        
        # Refresh the grid to show updated values
        self.refresh_tasks(self.current_week_id)
        
        # Update analysis
        if hasattr(self.main_window, 'refresh_analysis'):
            self.main_window.refresh_analysis()

    def open_timer_dialog(self, task_id):
        """Open the timer dialog for the specified task"""
        week_task_number = None
        time_limit_str = "00:00:00"  # Default value
        
        for row_idx, task in enumerate(self.task_model.tasks):
            if task[0] == task_id:
                week_task_number = row_idx + 1 # 1-based indexing
                # Get the time_limit string from the task data
                # task[6] corresponds to 'time_limit' in the fetched tuple
                time_limit_str = task[6] if len(task) > 6 and task[6] else "00:00:00"
                break
        
        dialog = TimerDialog(self, task_id, week_task_number=week_task_number, time_limit_str=time_limit_str)
        dialog.show()  # Use show() instead of exec() to make it non-modal

    def set_office_hour_count_label(self, label):
        """Sets the QLabel widget for displaying office hour count."""
        self.office_hour_count_label = label
        self.update_office_hour_count_display()

    def add_office_hour_session(self):
        """Increments the office_hour_count for the current week."""
        if self.current_week_id is None:
            if hasattr(self.main_window, 'toaster_manager'):
                self.main_window.toaster_manager.show_warning(
                    "No Week Selected", "Please select a week to add office hours.", 3000
                )
            return

        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("UPDATE weeks SET office_hour_count = office_hour_count + 1 WHERE id=?", (self.current_week_id,))
            conn.commit()
            conn.close()
            self.update_office_hour_count_display()
            if hasattr(self.main_window, 'refresh_analysis'):
                self.main_window.refresh_analysis()
        except Exception as e:
            print(f"Error adding office hour session: {e}")
            if hasattr(self.main_window, 'toaster_manager'):
                self.main_window.toaster_manager.show_error(
                    "Error", f"Failed to add office hour session: {str(e)}", 3000
                )

    def remove_office_hour_session(self):
        """Decrements the office_hour_count for the current week (min 0)."""
        if self.current_week_id is None:
            if hasattr(self.main_window, 'toaster_manager'):
                self.main_window.toaster_manager.show_warning(
                    "No Week Selected", "Please select a week to remove office hours.", 3000
                )
            return
        
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            # Ensure count does not go below zero
            c.execute("UPDATE weeks SET office_hour_count = MAX(0, office_hour_count - 1) WHERE id=?", (self.current_week_id,))
            conn.commit()
            conn.close()
            self.update_office_hour_count_display()
            if hasattr(self.main_window, 'refresh_analysis'):
                self.main_window.refresh_analysis()
        except Exception as e:
            print(f"Error removing office hour session: {e}")
            if hasattr(self.main_window, 'toaster_manager'):
                self.main_window.toaster_manager.show_error(
                    "Error", f"Failed to remove office hour session: {str(e)}", 3000
                )

    def update_office_hour_count_display(self):
        """Updates the office hour count label."""
        if not hasattr(self, 'office_hour_count_label') or self.current_week_id is None:
            if hasattr(self, 'office_hour_count_label'):
                self.office_hour_count_label.setText("Office Hours: N/A")
            return

        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT office_hour_count FROM weeks WHERE id=?", (self.current_week_id,))
            result = c.fetchone()
            conn.close()

            office_hour_count = result[0] if result and result[0] is not None else 0
            self.office_hour_count_label.setText(f"Office Hours: {office_hour_count}")
        except Exception as e:
            print(f"Error updating office hour count display: {e}")
            if hasattr(self, 'office_hour_count_label'):
                self.office_hour_count_label.setText("Office Hours: Error")

    def validate_task_against_boundaries(self, task_id, week_id):
        """
        Validate a task's actual timestamps against week boundaries.
        If both time_begin and time_end exist, both must be within boundaries.
        """
        try:
            from global_settings import global_settings
            if not global_settings.should_show_boundary_warnings():
                return True
            
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            
            # Get task timestamps
            c.execute("SELECT time_begin, time_end, date_audited FROM tasks WHERE id=?", (task_id,))
            result = c.fetchone()
            conn.close()
            
            if not result:
                return True
            
            time_begin_str, time_end_str, date_audited = result
            
            # Parse available timestamps
            time_begin = None
            time_end = None
            fallback_time = None
            
            if time_begin_str and time_begin_str.strip():
                try:
                    time_begin = datetime.strptime(time_begin_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    pass
            
            if time_end_str and time_end_str.strip():
                try:
                    time_end = datetime.strptime(time_end_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    pass
            
            if date_audited and date_audited.strip():
                try:
                    # Assume middle of day for date-only timestamps
                    fallback_time = datetime.strptime(date_audited, '%Y-%m-%d').replace(hour=12)
                except ValueError:
                    pass
            
            # Determine validation strategy
            timestamps_to_validate = []
            
            if time_begin and time_end:
                # Both timestamps exist - both must be within boundaries
                timestamps_to_validate = [time_begin, time_end]
                validation_mode = "both"
            elif time_begin:
                # Only time_begin exists
                timestamps_to_validate = [time_begin]
                validation_mode = "begin_only"
            elif time_end:
                # Only time_end exists
                timestamps_to_validate = [time_end]
                validation_mode = "end_only"
            elif fallback_time:
                # Only date_audited exists (fallback)
                timestamps_to_validate = [fallback_time]
                validation_mode = "date_fallback"
            else:
                # No valid timestamps
                return True
            
            # Validate each timestamp
            outside_boundary_times = []
            for timestamp in timestamps_to_validate:
                if self.is_task_outside_week_boundaries(week_id, timestamp):
                    outside_boundary_times.append(timestamp)
            
            # Report boundary violations
            if outside_boundary_times:
                if validation_mode == "both":
                    if len(outside_boundary_times) == 2:
                        warning_msg = f"Task start ({time_begin.strftime('%Y-%m-%d %H:%M')}) and end ({time_end.strftime('%Y-%m-%d %H:%M')}) both fall outside week boundaries."
                    elif time_begin in outside_boundary_times:
                        warning_msg = f"Task start time ({time_begin.strftime('%Y-%m-%d %H:%M')}) falls outside week boundaries."
                    else:
                        warning_msg = f"Task end time ({time_end.strftime('%Y-%m-%d %H:%M')}) falls outside week boundaries."
                else:
                    # Single timestamp validation
                    timestamp = outside_boundary_times[0]
                    warning_msg = f"Task timestamp ({timestamp.strftime('%Y-%m-%d %H:%M')}) falls outside week boundaries."
                
                if hasattr(self.main_window, 'toaster_manager'):
                    self.main_window.toaster_manager.show_warning(
                        "Boundary Validation Warning",
                        warning_msg,
                        5000
                    )
                return False
            
            return True
            
        except Exception as e:
            print(f"Error validating task boundaries: {e}")
            return True


class TaskGridItemDelegate(QtWidgets.QStyledItemDelegate):
    """Custom delegate to draw highlighted borders around empty cells"""
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def paint(self, painter, option, index):
        # Get highlighting information from the model
        highlight_data = index.model().data(index, QtCore.Qt.UserRole)
        needs_highlight = highlight_data and highlight_data.get('needs_highlight', False) if highlight_data else False
        
        # Check if it needs highlighting
        if needs_highlight:
            # Save painter state
            painter.save()
            
            # Fill the background (respects selection state)
            if option.state & QtWidgets.QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())
            else:
                painter.fillRect(option.rect, option.palette.base())
            
            # Draw the red border with glow effect
            pen = QtGui.QPen(QtGui.QColor(255, 100, 100, 180))
            pen.setWidth(2)
            painter.setPen(pen)
            
            # Draw inner rectangle (accounting for pen width)
            rect = option.rect.adjusted(2, 2, -2, -2)
            painter.drawRect(rect)
            
            # For a subtle glow effect, draw additional rectangles with decreasing opacity
            for i in range(1, 3):
                glow_rect = option.rect.adjusted(i, i, -i, -i)
                glow_pen = QtGui.QPen(QtGui.QColor(255, 100, 100, 80 - (i * 20)))
                glow_pen.setWidth(1)
                painter.setPen(glow_pen)
                painter.drawRect(glow_rect)
            
            # Draw the text
            painter.setPen(QtGui.QPen(option.palette.text().color()))
            text = index.model().data(index, QtCore.Qt.DisplayRole) or ""
            painter.drawText(option.rect.adjusted(4, 4, -4, -4), 
                            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, 
                            text)
            
            # Restore painter
            painter.restore()
        else:
            # Use default painting for normal cells
            super().paint(painter, option, index)


class FeedbackDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, feedback="", task_id=None):
        super().__init__(parent)
        self.task_id = task_id
        
        self.setWindowTitle("Edit Feedback")
        self.resize(600, 400)
        
        # Apply dark theme styling (now handled globally by main.py ThemeManager)
        layout = QtWidgets.QVBoxLayout(self)
        
        # Text editor
        self.editor = QtWidgets.QPlainTextEdit()
        self.editor.setPlainText(feedback)
        layout.addWidget(self.editor)
        
        # Buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.save_feedback)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def save_feedback(self):
        feedback = self.editor.toPlainText()
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("UPDATE tasks SET feedback=? WHERE id=?", (feedback, self.task_id))
        conn.commit()
        conn.close()
        
        self.accept() 