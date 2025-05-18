import sqlite3
from PySide6 import QtCore, QtWidgets, QtGui
from datetime import datetime

DB_FILE = "tasks.db"

class TaskGrid(QtWidgets.QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_week_id = None
        
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
        
        # Allow editing cells directly
        self.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked)
        
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
    
    def handle_cell_changed(self, row, col):
        # Skip if we're just loading data
        if not hasattr(self, 'tasks') or row >= len(self.tasks):
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
        
        # Emit signal to notify analysis widget to refresh
        self.parent().refresh_analysis()
    
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
        self.current_week_id = week_id
        self.setRowCount(0)
        
        if week_id is None:
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
                
                # Special handling for some columns
                if col_idx == 6:  # Score column
                    validator = QtGui.QIntValidator(1, 5)
                    item.setData(QtCore.Qt.UserRole, validator)
                
                self.setItem(row_idx, col_idx, item)
            
            # Add action buttons in the last column
            actions_widget = QtWidgets.QWidget()
            actions_layout = QtWidgets.QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            edit_feedback_btn = QtWidgets.QPushButton("Edit")
            delete_btn = QtWidgets.QPushButton("Delete")
            
            actions_layout.addWidget(edit_feedback_btn)
            actions_layout.addWidget(delete_btn)
            
            # Connect buttons
            edit_feedback_btn.clicked.connect(lambda _, tid=task_id: self.edit_feedback(tid))
            delete_btn.clicked.connect(lambda _, tid=task_id: self.delete_task(tid))
            
            self.setCellWidget(row_idx, len(task)-1, actions_widget)
            
            # Set row height
            self.setRowHeight(row_idx, 30)
    
    def edit_feedback(self, task_id):
        # Get current feedback text
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT feedback FROM tasks WHERE id=?", (task_id,))
        feedback = c.fetchone()[0] or ""
        conn.close()
        
        # Show dialog with markdown editor
        dialog = FeedbackDialog(self, feedback, task_id)
        dialog.exec()
    
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
            self.parent().refresh_analysis()
    
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