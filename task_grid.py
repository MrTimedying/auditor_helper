import sqlite3
from PySide6 import QtCore, QtWidgets, QtGui
from datetime import datetime

DB_FILE = "tasks.db"

class TaskGridItem(QtWidgets.QTableWidgetItem):
    """Custom table widget item that supports empty cell highlighting"""
    def __init__(self, text="", is_empty=False, init_value=False):
        super().__init__(text)
        self.is_empty = is_empty
        self.is_init_value = init_value
        self.needs_highlight = is_empty or init_value
        
        # Set placeholder style for empty cells
        if self.needs_highlight:
            self._apply_empty_style()
    
    def _apply_empty_style(self):
        """Apply style for empty or init value cells"""
        # The actual style will be set in the TaskGrid paint event
        # This method exists for future extensibility
        pass

class TaskGrid(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_week_id = None
        self.main_window = parent  # Store direct reference to main window
        self.selected_tasks = set()  # Store selected task IDs
        
        # Setup table structure
        columns = [
            "", "Attempt ID", "Duration", "Project ID", "Project Name", 
            "Operation ID", "Time Limit", "Date Audited", "Score", 
            "Feedback", "Locale"
        ]
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        
        # Allow editing by double click, but handle feedback cells specially
        self.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked | 
                             QtWidgets.QAbstractItemView.EditKeyPressed)
        self.cellDoubleClicked.connect(self.handle_cell_double_clicked)
        
        # Set column widths
        self.setColumnWidth(0, 30)   # Checkbox column
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
        
        # Connect signals
        self.cellChanged.connect(self.handle_cell_changed)
        self.cellClicked.connect(self.handle_cell_clicked)
        
        # Flag to prevent recursive cell change handling
        self.is_loading = False
        
        # Custom item delegate for cell highlighting
        self.setItemDelegate(TaskGridItemDelegate(self))
    
    def handle_cell_double_clicked(self, row, col):
        # Skip if we don't have task data
        if not hasattr(self, 'tasks') or row >= len(self.tasks):
            return
            
        task_id = self.tasks[row][0]
        
        # Skip checkbox column
        if col == 0:
            return
            
        # Handle feedback cell (col 9) - open dialog instead of inline edit
        if col == 9:
            self.edit_feedback(task_id)
            return
    
    def handle_cell_clicked(self, row, col):
        # Handle checkbox column clicks
        if col == 0 and hasattr(self, 'tasks') and row < len(self.tasks):
            task_id = self.tasks[row][0]
            checkbox_item = self.item(row, 0)
            
            if checkbox_item.checkState() == QtCore.Qt.Checked:
                self.selected_tasks.add(task_id)
            else:
                self.selected_tasks.discard(task_id)
                
            # Update delete button text
            if hasattr(self.main_window, 'update_delete_button'):
                self.main_window.update_delete_button()
    
    def handle_cell_changed(self, row, col):
        # Skip if we're just loading data or it's the checkbox column
        if self.is_loading or not hasattr(self, 'tasks') or row >= len(self.tasks) or col == 0:
            return
            
        task_id = self.tasks[row][0]
        cell_item = self.item(row, col)
        cell_value = cell_item.text()
        
        # Determine which field to update based on column
        field_names = [
            None,  # Skip checkbox column
            "attempt_id", "duration", "project_id", "project_name",
            "operation_id", "time_limit", "date_audited", "score",
            "feedback", "locale"
        ]
        
        if col < len(field_names) and field_names[col]:
            field_name = field_names[col]
            
            # Update cell highlighting state
            if isinstance(cell_item, TaskGridItem):
                # Check if the cell is now filled and was previously empty
                if cell_item.needs_highlight and cell_value.strip():
                    cell_item.needs_highlight = False
                    cell_item.is_empty = False
                    cell_item.is_init_value = False
                # Check if the cell is now empty
                elif not cell_value.strip():
                    cell_item.needs_highlight = True
                    cell_item.is_empty = True
                    cell_item.is_init_value = False
            
            # Update the database
            self.update_task_field(task_id, field_name, cell_value)
    
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
        
        # Use direct reference to main window instead of parent()
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
        self.is_loading = True  # Set loading flag to prevent unwanted signal handling
        self.current_week_id = week_id
        self.setRowCount(0)
        self.selected_tasks.clear()  # Clear selected tasks
        
        if week_id is None:
            self.is_loading = False
            return
            
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(
            """SELECT id, attempt_id, duration, project_id, project_name,
               operation_id, time_limit, date_audited, score, feedback, locale
               FROM tasks WHERE week_id=? ORDER BY id""", 
            (week_id,)
        )
        self.tasks = c.fetchall()
        conn.close()
        
        for row_idx, task in enumerate(self.tasks):
            task_id = task[0]
            self.insertRow(row_idx)
            
            # Add checkbox in the first column
            checkbox_item = QtWidgets.QTableWidgetItem()
            checkbox_item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            checkbox_item.setCheckState(QtCore.Qt.Unchecked)
            self.setItem(row_idx, 0, checkbox_item)
            
            # Populate cells
            for col_idx, value in enumerate(task[1:]):  # Skip the ID
                # Process value
                display_value = str(value) if value is not None else ""
                
                # Check if this is an empty value or initialization value
                is_empty = self.is_empty_value(display_value)
                is_init = self.is_init_value(col_idx, display_value)
                
                # Create the custom item
                item = TaskGridItem(display_value, is_empty=is_empty, init_value=is_init)
                
                # Special styling for feedback cells to indicate they're clickable
                if col_idx == 8:  # Feedback column (9 in the grid with checkbox)
                    item.setToolTip(str(value) if value is not None else "") # Use full text for tooltip
                    # Make feedback non-editable directly in the grid
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                
                # Special handling for Score column
                if col_idx == 7:  # Score column (8 in the grid with checkbox)
                    validator = QtGui.QIntValidator(1, 5)
                    item.setData(QtCore.Qt.UserRole, validator)
                
                # Add item to the grid (add 1 to col_idx to account for checkbox column)
                self.setItem(row_idx, col_idx + 1, item)
            
            # Set row height
            self.setRowHeight(row_idx, 30)
        
        # Update delete button text
        if hasattr(self.main_window, 'update_delete_button'):
            self.main_window.update_delete_button()
            
        self.is_loading = False  # Reset loading flag
    
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
            # After saving, refresh the displayed text in the table
            # The database is updated in the FeedbackDialog save_feedback method
            
            # Find the row for the updated task
            for row_idx in range(self.rowCount()):
                if row_idx < len(self.tasks) and self.tasks[row_idx][0] == task_id:
                    item = self.item(row_idx, 9)  # Feedback column (was 8, now 9 with checkbox)
                    if item:
                        new_text = dialog.editor.toPlainText()
                        item.setText(new_text) # Set the full text
                        item.setToolTip(new_text) # Update the tooltip as well
                        
                        # Update highlighting state if needed
                        if isinstance(item, TaskGridItem):
                            item.is_empty = not new_text.strip()
                            item.needs_highlight = item.is_empty
                    break
    
    def delete_selected_tasks(self):
        if not self.selected_tasks:
            return
            
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        for task_id in self.selected_tasks:
            c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            
        conn.commit()
        conn.close()
        
        # Refresh the grid and analysis
        self.refresh_tasks(self.current_week_id)
        
        # Use direct reference to main window
        try:
            if hasattr(self.main_window, 'refresh_analysis'):
                self.main_window.refresh_analysis()
        except Exception as e:
            print(f"Error updating analysis after deletion: {e}")
    
    def delete_task(self, task_id):
        # Legacy method kept for compatibility
        self.selected_tasks = {task_id}
        self.delete_selected_tasks()
    
    def add_task(self, week_id):
        if week_id is None:
            return
            
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # Default values for a new task
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute(
            """INSERT INTO tasks (
                week_id, attempt_id, duration, project_id, project_name,
                operation_id, time_limit, date_audited, score, feedback, locale
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (week_id, "", "00:00:00", "", "", "", "00:00:00", today, 0, "", "")
        )
        conn.commit()
        conn.close()
        
        # Refresh the grid
        self.refresh_tasks(week_id)


class TaskGridItemDelegate(QtWidgets.QStyledItemDelegate):
    """Custom delegate to draw highlighted borders around empty cells"""
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def paint(self, painter, option, index):
        # Extract the item from the model
        model = index.model()
        item = model.itemFromIndex(index) if hasattr(model, 'itemFromIndex') else None
        
        # Check if it's our custom item and needs highlighting
        if isinstance(item, TaskGridItem) and item.needs_highlight:
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
            text = item.text()
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