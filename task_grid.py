import sqlite3
from PySide6 import QtCore, QtWidgets, QtGui
from datetime import datetime

DB_FILE = "tasks.db"

class TaskGrid(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_week_id = None
        self.main_window = parent  # Store direct reference to main window
        
        # Setup table structure
        columns = [
            "Attempt ID", "Duration", "Project ID", "Project Name", 
            "Operation ID", "Time Limit", "Date Audited", "Score", 
            "Feedback", "Locale", "Actions"
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
        self.setColumnWidth(0, 100)  # Attempt ID
        self.setColumnWidth(1, 80)   # Duration
        self.setColumnWidth(2, 80)   # Project ID
        self.setColumnWidth(3, 120)  # Project Name
        self.setColumnWidth(4, 100)  # Operation ID
        self.setColumnWidth(5, 80)   # Time Limit
        self.setColumnWidth(6, 100)  # Date Audited
        self.setColumnWidth(7, 60)   # Score
        self.setColumnWidth(8, 200)  # Feedback
        self.setColumnWidth(9, 80)   # Locale
        
        # Connect signals
        self.cellChanged.connect(self.handle_cell_changed)
        
        # Flag to prevent recursive cell change handling
        self.is_loading = False
    
    def handle_cell_double_clicked(self, row, col):
        # Skip if we don't have task data
        if not hasattr(self, 'tasks') or row >= len(self.tasks):
            return
            
        task_id = self.tasks[row][0]
        
        # Handle feedback cell (col 8) - open dialog instead of inline edit
        if col == 8:
            self.edit_feedback(task_id)
            return
        
        # For last column (actions), don't make it editable
        if col == self.columnCount() - 1:
            return
    
    def handle_cell_changed(self, row, col):
        # Skip if we're just loading data or it's the actions column
        if self.is_loading or not hasattr(self, 'tasks') or row >= len(self.tasks) or col >= self.columnCount() - 1:
            return
            
        task_id = self.tasks[row][0]
        cell_value = self.item(row, col).text()
        
        # Determine which field to update based on column
        field_names = [
            "attempt_id", "duration", "project_id", "project_name",
            "operation_id", "time_limit", "date_audited", "score",
            "feedback", "locale"
        ]
        
        if col < len(field_names):
            field_name = field_names[col]
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
    
    def refresh_tasks(self, week_id):
        self.is_loading = True  # Set loading flag to prevent unwanted signal handling
        self.current_week_id = week_id
        self.setRowCount(0)
        
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
            
            # Populate cells
            for col_idx, value in enumerate(task[1:]):  # Skip the ID
                item = QtWidgets.QTableWidgetItem(str(value) if value is not None else "")
                
                # Special styling for feedback cells to indicate they're clickable
                if col_idx == 8:  # Feedback column
                    item.setToolTip("Double-click to edit feedback")
                    item.setBackground(QtGui.QColor(240, 240, 255))  # Light blue background
                    # Limit display text length
                    if value and len(value) > 30:
                        item.setText(f"{value[:30]}...")
                    # Make feedback non-editable directly in the grid
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                
                # Special handling for Score column
                if col_idx == 7:  # Score column (was 6 before, now 7 because feedback is 8)
                    validator = QtGui.QIntValidator(1, 5)
                    item.setData(QtCore.Qt.UserRole, validator)
                
                self.setItem(row_idx, col_idx, item)
            
            # Add action buttons in the last column
            actions_widget = QtWidgets.QWidget()
            actions_layout = QtWidgets.QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            delete_btn = QtWidgets.QPushButton("Delete")
            actions_layout.addWidget(delete_btn)
            
            # Connect buttons
            delete_btn.clicked.connect(lambda _, tid=task_id: self.delete_task(tid))
            
            self.setCellWidget(row_idx, len(task)-1, actions_widget)
            
            # Set row height
            self.setRowHeight(row_idx, 30)
        
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
            for row_idx in range(self.rowCount()):
                if row_idx < len(self.tasks) and self.tasks[row_idx][0] == task_id:
                    item = self.item(row_idx, 8)  # Feedback column
                    if item:
                        new_text = dialog.editor.toPlainText()
                        if len(new_text) > 30:
                            item.setText(f"{new_text[:30]}...")
                        else:
                            item.setText(new_text)
                        break
    
    def delete_task(self, task_id):
        reply = QtWidgets.QMessageBox.question(
            self, 'Confirm Deletion',
            "Are you sure you want to delete this task?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
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