import sqlite3
from PySide6 import QtCore, QtWidgets, QtGui

DB_FILE = "tasks.db"

class AnalysisWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Data Analysis")
        
        # Allow this widget to be undocked/floated
        self.setWindowFlags(QtCore.Qt.Window)
        
        # Layout
        layout = QtWidgets.QVBoxLayout(self)
        
        # Statistics display
        self.total_time_label = QtWidgets.QLabel("Total Time: 00:00:00")
        self.avg_time_label = QtWidgets.QLabel("Average Time: 00:00:00")
        self.time_limit_usage_label = QtWidgets.QLabel("Time Limit Usage: 0.0%")
        self.fail_rate_label = QtWidgets.QLabel("Fail Rate: 0.0%")
        
        # Add labels to layout
        layout.addWidget(QtWidgets.QLabel("<b>Weekly Statistics</b>"))
        layout.addWidget(self.total_time_label)
        layout.addWidget(self.avg_time_label)
        layout.addWidget(self.time_limit_usage_label)
        layout.addWidget(self.fail_rate_label)
        layout.addStretch()

    def refresh_analysis(self, week_id):
        if week_id is None:
            self.clear_statistics()
            return
            
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # Fetch all tasks for the week
        c.execute("""
            SELECT duration, time_limit, score
            FROM tasks
            WHERE week_id=?
        """, (week_id,))
        
        tasks = c.fetchall()
        conn.close()
        
        if not tasks:
            self.clear_statistics()
            return
            
        # Calculate statistics
        # Parse durations and time limits
        total_seconds = 0
        total_limit_seconds = 0
        low_scores = 0  # Tasks with score 1 or 2
        
        for duration_str, time_limit_str, score in tasks:
            # Parse duration (hh:mm:ss)
            try:
                hours, minutes, seconds = map(int, duration_str.split(':'))
                task_seconds = hours * 3600 + minutes * 60 + seconds
                total_seconds += task_seconds
                
                # Parse time limit
                hours, minutes, seconds = map(int, time_limit_str.split(':'))
                limit_seconds = hours * 3600 + minutes * 60 + seconds
                total_limit_seconds += limit_seconds
                
                # Count failing scores (1 or 2)
                if score in (1, 2):
                    low_scores += 1
            except (ValueError, AttributeError):
                # Skip invalid entries
                pass
        
        # Calculate statistics
        num_tasks = len(tasks)
        avg_seconds = total_seconds / num_tasks if num_tasks > 0 else 0
        time_limit_usage = (total_seconds / total_limit_seconds * 100) if total_limit_seconds > 0 else 0
        fail_rate = (low_scores / num_tasks * 100) if num_tasks > 0 else 0
        
        # Format time as hh:mm:ss
        def format_time(seconds):
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        
        # Update labels
        self.total_time_label.setText(f"Total Time: {format_time(total_seconds)}")
        self.avg_time_label.setText(f"Average Time: {format_time(int(avg_seconds))}")
        self.time_limit_usage_label.setText(f"Time Limit Usage: {time_limit_usage:.1f}%")
        self.fail_rate_label.setText(f"Fail Rate: {fail_rate:.1f}%")
    
    def clear_statistics(self):
        self.total_time_label.setText("Total Time: 00:00:00")
        self.avg_time_label.setText("Average Time: 00:00:00")
        self.time_limit_usage_label.setText("Time Limit Usage: 0.0%")
        self.fail_rate_label.setText("Fail Rate: 0.0%") 