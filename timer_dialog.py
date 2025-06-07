import sqlite3
from PySide6 import QtCore, QtWidgets, QtGui
from datetime import datetime

DB_FILE = "tasks.db"

class TimerDialog(QtWidgets.QDialog):
    """
    Timer dialog for tracking task durations.
    Features start, pause, and reset buttons with toaster confirmation for reset.
    """
    
    def __init__(self, parent=None, task_id=None, week_task_number=None):
        super().__init__(parent)
        self.task_id = task_id
        self.parent_grid = parent
        self.main_window = parent.main_window if hasattr(parent, 'main_window') else None
        self.week_task_number = week_task_number
        
        # Timer state
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.setInterval(1000)  # Update every second
        
        self.total_seconds = 0
        self.is_running = False
        self.is_first_start_for_task = True
        self.start_timestamp_for_new_task = None
        self.initial_duration_seconds = 0  # Store initial duration to check if changed
        
        if self.week_task_number is not None:
            self.setWindowTitle(f"Timer - Task #{self.week_task_number}")
        else:
            self.setWindowTitle(f"Timer - Task {task_id}") # Fallback to original if not found
        self.setWindowFlags(QtCore.Qt.Window)  # Make it undocked
        self.resize(300, 200)
        
        self.setup_ui()
        self.load_initial_duration()
        
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # Timer display
        self.time_display = QtWidgets.QLabel("00:00:00")
        self.time_display.setAlignment(QtCore.Qt.AlignCenter)
        self.time_display.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                background-color: #2a2a2a;
                color: #ffffff;
                border: 2px solid #444444;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        self.time_display.mousePressEvent = self.edit_time
        layout.addWidget(self.time_display)
        
        # Buttons
        buttons_layout = QtWidgets.QHBoxLayout()
        
        self.start_button = QtWidgets.QPushButton("Start")
        self.start_button.clicked.connect(self.start_timer)
        
        self.pause_button = QtWidgets.QPushButton("Pause")
        self.pause_button.clicked.connect(self.pause_timer)
        self.pause_button.setEnabled(False)
        
        self.reset_button = QtWidgets.QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_timer)
        
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.pause_button)
        buttons_layout.addWidget(self.reset_button)
        
        layout.addLayout(buttons_layout)
        
        # Instructions
        instructions = QtWidgets.QLabel("Click on the time to edit it directly")
        instructions.setAlignment(QtCore.Qt.AlignCenter)
        instructions.setStyleSheet("color: #666666; font-size: 12px;")
        layout.addWidget(instructions)
        
    def load_initial_duration(self):
        """Load the current duration from the database"""
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT duration, time_begin FROM tasks WHERE id=?", (self.task_id,))
        result = c.fetchone()
        conn.close()
        
        if result:
            duration_str = result[0] or "00:00:00"
            time_begin = result[1]
            
            # Parse duration
            try:
                h, m, s = map(int, duration_str.split(':'))
                self.total_seconds = h * 3600 + m * 60 + s
                self.initial_duration_seconds = self.total_seconds
            except (ValueError, AttributeError):
                self.total_seconds = 0
                self.initial_duration_seconds = 0
            
            # Check if this is the first start for this task
            if time_begin and time_begin.strip():
                self.is_first_start_for_task = False
                
            self.update_display()
    
    def update_display(self):
        """Update the timer display"""
        hours = int(self.total_seconds // 3600)
        minutes = int((self.total_seconds % 3600) // 60)
        seconds = int(self.total_seconds % 60)
        self.time_display.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        
        if self.is_running:
            self.total_seconds += 1
    
    def start_timer(self):
        """Start the timer"""
        if not self.is_running:
            # Record start timestamp if this is the first start for this task
            if self.is_first_start_for_task:
                self.start_timestamp_for_new_task = datetime.now()
            
            self.is_running = True
            self.timer.start()
            self.start_button.setEnabled(False)
            self.pause_button.setEnabled(True)
    
    def pause_timer(self):
        """Pause the timer"""
        if self.is_running:
            self.is_running = False
            self.timer.stop()
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
    
    def reset_timer(self):
        """Reset the timer with confirmation"""
        if self.main_window and hasattr(self.main_window, 'toaster_manager'):
            self.main_window.toaster_manager.show_question(
                "Are you sure you want to reset the timer to 00:00:00?",
                "Reset Timer",
                self.confirm_reset_timer
            )
        else:
            # Fallback to traditional dialog if toaster not available
            reply = QtWidgets.QMessageBox.question(
                self, 'Reset Timer',
                "Are you sure you want to reset the timer to 00:00:00?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No
            )
            
            if reply == QtWidgets.QMessageBox.Yes:
                self.do_reset_timer()
    
    def confirm_reset_timer(self, result):
        """Callback for toaster confirmation"""
        if result:
            self.do_reset_timer()
    
    def do_reset_timer(self):
        """Perform the actual timer reset"""
        self.pause_timer()
        self.total_seconds = 0
        self.update_display()
    
    def edit_time(self, event):
        """Allow direct editing of the time display"""
        current_time = self.time_display.text()
        
        time_input, ok = QtWidgets.QInputDialog.getText(
            self, 'Edit Time', 'Enter time (HH:MM:SS):', text=current_time
        )
        
        if ok and time_input:
            try:
                h, m, s = map(int, time_input.split(':'))
                if 0 <= h < 100 and 0 <= m < 60 and 0 <= s < 60:
                    self.total_seconds = h * 3600 + m * 60 + s
                    self.update_display()
                else:
                    QtWidgets.QMessageBox.warning(
                        self, "Invalid Time", 
                        "Please enter a valid time in HH:MM:SS format."
                    )
            except ValueError:
                QtWidgets.QMessageBox.warning(
                    self, "Invalid Time", 
                    "Please enter a valid time in HH:MM:SS format."
                )
    
    def has_duration_changed(self):
        """Check if the current duration is different from the initial one"""
        return self.total_seconds != self.initial_duration_seconds
    
    def closeEvent(self, event):
        """Handle dialog close - update the database and parent grid"""
        # Stop the timer if running
        if self.is_running:
            self.pause_timer()
        
        # Update the parent grid with the new values
        if self.parent_grid and hasattr(self.parent_grid, 'update_task_time_and_duration_from_timer'):
            self.parent_grid.update_task_time_and_duration_from_timer(
                task_id=self.task_id,
                new_duration_seconds=self.total_seconds,
                is_first_start_for_task=self.is_first_start_for_task and self.start_timestamp_for_new_task is not None,
                has_duration_changed=self.has_duration_changed(),
                start_timestamp_for_new_task=self.start_timestamp_for_new_task
            )
        
        super().closeEvent(event) 